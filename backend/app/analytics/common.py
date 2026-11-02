import pandas as pd
import numpy as np
from typing import Dict, Optional

FILTERABLE_ROLES = {
    "date": "order_date",  # handled specially (range)
    "city": "customer_city",
    "restaurant": "restaurant_name",
    "cuisine": "cuisine",
    "order_status": "order_status",
    "payment_method": "payment_method",
    "customer_type": "customer_type",
    "food_category": "food_category",
}


def available_filters(df: pd.DataFrame, role_map: Dict[str, str]) -> Dict[str, list]:
    """Build filter option lists dynamically -- only for columns that exist (Section 22)."""
    filters = {}
    if "order_date" in role_map and "_parsed_date" in df.columns:
        valid = df["_parsed_date"].dropna()
        if len(valid) > 0:
            filters["date_range"] = [valid.min().date().isoformat(), valid.max().date().isoformat()]
    for key, role in FILTERABLE_ROLES.items():
        if key == "date":
            continue
        if role in role_map and role_map[role] in df.columns:
            vals = df[role_map[role]].dropna().unique().tolist()
            vals = sorted([str(v) for v in vals])[:200]
            if len(vals) > 1:
                filters[key] = vals
    return filters


def apply_filters(df: pd.DataFrame, role_map: Dict[str, str], filters: Optional[Dict] = None) -> pd.DataFrame:
    if not filters:
        return df
    out = df

    if filters.get("date_from") and "_parsed_date" in out.columns:
        out = out[out["_parsed_date"] >= pd.to_datetime(filters["date_from"])]
    if filters.get("date_to") and "_parsed_date" in out.columns:
        out = out[out["_parsed_date"] <= pd.to_datetime(filters["date_to"])]

    for key, role in FILTERABLE_ROLES.items():
        if key == "date":
            continue
        val = filters.get(key)
        if val and role in role_map and role_map[role] in out.columns:
            if isinstance(val, list):
                out = out[out[role_map[role]].astype(str).isin(val)]
            else:
                out = out[out[role_map[role]].astype(str) == str(val)]
    return out


def safe_col(df: pd.DataFrame, role_map: Dict[str, str], role: str):
    col = role_map.get(role)
    if col and col in df.columns:
        return df[col]
    return None


def round_num(x, nd=2):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return 0
    return round(float(x), nd)
