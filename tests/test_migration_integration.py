from src.migrate_validate import transform_dataframe
from pymongo import ASCENDING


def test_insert_transformed_documents_into_mongo(sample_df, mongo_collection):
    transformed_df, _ = transform_dataframe(sample_df)
    docs = transformed_df.to_dict(orient="records")

    mongo_collection.create_index([("row_hash", ASCENDING)], unique=True, name="ux_row_hash")
    result = mongo_collection.insert_many(docs, ordered=False)

    assert len(result.inserted_ids) == 2
    assert mongo_collection.count_documents({}) == 2


def test_indexes_exist(sample_df, mongo_collection):
    transformed_df, _ = transform_dataframe(sample_df)
    docs = transformed_df.to_dict(orient="records")

    mongo_collection.create_index([("row_hash", 1)], unique=True, name="ux_row_hash")
    mongo_collection.create_index([("medical_condition", 1)], name="idx_medical_condition")
    mongo_collection.insert_many(docs, ordered=False)

    indexes = mongo_collection.index_information()
    assert "ux_row_hash" in indexes
    assert "idx_medical_condition" in indexes