from app.utils.schema_detection import detect_roles
from app.etl.transform import apply_transformations
from app.analytics.sales import sales_analytics
from app.analytics.rfm import compute_rfm
from app.analytics.restaurant import restaurant_analytics


def _prepared(sample_df):
    roles = detect_roles(sample_df)
    df = apply_transformations(sample_df, roles)
    return df, roles


def test_sales_analytics_computes_kpis(sample_df):
    df, roles = _prepared(sample_df)
    result = sales_analytics(df, roles)
    assert result["kpis"]["total_orders"] == 20
    assert result["kpis"]["total_revenue"] > 0
    assert result["revenue_by_cuisine"] is not None


def test_rfm_segments_customers(sample_df):
    df, roles = _prepared(sample_df)
    rfm = compute_rfm(df, roles)
    assert rfm is not None
    assert set(["recency", "frequency", "monetary", "segment"]).issubset(rfm.columns)
    assert rfm["customer_id"].nunique() == 5


def test_restaurant_analytics_ranks_restaurants(sample_df):
    df, roles = _prepared(sample_df)
    result = restaurant_analytics(df, roles)
    assert result["available"] is True
    assert len(result["restaurants"]) == 3
    assert "top_performing" in result
