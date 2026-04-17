import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from numbers import Integral
from pymongo import MongoClient, ASCENDING
from pymongo.errors import BulkWriteError


# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = Path("data/raw/healthcare_dataset.csv")
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "healthcare_db"
COLLECTION_NAME = "admissions"

# Stratégie doublons :
# True  -> supprime les doublons exacts avant insertion
# False -> conserve les doublons du CSV
DROP_EXACT_DUPLICATES_BEFORE_IMPORT = True

# Si True, vide la collection avant migration
RESET_COLLECTION_BEFORE_IMPORT = True

EXPECTED_COLUMNS = [
    "Name",
    "Age",
    "Gender",
    "Blood Type",
    "Medical Condition",
    "Date of Admission",
    "Doctor",
    "Hospital",
    "Insurance Provider",
    "Billing Amount",
    "Room Number",
    "Admission Type",
    "Discharge Date",
    "Medication",
    "Test Results",
]

RENAMED_COLUMNS = {
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

ALLOWED_GENDER = {"Male", "Female"}
ALLOWED_ADMISSION_TYPE = {"Emergency", "Urgent", "Elective"}
ALLOWED_TEST_RESULTS = {"Normal", "Abnormal", "Inconclusive"}


# ============================================================
# OUTILS
# ============================================================

def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def stable_row_hash(row: pd.Series) -> str:
    """
    Génère un hash stable à partir des valeurs de la ligne.
    Sert à éviter les réimports dupliqués si on crée un index unique dessus.
    """
    raw = "||".join("" if pd.isna(v) else str(v) for v in row.tolist())
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def safe_int(value: Any) -> Any:
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_float(value: Any) -> Any:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def to_python_datetime(series: pd.Series) -> pd.Series:
    """
    Convertit une série en datetime pandas puis en datetime Python.
    Les datetime Python sont bien sérialisées par PyMongo dans MongoDB.
    """
    converted = pd.to_datetime(series, errors="coerce")
    return converted.dt.to_pydatetime()


def count_missing_fields_in_documents(documents: List[Dict[str, Any]], required_fields: List[str]) -> Dict[str, int]:
    counts = {field: 0 for field in required_fields}
    for doc in documents:
        for field in required_fields:
            if field not in doc or doc[field] is None:
                counts[field] += 1
    return counts


# ============================================================
# ÉTAPE 1 — CONTRÔLE AVANT MIGRATION
# ============================================================

def check_before_migration(csv_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    print_section("1) CONTRÔLE AVANT MIGRATION")

    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

    df = pd.read_csv(csv_path)

    report: Dict[str, Any] = {
        "csv_path": str(csv_path),
        "row_count_raw": int(len(df)),
        "column_count_raw": int(len(df.columns)),
        "columns_found": df.columns.tolist(),
        "columns_missing": [],
        "columns_unexpected": [],
        "dtype_raw": {k: str(v) for k, v in df.dtypes.to_dict().items()},
        "missing_values_per_column": {},
        "duplicate_rows_exact": 0,
        "date_parse_errors": {},
        "business_rules": {},
        "status": "OK",
    }

    # Vérification colonnes
    found = set(df.columns.tolist())
    expected = set(EXPECTED_COLUMNS)
    report["columns_missing"] = sorted(list(expected - found))
    report["columns_unexpected"] = sorted(list(found - expected))

    # Valeurs manquantes
    report["missing_values_per_column"] = {
        col: int(val) for col, val in df.isna().sum().to_dict().items()
    }

    # Doublons exacts
    report["duplicate_rows_exact"] = int(df.duplicated().sum())

    # Parsing des dates pour contrôle
    admission_dates = pd.to_datetime(df["Date of Admission"], errors="coerce")
    discharge_dates = pd.to_datetime(df["Discharge Date"], errors="coerce")

    report["date_parse_errors"] = {
        "date_of_admission_invalid": int(admission_dates.isna().sum()),
        "discharge_date_invalid": int(discharge_dates.isna().sum()),
    }

    # Contrôles métier
    invalid_age = int((pd.to_numeric(df["Age"], errors="coerce") <= 0).sum())
    invalid_billing = int((pd.to_numeric(df["Billing Amount"], errors="coerce") < 0).sum())
    invalid_room = int((pd.to_numeric(df["Room Number"], errors="coerce") <= 0).sum())
    invalid_stay_order = int((discharge_dates < admission_dates).sum())

    invalid_gender = int((~df["Gender"].isin(ALLOWED_GENDER)).sum())
    invalid_admission_type = int((~df["Admission Type"].isin(ALLOWED_ADMISSION_TYPE)).sum())
    invalid_test_results = int((~df["Test Results"].isin(ALLOWED_TEST_RESULTS)).sum())

    report["business_rules"] = {
        "invalid_age_leq_0": invalid_age,
        "invalid_billing_amount_lt_0": invalid_billing,
        "invalid_room_number_leq_0": invalid_room,
        "invalid_discharge_before_admission": invalid_stay_order,
        "invalid_gender_values": invalid_gender,
        "invalid_admission_type_values": invalid_admission_type,
        "invalid_test_results_values": invalid_test_results,
    }

    # Statut global
    has_blocking_issue = (
        len(report["columns_missing"]) > 0
        or report["date_parse_errors"]["date_of_admission_invalid"] > 0
        or report["date_parse_errors"]["discharge_date_invalid"] > 0
    )
    if has_blocking_issue:
        report["status"] = "BLOCKING_ISSUES"

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return df, report


# ============================================================
# ÉTAPE 2 — TRANSFORMATION
# ============================================================

def transform_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    print_section("2) TRANSFORMATION DES DONNÉES")

    working_df = df.copy()

    transform_report = {
        "rows_before_transform": int(len(working_df)),
        "duplicate_rows_removed": 0,
        "rows_after_transform": 0,
        "notes": [],
    }

    # Optionnel : suppression des doublons exacts
    if DROP_EXACT_DUPLICATES_BEFORE_IMPORT:
        before = len(working_df)
        working_df = working_df.drop_duplicates().copy()
        after = len(working_df)
        transform_report["duplicate_rows_removed"] = int(before - after)
        transform_report["notes"].append("Suppression des doublons exacts activée.")
    else:
        transform_report["notes"].append("Suppression des doublons exacts désactivée.")

    # Renommage des colonnes
    working_df = working_df.rename(columns=RENAMED_COLUMNS)

    # Conversions de types
    working_df["age"] = working_df["age"].apply(safe_int)
    working_df["billing_amount"] = working_df["billing_amount"].apply(safe_float)
    working_df["room_number"] = working_df["room_number"].apply(safe_int)

    working_df["date_of_admission"] = to_python_datetime(working_df["date_of_admission"])
    working_df["discharge_date"] = to_python_datetime(working_df["discharge_date"])

    # Durée de séjour
    working_df["stay_days"] = (
        pd.to_datetime(working_df["discharge_date"]) - pd.to_datetime(working_df["date_of_admission"])
    ).dt.days

    # Hash technique pour idempotence / anti-doublon technique
    working_df["row_hash"] = working_df.apply(stable_row_hash, axis=1)

    # Métadonnées source
    working_df["source_file"] = CSV_PATH.name

    transform_report["rows_after_transform"] = int(len(working_df))

    print(json.dumps(transform_report, indent=2, ensure_ascii=False))
    return working_df, transform_report


# ============================================================
# ÉTAPE 3 — MIGRATION VERS MONGODB
# ============================================================

def migrate_to_mongodb(df: pd.DataFrame) -> Dict[str, Any]:
    print_section("3) MIGRATION VERS MONGODB")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    migration_report: Dict[str, Any] = {
        "mongo_uri": MONGO_URI,
        "database": DB_NAME,
        "collection": COLLECTION_NAME,
        "collection_reset": RESET_COLLECTION_BEFORE_IMPORT,
        "documents_to_insert": int(len(df)),
        "inserted_documents": 0,
        "bulk_write_errors": [],
        "indexes_created": [],
        "status": "OK",
    }

    try:
        if RESET_COLLECTION_BEFORE_IMPORT:
            collection.drop()
            collection = db[COLLECTION_NAME]

        # Index utiles
        index_specs = [
            [("row_hash", ASCENDING)],
            [("medical_condition", ASCENDING)],
            [("date_of_admission", ASCENDING)],
            [("hospital", ASCENDING)],
            [("doctor", ASCENDING), ("hospital", ASCENDING)],
        ]

        # Index unique anti-doublon technique
        migration_report["indexes_created"].append(
            collection.create_index(index_specs[0], unique=True, name="ux_row_hash")
        )
        # Index métier
        migration_report["indexes_created"].append(
            collection.create_index(index_specs[1], name="idx_medical_condition")
        )
        migration_report["indexes_created"].append(
            collection.create_index(index_specs[2], name="idx_date_of_admission")
        )
        migration_report["indexes_created"].append(
            collection.create_index(index_specs[3], name="idx_hospital")
        )
        migration_report["indexes_created"].append(
            collection.create_index(index_specs[4], name="idx_doctor_hospital")
        )

        documents = df.to_dict(orient="records")

        if documents:
            result = collection.insert_many(documents, ordered=False)
            migration_report["inserted_documents"] = len(result.inserted_ids)

    except BulkWriteError as exc:
        details = exc.details or {}
        migration_report["status"] = "PARTIAL_OR_ERROR"
        migration_report["bulk_write_errors"] = details.get("writeErrors", [])
        migration_report["inserted_documents"] = details.get("nInserted", 0)

    finally:
        client.close()

    print(json.dumps(migration_report, indent=2, ensure_ascii=False))
    return migration_report


# ============================================================
# ÉTAPE 4 — CONTRÔLE APRÈS MIGRATION
# ============================================================

def check_after_migration(expected_rows: int) -> Dict[str, Any]:
    print_section("4) CONTRÔLE APRÈS MIGRATION")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    required_fields = [
        "name",
        "age",
        "gender",
        "blood_type",
        "medical_condition",
        "date_of_admission",
        "doctor",
        "hospital",
        "insurance_provider",
        "billing_amount",
        "room_number",
        "admission_type",
        "discharge_date",
        "medication",
        "test_results",
        "stay_days",
        "row_hash",
        "source_file",
    ]

    total_docs = collection.count_documents({})
    sample_docs = list(collection.find({}, {"_id": 0}).limit(200))
    existing_indexes = list(collection.index_information().keys())

    # Documents incomplets sur l'échantillon
    missing_fields_in_sample = count_missing_fields_in_documents(sample_docs, required_fields)

    # Vérification types sur échantillon
    type_checks = {
        "age_is_int_on_sample": 0,
        "billing_amount_is_number_on_sample": 0,
        "room_number_is_int_on_sample": 0,
        "stay_days_is_int_on_sample": 0,
        "date_of_admission_present_on_sample": 0,
        "discharge_date_present_on_sample": 0,
    }

    for doc in sample_docs:
        if isinstance(doc.get("age"), int):
            type_checks["age_is_int_on_sample"] += 1
        if isinstance(doc.get("billing_amount"), (int, float)):
            type_checks["billing_amount_is_number_on_sample"] += 1
        if isinstance(doc.get("room_number"), int):
            type_checks["room_number_is_int_on_sample"] += 1
        if isinstance(doc.get("stay_days"), Integral):
            type_checks["stay_days_is_int_on_sample"] += 1
        if doc.get("date_of_admission") is not None:
            type_checks["date_of_admission_present_on_sample"] += 1
        if doc.get("discharge_date") is not None:
            type_checks["discharge_date_present_on_sample"] += 1

    # Vérification simple des doublons techniques
    pipeline = [
        {"$group": {"_id": "$row_hash", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$count": "duplicate_hash_groups"},
    ]
    dup_result = list(collection.aggregate(pipeline))
    duplicate_hash_groups = dup_result[0]["duplicate_hash_groups"] if dup_result else 0

    report = {
        "expected_documents": int(expected_rows),
        "documents_in_mongodb": int(total_docs),
        "count_matches_expectation": total_docs == expected_rows,
        "sample_size_checked": int(len(sample_docs)),
        "missing_required_fields_in_sample": missing_fields_in_sample,
        "type_checks_on_sample": type_checks,
        "duplicate_hash_groups": int(duplicate_hash_groups),
        "indexes_found": existing_indexes,
        "status": "OK" if total_docs == expected_rows and duplicate_hash_groups == 0 else "CHECK_NEEDED",
    }

    client.close()

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print_section("LANCEMENT DU PIPELINE DE CONTRÔLE + MIGRATION")

    # 1. Contrôle avant migration
    raw_df, before_report = check_before_migration(CSV_PATH)

    if before_report["status"] == "BLOCKING_ISSUES":
        raise ValueError(
            "Le contrôle avant migration a détecté des problèmes bloquants. "
            "Corrige le dataset ou adapte les règles avant d'aller plus loin."
        )

    # 2. Transformation
    transformed_df, transform_report = transform_dataframe(raw_df)

    # 3. Migration
    migration_report = migrate_to_mongodb(transformed_df)

    # 4. Contrôle après migration
    after_report = check_after_migration(expected_rows=len(transformed_df))

    # 5. Rapport final consolidé
    final_report = {
        "before_migration": before_report,
        "transform": transform_report,
        "migration": migration_report,
        "after_migration": after_report,
    }

    print_section("5) RAPPORT FINAL CONSOLIDÉ")
    print(json.dumps(final_report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()