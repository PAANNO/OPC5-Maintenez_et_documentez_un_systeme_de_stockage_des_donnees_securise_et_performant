"""
Pipeline de migration : CSV healthcare → MongoDB.

Étapes :
  1. Extraction (lecture CSV)
  2. Validation amont (colonnes attendues, lignes non vides)
  3. Transformation (renommage, normalisation casse, parsing dates, dédoublonnage)
  4. Chargement (insertion par batchs)
  5. Indexation
  6. Validation aval (recompte, présence des index)

Usage :
    python -m src.migrate

Pré-requis :
    - MongoDB joignable sur l'URI configurée (cf. src/config.py)
    - CSV présent dans data/healthcare_dataset.csv
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from pymongo import ASCENDING, DESCENDING, IndexModel, MongoClient
from pymongo.errors import BulkWriteError, PyMongoError

from src import config


# ─── Logging ────────────────────────────────────────────────────────
def setup_logging() -> logging.Logger:
    """Configure un logger qui écrit à la fois console + fichier horodaté."""
    config.LOGS_DIR.mkdir(exist_ok=True)
    log_file = config.LOGS_DIR / f"migration_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger("migration")
    logger.setLevel(logging.INFO)
    # Évite la duplication si la fonction est appelée plusieurs fois
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # Fichier
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.info("Log écrit dans : %s", log_file)
    return logger


# ─── 1. Extraction ──────────────────────────────────────────────────
def extract(csv_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Lit le CSV source et retourne un DataFrame brut."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV introuvable : {csv_path}")

    logger.info("Lecture du CSV : %s", csv_path)
    df = pd.read_csv(csv_path)
    logger.info("CSV lu : %d lignes × %d colonnes", df.shape[0], df.shape[1])
    return df


# ─── 2. Validation amont ────────────────────────────────────────────
def validate_input(df: pd.DataFrame, logger: logging.Logger) -> None:
    """Vérifie la structure du CSV avant transformation."""
    logger.info("Validation amont du CSV…")

    missing = set(config.EXPECTED_CSV_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le CSV : {missing}")

    extra = set(df.columns) - set(config.EXPECTED_CSV_COLUMNS)
    if extra:
        logger.warning("Colonnes inattendues (ignorées) : %s", extra)

    total_nulls = df.isna().sum().sum()
    logger.info("Valeurs manquantes (toutes colonnes) : %d", total_nulls)

    logger.info("Validation amont OK")


# ─── 3. Transformation ──────────────────────────────────────────────
def transform(df: pd.DataFrame, logger: logging.Logger) -> list[dict]:
    """
    Applique toutes les transformations actées dans DECISIONS.md :
      - renommage snake_case
      - normalisation Title Case sur name/doctor
      - parsing dates (format ISO)
      - suppression doublons stricts
    Retourne une liste de documents prête pour insert_many.
    """
    logger.info("Transformation en cours…")
    df = df.rename(columns=config.RENAME_MAP)

    # Title Case sur les noms (gère la casse aléatoire du dataset Kaggle)
    for field in config.NAME_FIELDS:
        df[field] = df[field].str.strip().str.title()

    # Parsing explicite des dates (format spécifié → rapide + pas de warning)
    for field in config.DATE_FIELDS:
        df[field] = pd.to_datetime(df[field], format=config.DATE_FORMAT)

    # Doublons stricts
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    logger.info("Doublons stricts supprimés : %d (%d → %d)", removed, before, len(df))

    documents = df.to_dict(orient="records")
    logger.info("Transformation terminée : %d documents prêts", len(documents))
    return documents


# ─── 4. Chargement ──────────────────────────────────────────────────
def load(documents: list[dict], collection, logger: logging.Logger) -> int:
    """
    Insère les documents par batchs.
    Vide la collection avant pour garantir l'idempotence (on peut relancer
    le script sans accumuler de doublons).
    Retourne le nombre de documents insérés.
    """
    logger.info("Vidage de la collection %s avant insertion…", collection.name)
    collection.delete_many({})

    total = len(documents)
    inserted = 0

    for start in range(0, total, config.BATCH_SIZE):
        batch = documents[start : start + config.BATCH_SIZE]
        try:
            result = collection.insert_many(batch, ordered=False)
            inserted += len(result.inserted_ids)
            logger.info(
                "Batch inséré : %d/%d (%.1f%%)",
                inserted,
                total,
                100 * inserted / total,
            )
        except BulkWriteError as e:
            # ordered=False : on continue malgré les erreurs d'insertion ponctuelles
            logger.error("Erreur d'insertion sur un batch : %s", e.details)
            raise

    logger.info("Insertion terminée : %d documents", inserted)
    return inserted


# ─── 5. Indexation ──────────────────────────────────────────────────
def create_indexes(collection, logger: logging.Logger) -> list[str]:
    """
    Crée les index actés dans DECISIONS.md.
    Stratégie : 3 index simples + 1 composé pour analyses démographiques.
    """
    logger.info("Création des index…")

    indexes = [
        IndexModel(
            [("medical_condition", ASCENDING)],
            name="idx_medical_condition",
        ),
        IndexModel(
            [("date_of_admission", DESCENDING)],
            name="idx_date_of_admission_desc",
        ),
        IndexModel(
            [("hospital", ASCENDING)],
            name="idx_hospital",
        ),
        IndexModel(
            [("age", ASCENDING), ("gender", ASCENDING)],
            name="idx_age_gender",
        ),
    ]
    created = collection.create_indexes(indexes)
    logger.info("Index créés : %s", created)
    return created


# ─── 6. Validation aval ─────────────────────────────────────────────
def validate_output(
    collection,
    expected_count: int,
    expected_indexes: list[str],
    logger: logging.Logger,
) -> None:
    """Vérifie que la migration s'est bien passée côté MongoDB."""
    logger.info("Validation aval…")

    actual_count = collection.count_documents({})
    if actual_count != expected_count:
        raise AssertionError(
            f"Nombre de documents incorrect : attendu {expected_count}, "
            f"trouvé {actual_count}"
        )
    logger.info("Comptage OK : %d documents", actual_count)

    existing_indexes = set(collection.index_information().keys())
    missing = set(expected_indexes) - existing_indexes
    if missing:
        raise AssertionError(f"Index manquants : {missing}")
    logger.info("Index présents : %s", sorted(existing_indexes))

    logger.info("Validation aval OK")


