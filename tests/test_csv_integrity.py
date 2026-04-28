"""
Tests d'intégrité du CSV source (avant migration).

Ces tests garantissent que le fichier reçu du client respecte le contrat
attendu : présence des colonnes, types, pas de fichier vide.
Ils permettent de détecter une dégradation de la source en amont
(ex. : nouveau dataset livré avec une colonne en moins).
"""

import pandas as pd
import pytest

from src import config


class TestCsvStructure:
    """Vérifications sur la structure du fichier CSV source."""

    def test_csv_not_empty(self, csv_dataframe: pd.DataFrame):
        """Le CSV doit contenir au moins une ligne."""
        assert len(csv_dataframe) > 0, "Le CSV source est vide"

    def test_expected_columns_present(self, csv_dataframe: pd.DataFrame):
        """Toutes les colonnes attendues doivent être présentes."""
        missing = set(config.EXPECTED_CSV_COLUMNS) - set(csv_dataframe.columns)
        assert not missing, f"Colonnes manquantes : {missing}"

    def test_no_unexpected_columns(self, csv_dataframe: pd.DataFrame):
        """Pas de colonnes inattendues (signal d'évolution silencieuse de la source)."""
        extra = set(csv_dataframe.columns) - set(config.EXPECTED_CSV_COLUMNS)
        assert not extra, f"Colonnes inattendues : {extra}"


class TestCsvDataQuality:
    """Vérifications sur la qualité des données du CSV."""

    def test_no_missing_values(self, csv_dataframe: pd.DataFrame):
        """Le dataset Kaggle ne contient aucune valeur manquante."""
        nulls = csv_dataframe.isna().sum().sum()
        assert nulls == 0, f"Valeurs manquantes détectées : {nulls}"

    def test_age_range_realistic(self, csv_dataframe: pd.DataFrame):
        """L'âge doit être dans une plage humaine plausible."""
        assert csv_dataframe["Age"].min() >= 0
        assert csv_dataframe["Age"].max() <= 120

    def test_dates_parseable(self, csv_dataframe: pd.DataFrame):
        """Toutes les dates doivent être parseables au format ISO."""
        for col in ["Date of Admission", "Discharge Date"]:
            parsed = pd.to_datetime(
                csv_dataframe[col], format="%Y-%m-%d", errors="coerce"
            )
            n_failed = parsed.isna().sum()
            assert n_failed == 0, f"{n_failed} dates non parseables dans {col}"

    def test_discharge_after_admission(self, csv_dataframe: pd.DataFrame):
        """Cohérence métier : date de sortie >= date d'admission."""
        admission = pd.to_datetime(
            csv_dataframe["Date of Admission"], format="%Y-%m-%d"
        )
        discharge = pd.to_datetime(csv_dataframe["Discharge Date"], format="%Y-%m-%d")
        invalid = (discharge < admission).sum()
        assert invalid == 0, f"{invalid} cas où discharge_date < date_of_admission"
