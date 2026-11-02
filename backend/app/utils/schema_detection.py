"""
Dataset schema-detection layer.

The platform must NOT assume a fixed column set. This module inspects an
uploaded CSV's column names (and, as a fallback, value patterns/dtypes) and
maps them to canonical "roles" that the rest of the analytics/ML pipeline
understands. Any role that cannot be found is simply left absent -- the
analytics layer is responsible for gracefully degrading when a role is
missing (never fabricating data).
"""
import re
import pandas as pd
from typing import Dict, Optional, List

# canonical_role -> list of regex fragments (checked against normalized column name)
ROLE_PATTERNS: Dict[str, List[str]] = {
    "order_id": [r"^order[_ ]?id$", r"^order[_ ]?no$", r"^transaction[_ ]?id$", r"^id$"],
    "order_date": [r"^order[_ ]?date$", r"^date$", r"^created[_ ]?at$", r"^order[_ ]?datetime$"],
    "order_time": [r"^order[_ ]?time$", r"^time$"],
    "customer_id": [r"^customer[_ ]?id$", r"^cust[_ ]?id$", r"^user[_ ]?id$"],
    "customer_age": [r"^customer[_ ]?age$", r"^age$"],
    "customer_gender": [r"^customer[_ ]?gender$", r"^gender$", r"^sex$"],
    "customer_city": [r"^customer[_ ]?city$", r"^city$"],
    "customer_area": [r"^customer[_ ]?area$", r"^area$", r"^locality$", r"^neighbou?rhood$"],
    "customer_type": [r"^customer[_ ]?type$", r"^segment$"],
    "restaurant_id": [r"^restaurant[_ ]?id$", r"^store[_ ]?id$", r"^outlet[_ ]?id$", r"^vendor[_ ]?id$"],
    "restaurant_name": [r"^restaurant[_ ]?name$", r"^restaurant$", r"^store[_ ]?name$", r"^vendor$", r"^merchant$"],
    "cuisine": [r"^cuisine$", r"^category$", r"^food[_ ]?category$"],
    "food_category": [r"^food[_ ]?category$", r"^category$"],
    "food_item": [r"^food[_ ]?item$", r"^item[_ ]?name$", r"^product$", r"^item$", r"^dish$"],
    "quantity": [r"^quantity$", r"^qty$", r"^units?$"],
    "unit_price": [r"^unit[_ ]?price$", r"^price$"],
    "subtotal": [r"^subtotal$", r"^sub[_ ]?total$", r"^amount$", r"^total[_ ]?amount$", r"^order[_ ]?value$",
                 r"^revenue$", r"^sales$", r"^net[_ ]?amount$"],
    "discount": [r"^discount$", r"^promo(tion)?$"],
    "delivery_fee": [r"^delivery[_ ]?fee$", r"^shipping[_ ]?fee$", r"^delivery[_ ]?charge$"],
    "payment_method": [r"^payment[_ ]?method$", r"^payment[_ ]?type$", r"^payment[_ ]?mode$"],
    "order_status": [r"^order[_ ]?status$", r"^status$"],
    "delivery_partner_id": [r"^delivery[_ ]?partner[_ ]?id$", r"^rider[_ ]?id$", r"^driver[_ ]?id$"],
    "delivery_partner_experience": [r"^delivery[_ ]?partner[_ ]?experience$", r"^rider[_ ]?experience$"],
    "distance_km": [r"^distance(_km)?$", r"^distance[_ ]?in[_ ]?km$"],
    "estimated_delivery_time": [r"^estimated[_ ]?delivery[_ ]?time$", r"^eta$"],
    "actual_delivery_time": [r"^actual[_ ]?delivery[_ ]?time$", r"^delivery[_ ]?time$", r"^delivery[_ ]?duration$"],
    "customer_rating": [r"^customer[_ ]?rating$", r"^food[_ ]?rating$", r"^rating$"],
    "delivery_rating": [r"^delivery[_ ]?rating$", r"^rider[_ ]?rating$"],
    "latitude": [r"^lat(itude)?$", r"^customer[_ ]?lat(itude)?$"],
    "longitude": [r"^lon(g|gitude)?$", r"^lng$", r"^customer[_ ]?lon(gitude)?$"],
}

# Roles required (at minimum) for each analytics module to be marked "Available"
MODULE_REQUIREMENTS = {
    "Sales Analytics": {"required": ["order_date"], "amount_any": ["subtotal", "unit_price"]},
    "Customer Analytics": {"required": ["customer_id"], "amount_any": ["subtotal"]},
    "Restaurant Analytics": {"required": ["restaurant_id_or_name"], "amount_any": ["subtotal"]},
    "Delivery Analytics": {"required": ["actual_delivery_time"], "amount_any": []},
    "Demand Forecasting": {"required": ["order_date"], "amount_any": []},
    "Churn Prediction": {"required": ["customer_id", "order_date"], "amount_any": ["subtotal"]},
    "Location Analytics": {"required_any": [["latitude", "longitude"], ["customer_city"]], "amount_any": []},
    "Recommendation Engine": {"required": ["order_id", "food_item"], "amount_any": []},
}