# ─── Orchestration ──────────────────────────────────────────────────
def main() -> int:
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("DÉBUT DE LA MIGRATION")
    logger.info("=" * 60)

    started_at = datetime.now()
    client = None
    try:
        # Connexion (timeout court pour échouer vite si Mongo absent)
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        logger.info("Connexion MongoDB OK : %s", config.MONGO_URI)

        db = client[config.MONGO_DB_NAME]
        collection = db[config.MONGO_COLLECTION_NAME]

        df = extract(config.CSV_PATH, logger)
        validate_input(df, logger)
        documents = transform(df, logger)
        inserted = load(documents, collection, logger)
        created_indexes = create_indexes(collection, logger)
        validate_output(collection, inserted, created_indexes, logger)

        elapsed = (datetime.now() - started_at).total_seconds()
        logger.info("=" * 60)
        logger.info("MIGRATION TERMINÉE EN %.1f s", elapsed)
        logger.info("=" * 60)
        return 0

    except (FileNotFoundError, ValueError, AssertionError) as e:
        logger.error("Erreur fonctionnelle : %s", e)
        return 1
    except PyMongoError as e:
        logger.error("Erreur MongoDB : %s", e)
        return 2
    except Exception as e:
        logger.exception("Erreur inattendue : %s", e)
        return 3
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    sys.exit(main())
