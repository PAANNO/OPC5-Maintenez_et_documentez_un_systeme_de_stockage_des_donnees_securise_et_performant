"""
Fixtures pytest partagées par tous les tests.

Une fixture est un "ingrédient" injecté automatiquement dans les tests
qui en ont besoin. Ici on en définit trois :
  - csv_dataframe : le DataFrame brut lu depuis le CSV
  - mongo_client : un client MongoDB connecté
  - mongo_collection : la collection patients de la base healthcare_db

Le scope="session" signifie que la fixture est créée UNE SEULE FOIS
pour toute la session de tests. Évite de re-lire le CSV 20 fois.
"""

import pandas as pd
import pytest
from pymongo import MongoClient

from src import config


@pytest.fixture(scope="session")
def csv_dataframe() -> pd.DataFrame:
    """DataFrame brut lu depuis le CSV source (avant transformation)."""
    if not config.CSV_PATH.exists():
        pytest.skip(f"CSV introuvable : {config.CSV_PATH}")
    return pd.read_csv(config.CSV_PATH)


@pytest.fixture(scope="session")
def mongo_client() -> MongoClient:
    """Client MongoDB. Skippe les tests si Mongo est injoignable."""
    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=2000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        pytest.skip(f"MongoDB injoignable sur {config.MONGO_URI} : {exc}")
    yield client
    client.close()


@pytest.fixture(scope="session")
def mongo_collection(mongo_client):
    """Collection patients (post-migration)."""
    collection = mongo_client[config.MONGO_DB_NAME][config.MONGO_COLLECTION_NAME]
    if collection.count_documents({}) == 0:
        pytest.skip(
            f"Collection vide : lancez 'uv run python -m src.migrate' avant les tests"
        )
    return collection
