"""
Configuration centralisée du pipeline de migration.

Ce module isole les paramètres pour qu'ils soient :
- modifiables sans toucher à la logique métier
- surchargeables par variables d'environnement (utile pour Docker)
- testables (on pourra mocker les chemins en tests)
"""

import os
from pathlib import Path

# Charge le .env local si présent (utile pour pytest et exécution hors Docker)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ─── Chemins ────────────────────────────────────────────────────────
# Racine du projet (parent du dossier src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
CSV_FILENAME = "healthcare_dataset.csv"
CSV_PATH = DATA_DIR / CSV_FILENAME

# ─── MongoDB ────────────────────────────────────────────────────────
# URI surchargée par variable d'environnement quand on passera à Docker
# Par défaut : Mongo local sans auth (phase 1 — auth ajoutée en étape 2)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "healthcare_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "patients")

# ─── Migration ──────────────────────────────────────────────────────
# Taille des batchs d'insertion (compromis mémoire / nombre de round-trips)
BATCH_SIZE = 5_000

# ─── Schéma : mapping CSV → MongoDB ─────────────────────────────────
RENAME_MAP = {
    "Name": "name",
    "Age": "age",
    "Gender": "gender",
    "Blood Type": "blood_type",
    "Medical Condition": "medical_condition",
    "Date of Admission": "date_of_admission",
    "Doctor": "doctor",
    "Hospital": "hospital",
    "Insurance Provider": "insurance_provider",
    "Billing Amount": "billing_amount",
    "Room Number": "room_number",
    "Admission Type": "admission_type",
    "Discharge Date": "discharge_date",
    "Medication": "medication",
    "Test Results": "test_results",
}

# Colonnes attendues dans le CSV source (validation amont)
EXPECTED_CSV_COLUMNS = list(RENAME_MAP.keys())

# Colonnes nominatives à normaliser en Title Case
NAME_FIELDS = ["name", "doctor"]

# Colonnes date à parser
DATE_FIELDS = ["date_of_admission", "discharge_date"]
DATE_FORMAT = "%Y-%m-%d"
