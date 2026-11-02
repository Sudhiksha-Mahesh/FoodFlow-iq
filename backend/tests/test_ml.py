import pandas as pd
from app.utils.schema_detection import detect_roles
from app.etl.transform import apply_transformations
from app.ml.forecasting import run_forecast
from app.ml.churn import build_customer_features, train_churn_models


def _daily_df(n_days=40):
    dates = pd.date_range("2026-01-01", periods=n_days).repeat(3)
    return pd.DataFrame({
        "order_id": [f"O{i}" for i in range(len(dates))],
        "order_date": dates.astype(str),
        "customer_id": [f"C{i % 10}" for i in range(len(dates))],
        "subtotal": [100 + (i % 7) * 15 for i in range(len(dates))],
    })


def test_forecast_insufficient_history_reports_reason():
    df = _daily_df(n_days=5)
    roles = detect_roles(df)
    df2 = apply_transformations(df, roles)
    result = run_forecast(df2, roles, horizon=7)
    assert result["available"] is False
    assert "days" in result["reason"]


def test_forecast_runs_with_enough_history():
    df = _daily_df(n_days=40)
    roles = detect_roles(df)
    df2 = apply_transformations(df, roles)
    result = run_forecast(df2, roles, horizon=7)
    assert result["available"] is True
    assert len(result["forecast"]["orders"]) == 7
    assert result["best_model"] in ("moving_average", "exponential_smoothing", "arima")


def test_churn_flags_insufficient_customers():
    df = _daily_df(n_days=10)
    roles = detect_roles(df)
    df2 = apply_transformations(df, roles)
    features = build_customer_features(df2, roles, churn_threshold_days=5)
    result = train_churn_models(features)
    assert result["available"] is False
