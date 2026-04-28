"""
Démonstration des opérations CRUD MongoDB sur la collection patients.

Ce module n'est PAS exécuté en production. C'est un script pédagogique
qui démontre les 4 opérations sur des données isolées (préfixées DEMO_)
pour ne pas polluer la collection migrée.

Usage :
    uv run python -m src.crud
"""

import logging
import sys
from datetime import datetime

from pymongo import MongoClient

from src import config


# ─── Logging minimal ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crud-demo")


# ─── Documents de démonstration ─────────────────────────────────────
DEMO_DOC_1 = {
    "name": "Demo Patient One",
    "age": 42,
    "gender": "Female",
    "blood_type": "O+",
    "medical_condition": "Hypertension",
    "date_of_admission": datetime(2025, 3, 15),
    "doctor": "Dr Demo",
    "hospital": "Demo Hospital",
    "insurance_provider": "Demo Insurance",
    "billing_amount": 1234.56,
    "room_number": 101,
    "admission_type": "Elective",
    "discharge_date": datetime(2025, 3, 20),
    "medication": "Demo Med",
    "test_results": "Normal",
}

DEMO_DOC_2 = {
    **DEMO_DOC_1,
    "name": "Demo Patient Two",
    "age": 55,
    "billing_amount": 9876.54,
}


def demo_create(collection) -> list:
    """CREATE : insert_one + insert_many."""
    logger.info("─" * 60)
    logger.info("CREATE")
    logger.info("─" * 60)

    # insert_one
    res1 = collection.insert_one(DEMO_DOC_1.copy())
    logger.info("insert_one : %s", res1.inserted_id)

    # insert_many
    res2 = collection.insert_many([DEMO_DOC_2.copy(), DEMO_DOC_2.copy()])
    logger.info(
        "insert_many : %d documents (%s)", len(res2.inserted_ids), res2.inserted_ids
    )

    return [res1.inserted_id, *res2.inserted_ids]


def demo_read(collection):
    """READ : find_one, find avec filtre, count, aggregate."""
    logger.info("─" * 60)
    logger.info("READ")
    logger.info("─" * 60)

    # find_one
    doc = collection.find_one({"name": "Demo Patient One"})
    logger.info("find_one : trouvé '%s', âge %s", doc["name"], doc["age"])

    # find avec filtre + projection
    cursor = collection.find(
        {"name": {"$regex": "^Demo"}},
        {"name": 1, "age": 1, "_id": 0},
    )
    matches = list(cursor)
    logger.info("find (regex Demo + projection) : %d documents", len(matches))
    for m in matches:
        logger.info("  → %s", m)

    # count
    n = collection.count_documents({"name": {"$regex": "^Demo"}})
    logger.info("count_documents (Demo*) : %d", n)

    # aggregate
    pipeline = [
        {"$match": {"name": {"$regex": "^Demo"}}},
        {"$group": {"_id": "$gender", "avg_billing": {"$avg": "$billing_amount"}}},
    ]
    logger.info("aggregate (avg billing par genre, démos) :")
    for row in collection.aggregate(pipeline):
        logger.info("  → %s", row)


def demo_update(collection):
    """UPDATE : update_one, update_many."""
    logger.info("─" * 60)
    logger.info("UPDATE")
    logger.info("─" * 60)

    # update_one : on corrige l'âge d'un patient
    res = collection.update_one(
        {"name": "Demo Patient One"},
        {"$set": {"age": 43}},
    )
    logger.info(
        "update_one : matched=%d, modified=%d", res.matched_count, res.modified_count
    )

    # update_many : on tag tous les démos
    res = collection.update_many(
        {"name": {"$regex": "^Demo"}},
        {"$set": {"is_demo": True}},
    )
    logger.info(
        "update_many : matched=%d, modified=%d", res.matched_count, res.modified_count
    )


def demo_delete(collection):
    """DELETE : delete_one, delete_many."""
    logger.info("─" * 60)
    logger.info("DELETE")
    logger.info("─" * 60)

    # delete_one
    res = collection.delete_one({"name": "Demo Patient One"})
    logger.info("delete_one : %d supprimé", res.deleted_count)

    # delete_many : nettoyage complet des démos restants
    res = collection.delete_many({"name": {"$regex": "^Demo"}})
    logger.info("delete_many : %d supprimés", res.deleted_count)

    # Vérification
    remaining = collection.count_documents({"name": {"$regex": "^Demo"}})
    logger.info("Démos restants : %d (doit être 0)", remaining)


def main() -> int:
    logger.info(
        "DÉMONSTRATION CRUD sur %s.%s",
        config.MONGO_DB_NAME,
        config.MONGO_COLLECTION_NAME,
    )

    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
        collection = client[config.MONGO_DB_NAME][config.MONGO_COLLECTION_NAME]

        # Nombre de documents avant : on doit retomber dessus à la fin
        baseline = collection.count_documents({})
        logger.info("Documents avant démo : %d", baseline)

        demo_create(collection)
        demo_read(collection)
        demo_update(collection)
        demo_delete(collection)

        # Vérification finale : on est revenu à l'état initial
        final = collection.count_documents({})
        logger.info("─" * 60)
        logger.info("Documents après démo : %d (baseline : %d)", final, baseline)
        if final != baseline:
            logger.error("Incohérence : la démo a laissé des résidus")
            return 1
        logger.info("Démo CRUD OK : la collection est revenue à son état initial")
        return 0

    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
