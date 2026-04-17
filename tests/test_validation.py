from pathlib import Path
import pandas as pd

from src.migrate_validate import check_before_migration


def test_check_before_migration_detects_valid_csv(tmp_path):
    csv_path = tmp_path / "mini.csv"

    df = pd.DataFrame(
        [
            {
                "Name": "Alice Doe",
                "Age": 35,
                "Gender": "Female",
                "Blood Type": "A+",
                "Medical Condition": "Diabetes",
                "Date of Admission": "2024-01-10",
                "Doctor": "Dr. Martin",
                "Hospital": "City Hospital",
                "Insurance Provider": "Aetna",
                "Billing Amount": 1200.50,
                "Room Number": 101,
                "Admission Type": "Emergency",
                "Discharge Date": "2024-01-12",
                "Medication": "Metformin",
                "Test Results": "Normal",
            }
        ]
    )
    df.to_csv(csv_path, index=False)

    result_df, report = check_before_migration(csv_path)

    assert len(result_df) == 1
    assert report["column_count_raw"] == 15
    assert report["columns_missing"] == []
    assert report["status"] == "OK"