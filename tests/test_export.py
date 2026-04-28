"""
Tests d'intégrité des fichiers exportés.

Pré-requis : avoir lancé `uv run python -m src.export` avant.
"""

import csv
import json
from pathlib import Path

import pytest

from src import config


EXPORTS_DIR = config.PROJECT_ROOT / "exports"
JSONL_PATH = EXPORTS_DIR / "patients_export.jsonl"
CSV_PATH = EXPORTS_DIR / "patients_export.csv"


@pytest.fixture(scope="module")
def jsonl_file():
    if not JSONL_PATH.exists():
        pytest.skip(f"Export JSONL absent ({JSONL_PATH}) — lancez src.export")
    return JSONL_PATH


@pytest.fixture(scope="module")
def csv_file():
    if not CSV_PATH.exists():
        pytest.skip(f"Export CSV absent ({CSV_PATH}) — lancez src.export")
    return CSV_PATH


class TestExportJsonl:
    def test_file_not_empty(self, jsonl_file: Path):
        assert jsonl_file.stat().st_size > 0

    def test_count_matches_collection(self, jsonl_file: Path, mongo_collection):
        """Une ligne du JSONL = un document de la collection."""
        with jsonl_file.open(encoding="utf-8") as f:
            n_lines = sum(1 for _ in f)
        assert n_lines == mongo_collection.count_documents({})

    def test_each_line_is_valid_json(self, jsonl_file: Path):
        """Chaque ligne doit être un JSON valide."""
        with jsonl_file.open(encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Ligne {i} invalide : {e}")

    def test_first_doc_has_expected_fields(self, jsonl_file: Path):
        with jsonl_file.open(encoding="utf-8") as f:
            doc = json.loads(f.readline())
        expected = set(config.RENAME_MAP.values())
        assert expected.issubset(set(doc.keys()))


class TestExportCsv:
    def test_file_not_empty(self, csv_file: Path):
        assert csv_file.stat().st_size > 0

    def test_count_matches_collection(self, csv_file: Path, mongo_collection):
        """Le CSV (hors header) doit avoir autant de lignes que la collection."""
        with csv_file.open(encoding="utf-8", newline="") as f:
            n_rows = sum(1 for _ in csv.DictReader(f))
        assert n_rows == mongo_collection.count_documents({})

    def test_csv_header_complete(self, csv_file: Path):
        """L'en-tête doit contenir tous les champs métier."""
        with csv_file.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
        for field in config.RENAME_MAP.values():
            assert field in header, f"Champ {field} absent du header CSV"

    def test_dates_in_iso_format(self, csv_file: Path):
        """Les dates doivent être en format ISO 8601."""
        with csv_file.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        # Format attendu : 2024-01-31T00:00:00 (au minimum les 10 premiers caractères)
        for field in config.DATE_FIELDS:
            value = row[field]
            assert (
                len(value) >= 10 and value[4] == "-" and value[7] == "-"
            ), f"{field}='{value}' n'est pas en format ISO"
