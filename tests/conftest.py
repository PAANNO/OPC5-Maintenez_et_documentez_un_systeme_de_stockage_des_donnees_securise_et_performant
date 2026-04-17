from pathlib import Path
import pandas as pd
import pytest
from pymongo import MongoClient

from src.migrate_validate import DB_NAME, COLLECTION_NAME


@pytest.fixture
def sample_df():
    return pd.DataFrame(
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
            },
            {
                "Name": "Bob Smith",
                "Age": 42,
                "Gender": "Male",
                "Blood Type": "O-",
                "Medical Condition": "Cancer",
                "Date of Admission": "2024-02-01",
                "Doctor": "Dr. House",
                "Hospital": "General Hospital",
                "Insurance Provider": "Blue Cross",
                "Billing Amount": 2500.00,
                "Room Number": 202,
                "Admission Type": "Urgent",
                "Discharge Date": "2024-02-05",
                "Medication": "Paracetamol",
                "Test Results": "Abnormal",
            },
        ]
    )


@pytest.fixture
def mongo_collection():
    client = MongoClient("mongodb://localhost:27017")
    db = client[DB_NAME]
    collection = db[f"{COLLECTION_NAME}_test"]

    collection.drop()
    yield collection
    collection.drop()
    client.close()