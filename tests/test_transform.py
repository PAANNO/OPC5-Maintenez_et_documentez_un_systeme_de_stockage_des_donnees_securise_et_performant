from numbers import Integral

from src.migrate_validate import transform_dataframe


def test_transform_dataframe_renames_columns(sample_df):
    transformed_df, report = transform_dataframe(sample_df)

    assert "name" in transformed_df.columns
    assert "medical_condition" in transformed_df.columns
    assert "Date of Admission" not in transformed_df.columns
    assert report["rows_before_transform"] == 2
    assert report["rows_after_transform"] == 2


def test_transform_dataframe_creates_stay_days_and_row_hash(sample_df):
    transformed_df, _ = transform_dataframe(sample_df)

    assert "stay_days" in transformed_df.columns
    assert "row_hash" in transformed_df.columns
    assert all(isinstance(v, Integral) for v in transformed_df["stay_days"])
    assert transformed_df["row_hash"].notna().all()