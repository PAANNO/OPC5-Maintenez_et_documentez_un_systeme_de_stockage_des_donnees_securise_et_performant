"""
Tests d'intégrité de la collection MongoDB (après migration).

Ces tests garantissent que la migration a produit le résultat attendu :
typage correct, index présents, normalisations appliquées.

Pré-requis : la migration doit avoir été lancée (uv run python -m src.migrate).
"""

from datetime import datetime

import pandas as pd
import pytest

from src import config


class TestMongoCollection:
    """Vérifications sur la collection elle-même."""

    def test_collection_not_empty(self, mongo_collection):
        """Collection peuplée."""
        assert mongo_collection.count_documents({}) > 0

    def test_count_matches_csv_minus_duplicates(
        self, mongo_collection, csv_dataframe: pd.DataFrame
    ):
        """Le nombre de documents = nb lignes CSV - doublons stricts."""
        expected = len(csv_dataframe) - csv_dataframe.duplicated().sum()
        actual = mongo_collection.count_documents({})
        assert (
            actual == expected
        ), f"Nombre incorrect : attendu {expected} (CSV - doublons), trouvé {actual}"


class TestMongoSchema:
    """Vérifications sur le typage et la structure des documents."""

    def test_all_expected_fields_present(self, mongo_collection):
        """Chaque document doit avoir tous les champs renommés en snake_case."""
        doc = mongo_collection.find_one()
        expected_fields = set(config.RENAME_MAP.values())
        actual_fields = set(doc.keys()) - {"_id"}
        missing = expected_fields - actual_fields
        assert not missing, f"Champs manquants : {missing}"

    def test_dates_are_datetime(self, mongo_collection):
        """Les champs date doivent être des datetime, pas des strings."""
        doc = mongo_collection.find_one()
        for field in config.DATE_FIELDS:
            assert isinstance(
                doc[field], datetime
            ), f"{field} devrait être datetime, trouvé {type(doc[field]).__name__}"

    def test_numeric_types(self, mongo_collection):
        """age et room_number en int, billing_amount en float."""
        doc = mongo_collection.find_one()
        assert isinstance(doc["age"], int)
        assert isinstance(doc["room_number"], int)
        assert isinstance(doc["billing_amount"], float)


class TestMongoIndexes:
    """Vérifications sur les index — point de vigilance explicite de la consigne."""

    def test_expected_indexes_present(self, mongo_collection):
        """Les 4 index métier + l'index _id par défaut doivent exister."""
        existing = set(mongo_collection.index_information().keys())
        expected = {
            "_id_",
            "idx_medical_condition",
            "idx_date_of_admission_desc",
            "idx_hospital",
            "idx_age_gender",
        }
        missing = expected - existing
        assert not missing, f"Index manquants : {missing}"

    def test_query_uses_index(self, mongo_collection):
        """Une requête sur medical_condition doit utiliser un IXSCAN."""
        explain = mongo_collection.find({"medical_condition": "Cancer"}).explain()
        winning = explain["queryPlanner"]["winningPlan"]
        # Le plan peut être imbriqué (FETCH > IXSCAN), on cherche IXSCAN partout
        assert "IXSCAN" in str(winning), f"La requête n'utilise pas d'index : {winning}"


class TestMongoBusinessRules:
    """Vérifications de règles métier après migration."""

    def test_no_strict_duplicates(self, mongo_collection):
        """Aucun doublon strict ne doit subsister."""
        # On groupe sur tous les champs sauf _id
        pipeline = [
            {
                "$group": {
                    "_id": {field: f"${field}" for field in config.RENAME_MAP.values()},
                    "count": {"$sum": 1},
                }
            },
            {"$match": {"count": {"$gt": 1}}},
            {"$count": "duplicate_groups"},
        ]
        result = list(mongo_collection.aggregate(pipeline))
        n_duplicates = result[0]["duplicate_groups"] if result else 0
        assert n_duplicates == 0, f"{n_duplicates} groupes de doublons trouvés"

    def test_names_are_title_case(self, mongo_collection):
        """Les champs name et doctor doivent être en Title Case."""
        for field in config.NAME_FIELDS:
            doc = mongo_collection.find_one({field: {"$exists": True}})
            value = doc[field]
            assert (
                value == value.title()
            ), f"{field}='{value}' n'est pas en Title Case (attendu : '{value.title()}')"

    def test_age_realistic(self, mongo_collection):
        """Aucun âge aberrant en base."""
        anomalies = mongo_collection.count_documents(
            {"$or": [{"age": {"$lt": 0}}, {"age": {"$gt": 120}}]}
        )
        assert anomalies == 0, f"{anomalies} âges aberrants détectés"
