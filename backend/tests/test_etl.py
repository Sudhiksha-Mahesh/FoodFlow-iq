from app.etl.profiling import profile_dataset
from app.etl.cleaning import clean_dataset
from app.etl.transform import apply_transformations
from app.utils.schema_detection import detect_roles, module_availability, compatibility_report


def test_profile_detects_missing_and_duplicates(messy_df):
    profile = profile_dataset(messy_df)
    assert profile["rows"] == 5
    assert profile["duplicate_rows"] == 1
    assert profile["missing_values"] >= 1


def test_clean_removes_duplicates_and_invalid_numeric(messy_df):
    result = clean_dataset(messy_df, {"missing_strategy": "auto", "remove_duplicates": True, "handle_invalid_numeric": True})
    cleaned = result["dataframe"]
    assert result["before"]["duplicates"] == 1
    assert cleaned.duplicated().sum() == 0
    # negative subtotal (-50) should have been nulled out then filled, not left negative
    assert (cleaned["subtotal"] < 0).sum() == 0


def test_schema_detection_finds_core_roles(sample_df):
    roles = detect_roles(sample_df)
    assert roles["order_id"] == "order_id"
    assert roles["customer_id"] == "customer_id"
    assert roles["order_date"] == "order_date"
    assert roles["subtotal"] == "subtotal"


def test_module_availability_flags_missing_columns(sample_df):
    roles = detect_roles(sample_df)
    avail = module_availability(roles)
    assert avail["Sales Analytics"]["status"] == "available"
    assert avail["Location Analytics"]["status"] == "unavailable"


def test_transform_generates_derived_fields(sample_df):
    roles = detect_roles(sample_df)
    out = apply_transformations(sample_df, roles)
    assert "total_amount" in out.columns
    assert "profit" in out.columns
    assert "order_month" in out.columns
    assert "delivery_delay" in out.columns
