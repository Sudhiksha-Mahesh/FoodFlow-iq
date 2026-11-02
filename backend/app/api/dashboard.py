from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.db import get_session
from app.services import dataset_store
from app.schemas.requests import FilterParams
from app.analytics.common import apply_filters, available_filters
from app.analytics import sales as sales_mod
from app.analytics import customer as customer_mod
from app.analytics import restaurant as restaurant_mod
from app.analytics import delivery as delivery_mod
from app.analytics.recommendations_engine import generate_recommendations

router = APIRouter(prefix="/api/datasets", tags=["dashboard"])


def _get_df_and_roles(dataset_id: str, db: Session):
    record = dataset_store.get_dataset(db, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found.")
    df = dataset_store.get_working_df(record)
    role_map = dataset_store.get_role_map(record)
    return df, role_map


@router.get("/{dataset_id}/filters")
def get_filters(dataset_id: str, db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    return available_filters(df, role_map)


@router.post("/{dataset_id}/dashboard/overview")
def dashboard_overview(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    result = sales_mod.sales_analytics(filtered, role_map)
    return result


@router.post("/{dataset_id}/dashboard/sales")
def dashboard_sales(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    return sales_mod.sales_analytics(filtered, role_map)


@router.post("/{dataset_id}/dashboard/customers")
def dashboard_customers(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    return customer_mod.customer_analytics(filtered, role_map)


@router.post("/{dataset_id}/dashboard/restaurants")
def dashboard_restaurants(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    return restaurant_mod.restaurant_analytics(filtered, role_map)


@router.post("/{dataset_id}/dashboard/delivery")
def dashboard_delivery(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    return delivery_mod.delivery_analytics(filtered, role_map)


@router.post("/{dataset_id}/dashboard/time")
def dashboard_time(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    from app.analytics.delivery import time_analytics
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    return time_analytics(filtered, role_map)


@router.post("/{dataset_id}/dashboard/locations")
def dashboard_locations(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    from app.analytics.delivery import location_analytics
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    return location_analytics(filtered, role_map)


@router.post("/{dataset_id}/insights")
def get_insights(dataset_id: str, filters: FilterParams = FilterParams(), db: Session = Depends(get_session)):
    df, role_map = _get_df_and_roles(dataset_id, db)
    filtered = apply_filters(df, role_map, filters.dict())
    from app.analytics.delivery import time_analytics as time_mod
    s = sales_mod.sales_analytics(filtered, role_map)
    c = customer_mod.customer_analytics(filtered, role_map)
    r = restaurant_mod.restaurant_analytics(filtered, role_map)
    d = delivery_mod.delivery_analytics(filtered, role_map)
    t = time_mod(filtered, role_map)
    recs = generate_recommendations(s, c, r, d, t, churn_summary=None)
    return {"recommendations": recs}
