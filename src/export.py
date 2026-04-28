"""
Pipeline d'export : MongoDB → fichiers (JSONL + CSV).

Ce module est le pendant de migrate.py côté lecture. Il extrait la collection
patients sous deux formats :
  - JSON Lines (.jsonl) : un document par ligne, types préservés via extended JSON.
                          Format de référence pour l'écosystème MongoDB.
  - CSV (.csv)          : format universel, lisible par Excel / Pandas.
                          Les types datetime sont sérialisés en ISO 8601.

Usage :
    uv run python -m src.export

Pré-requis :
    - Migration effectuée (collection patients peuplée)
    - Dossier exports/ accessible en écriture
"""

import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from bson import json_util
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from src import config


# ─── Constantes locales ─────────────────────────────────────────────
EXPORTS_DIR = config.PROJECT_ROOT / "exports"
JSONL_FILENAME = "patients_export.jsonl"
CSV_FILENAME = "patients_export.csv"

# Ordre des colonnes pour le CSV (l'ordre dans lequel on veut les voir)
CSV_FIELD_ORDER = list(config.RENAME_MAP.values())


# ─── Logging ────────────────────────────────────────────────────────
def setup_logging() -> logging.Logger:
    """Configure un logger console + fichier (réutilise la même conf que migrate)."""
    config.LOGS_DIR.mkdir(exist_ok=True)
    log_file = config.LOGS_DIR / f"export_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger("export")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.info("Log écrit dans : %s", log_file)
    return logger


# ─── Export JSON Lines ──────────────────────────────────────────────
def export_jsonl(collection, output_path: Path, logger: logging.Logger) -> int:
    """
    Exporte chaque document sur une ligne (format JSONL).

    Utilise bson.json_util pour la sérialisation en extended JSON
    (préserve ObjectId, datetime, etc. de manière réversible).
    """
    logger.info("Export JSONL → %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with output_path.open("w", encoding="utf-8") as f:
        # Streaming : on n'utilise pas .find().to_list() pour ne pas charger
        # toute la collection en mémoire. Pertinent pour de gros volumes.
        for doc in collection.find():
            f.write(json_util.dumps(doc) + "\n")
            written += 1

    size_mb = output_path.stat().st_size / 1_000_000
    logger.info("JSONL : %d documents écrits (%.2f MB)", written, size_mb)
    return written


# ─── Export CSV ─────────────────────────────────────────────────────
def export_csv(collection, output_path: Path, logger: logging.Logger) -> int:
    """
    Exporte la collection en CSV.

    Les datetime sont sérialisés en ISO 8601 (YYYY-MM-DDTHH:MM:SS).
    Le champ _id (ObjectId) est exclu : il n'a pas de sens hors MongoDB.
    """
    logger.info("Export CSV → %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELD_ORDER)
        writer.writeheader()

        for doc in collection.find():
            row = {}
            for field in CSV_FIELD_ORDER:
                value = doc.get(field)
                if isinstance(value, datetime):
                    row[field] = value.isoformat()
                else:
                    row[field] = value
            writer.writerow(row)
            written += 1

    size_mb = output_path.stat().st_size / 1_000_000
    logger.info("CSV : %d documents écrits (%.2f MB)", written, size_mb)
    return written


# ─── Orchestration ──────────────────────────────────────────────────
def main() -> int:
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("DÉBUT DE L'EXPORT")
    logger.info("=" * 60)

    started_at = datetime.now()
    client = None
    try:
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        logger.info("Connexion MongoDB OK : %s", config.MONGO_URI)

        collection = client[config.MONGO_DB_NAME][config.MONGO_COLLECTION_NAME]
        total = collection.count_documents({})
        if total == 0:
            logger.error("Collection vide : rien à exporter")
            return 1
        logger.info("Documents à exporter : %d", total)

        n_jsonl = export_jsonl(collection, EXPORTS_DIR / JSONL_FILENAME, logger)
        n_csv = export_csv(collection, EXPORTS_DIR / CSV_FILENAME, logger)

        # Cohérence : les deux exports doivent contenir le même nombre de lignes
        if n_jsonl != n_csv or n_jsonl != total:
            raise AssertionError(
                f"Incohérence : collection={total}, jsonl={n_jsonl}, csv={n_csv}"
            )

        elapsed = (datetime.now() - started_at).total_seconds()
        logger.info("=" * 60)
        logger.info("EXPORT TERMINÉ EN %.1f s", elapsed)
        logger.info("=" * 60)
        return 0

    except AssertionError as e:
        logger.error("Erreur de cohérence : %s", e)
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
