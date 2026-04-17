from pymongo import MongoClient
from pprint import pprint

# 1) Connexion à MongoDB
uri = "mongodb://localhost:27017"
client = MongoClient(uri)

# 2) Sélection de la base et de la collection
db = client["healthcare_db"]
collection = db["admissions"]

# 3) Nettoyage optionnel des données de démonstration
collection.delete_many({"demo": True})

# =========================
# CREATE
# =========================
document = {
    "name": "Bobby JacksOn",
    "age": 30,
    "gender": "Male",
    "blood_type": "B-",
    "medical_condition": "Cancer",
    "date_of_admission": "2024-01-31",
    "doctor": "Matthew Smith",
    "hospital": "Sons and Miller",
    "insurance_provider": "Blue Cross",
    "billing_amount": 18856.28,
    "room_number": 328,
    "admission_type": "Urgent",
    "discharge_date": "2024-02-02",
    "medication": "Paracetamol",
    "test_results": "Normal",
    "demo": True
}

result_insert = collection.insert_one(document)
print("CREATE - inserted_id :", result_insert.inserted_id)

# =========================
# READ
# =========================
print("\nREAD - find_one() :")
doc = collection.find_one({"demo": True})
pprint(doc)

print("\nREAD - find() :")
for d in collection.find({"demo": True}, {"_id": 0, "name": 1, "medical_condition": 1, "hospital": 1}):
    pprint(d)

# =========================
# UPDATE
# =========================
result_update = collection.update_one(
    {"name": "Bobby JacksOn", "demo": True},
    {"$set": {"test_results": "Abnormal", "hospital": "Sons & Miller"}}
)

print("\nUPDATE - matched_count :", result_update.matched_count)
print("UPDATE - modified_count :", result_update.modified_count)

print("\nREAD après UPDATE :")
updated_doc = collection.find_one({"name": "Bobby JacksOn", "demo": True}, {"_id": 0})
pprint(updated_doc)

# =========================
# DELETE
# =========================
result_delete = collection.delete_one({"name": "Bobby JacksOn", "demo": True})
print("\nDELETE - deleted_count :", result_delete.deleted_count)

print("\nREAD après DELETE :")
remaining = collection.find_one({"name": "Bobby JacksOn", "demo": True})
print(remaining)

# 4) Fermeture de la connexion
client.close()