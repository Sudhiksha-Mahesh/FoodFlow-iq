import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.db import get_session
from app.services import dataset_store
from app.schemas.requests import FilterParams, ForecastRequest, ChurnRequest, AprioriRequest
from app.analytics.common import apply_filters
from app.analytics.rfm import compute_rfm
from app.ml.forecasting import run_forecast
from app.ml.churn import build_customer_features, train_churn_models, risk_level
from app.ml.apriori import run_apriori
from app.analytics import sales as sales_mod
from app.analytics import customer as customer_mod
from app.analytics import restaurant as restaurant_mod
from app.analytics import delivery as delivery_mod
from app.analytics.delivery import time_analytics
from app.analytics.recommendations_engine import generate_recommendations

router = APIRouter(prefix="/api/datasets", tags=["ml"])


def _get_df_and_roles(dataset_id: str, db: Session):
    record = dataset_store.get_dataset(db, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found.")
    df = dataset_store.get_working_df(record)
    role_map = dataset_store.get_role_map(record)
    return df, role_map


def _clean_json(obj):
    """Recursively replace NaN/inf with None so FastAPI's JSON encoder doesn't choke."""
    if isinstance(obj, dict):
        return {k: _clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_json(v) for v in obj]
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj


@router.post("/{dataset_id}/rfm")
def rfm_endpoint(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    rfm = compute_rfm(filtered, role_map)
    if rfm is None:
        return {"available": False, "reason": "Customer identifier and/or order date columns unavailable."}
    out = rfm.copy()
    out["last_order"] = out["last_order"].dt.date.astype(str)
    return _clean_json({"available": True, "customers": out.to_dict(orient="records")})


@router.post("/{dataset_id}/forecast")
def forecast_endpoint(dataset_id: str, req: ForecastRequest, db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    result = run_forecast(df, role_map, group_by=req.group_by, group_value=req.group_value, horizon=req.horizon)
    return _clean_json(result)


@router.post("/{dataset_id}/churn")
def churn_endpoint(dataset_id: str, req: ChurnRequest, db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    features = build_customer_features(df, role_map, churn_threshold_days=req.churn_threshold_days)
    if features is None:
        return {"available": False, "reason": "Customer identifier and/or order date columns unavailable."}

    result = train_churn_models(features)
    if not result.get("available"):
        return result

    predictions = result["customer_predictions"]
    predictions["risk"] = predictions["churn_probability"].apply(lambda p: risk_level(p, req.low_max, req.medium_max))

    summary = {
        "high_risk": int((predictions["risk"] == "High").sum()),
        "medium_risk": int((predictions["risk"] == "Medium").sum()),
        "low_risk": int((predictions["risk"] == "Low").sum()),
        "avg_churn_probability": round(float(predictions["churn_probability"].mean()), 1),
    }

    monetary_median = predictions["monetary"].median() if "monetary" in predictions.columns else 0
    high_value_high_risk = predictions[(predictions["monetary"] >= monetary_median) & (predictions["risk"] == "High")]
    summary["high_value_high_risk_count"] = int(len(high_value_high_risk))

    table_cols = ["customer_id", "total_orders", "monetary", "recency", "churn_probability", "risk"]
    table_cols = [c for c in table_cols if c in predictions.columns]
    table = predictions[table_cols].rename(columns={
        "total_orders": "orders", "monetary": "total_spending", "recency": "days_since_last_order"
    }).sort_values("churn_probability", ascending=False)

    return _clean_json({
        "available": True,
        "model_comparison": result["model_comparison"],
        "best_model": result["best_model"],
        "feature_columns": result["feature_columns"],
        "summary": summary,
        "customers": table.to_dict(orient="records"),
    })


@router.post("/{dataset_id}/apriori")
def apriori_endpoint(dataset_id: str, req: AprioriRequest, db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    result = run_apriori(df, role_map, req.min_support, req.min_confidence, req.min_lift)
    return _clean_json(result)


@router.post("/{dataset_id}/recommendations")
def recommendations_endpoint(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())

    s = sales_mod.sales_analytics(filtered, role_map)
    c = customer_mod.customer_analytics(filtered, role_map)
    r = restaurant_mod.restaurant_analytics(filtered, role_map)
    d = delivery_mod.delivery_analytics(filtered, role_map)
    t = time_analytics(filtered, role_map)

    churn_summary = None
    features = build_customer_features(filtered, role_map, churn_threshold_days=60)
    if features is not None and len(features) >= 30:
        churn_result = train_churn_models(features)
        if churn_result.get("available"):
            preds = churn_result["customer_predictions"]
            preds["risk"] = preds["churn_probability"].apply(lambda p: risk_level(p))
            monetary_median = preds["monetary"].median() if "monetary" in preds.columns else 0
            churn_summary = {
                "high_value_high_risk_count": int(((preds["monetary"] >= monetary_median) & (preds["risk"] == "High")).sum())
            }

    recs = generate_recommendations(s, c, r, d, t, churn_summary=churn_summary)
    return _clean_json({"recommendations": recs})