def _normalize(col: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", col.strip().lower().replace(" ", "_").replace("-", "_"))


def detect_roles(df: pd.DataFrame) -> Dict[str, str]:
    """Return mapping of canonical_role -> actual column name found in df."""
    normalized = {c: _normalize(c) for c in df.columns}
    role_map: Dict[str, str] = {}

    for role, patterns in ROLE_PATTERNS.items():
        if role in role_map:
            continue
        for col, norm in normalized.items():
            if any(re.match(p, norm) for p in patterns):
                role_map[role] = col
                break

    # Fallback dtype-based detection for revenue/amount if still missing
    if "subtotal" not in role_map:
        for col in df.columns:
            if col in role_map.values():
                continue
            if pd.api.types.is_numeric_dtype(df[col]) and _normalize(col) not in (
                "quantity", "age", "distance_km", "rating"
            ):
                # heuristics: a numeric column with reasonably large magnitude & variance
                series = pd.to_numeric(df[col], errors="coerce")
                if series.dropna().mean() > 10:
                    role_map["subtotal"] = col
                    break

    # Fallback date detection: try parsing any object column as dates
    if "order_date" not in role_map:
        for col in df.columns:
            if col in role_map.values():
                continue
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().mean() > 0.7:
                    role_map["order_date"] = col
                    break
            except Exception:
                continue

    return role_map


def compatibility_report(role_map: Dict[str, str]) -> Dict[str, dict]:
    """Human-readable ✓ / ⚠ compatibility summary (Section 5)."""
    checks = {
        "Order identifier": "order_id" in role_map,
        "Date": "order_date" in role_map,
        "Customer identifier": "customer_id" in role_map,
        "Revenue / amount": "subtotal" in role_map,
        "Restaurant": ("restaurant_id" in role_map or "restaurant_name" in role_map),
        "Cuisine": "cuisine" in role_map,
        "Delivery time": "actual_delivery_time" in role_map,
        "Customer rating": "customer_rating" in role_map,
        "Location": ("latitude" in role_map and "longitude" in role_map) or "customer_city" in role_map,
        "Payment method": "payment_method" in role_map,
        "Order status": "order_status" in role_map,
        "Food item": "food_item" in role_map,
    }
    return {k: {"available": v} for k, v in checks.items()}


def module_availability(role_map: Dict[str, str], n_customers: Optional[int] = None) -> Dict[str, dict]:
    """Determine which analytics modules can run given detected roles (Section 5 / 31)."""
    has = lambda r: r in role_map
    result = {}

    result["Sales Analytics"] = _status(has("order_date") and (has("subtotal") or has("unit_price")))
    result["Customer Analytics"] = _status(has("customer_id") and has("subtotal"))
    result["Restaurant Analytics"] = _status((has("restaurant_id") or has("restaurant_name")) and has("subtotal"))

    delivery_ok = has("actual_delivery_time")
    delivery_partial = has("distance_km") or has("estimated_delivery_time")
    if delivery_ok:
        result["Delivery Analytics"] = _status(True)
    elif delivery_partial:
        result["Delivery Analytics"] = _status(True, partial=True, note="Only partial delivery fields detected")
    else:
        result["Delivery Analytics"] = _status(False, note="Delivery time columns missing")

    result["Demand Forecasting"] = _status(has("order_date"))

    if has("customer_id") and has("order_date"):
        if n_customers is not None and n_customers < 200:
            result["Churn Prediction"] = _status(
                True, partial=True, note=f"Only {n_customers} customers with sufficient history detected (200+ recommended)"
            )
        else:
            result["Churn Prediction"] = _status(True)
    else:
        result["Churn Prediction"] = _status(False, note="Customer identifier or date column missing")

    result["Location Analytics"] = _status(
        (has("latitude") and has("longitude")) or has("customer_city"),
        note=None if ((has("latitude") and has("longitude")) or has("customer_city")) else "Location columns missing"
    )

    result["Recommendation Engine"] = _status(
        has("order_id") and has("food_item"),
        note=None if (has("order_id") and has("food_item")) else "Insufficient product-level transaction data"
    )

    return result


def _status(available: bool, partial: bool = False, note: Optional[str] = None) -> dict:
    if available and not partial:
        return {"status": "available", "label": "Available", "note": note}
    if available and partial:
        return {"status": "partial", "label": "Partial", "note": note}
    return {"status": "unavailable", "label": "Unavailable", "note": note}
