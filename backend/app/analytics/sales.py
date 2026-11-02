import pandas as pd
import numpy as np
from typing import Dict
from app.analytics.common import safe_col, round_num


def _revenue(df, role_map):
    col = safe_col(df, role_map, "subtotal")
    return pd.to_numeric(col, errors="coerce").fillna(0) if col is not None else pd.Series([0] * len(df))


def overview_kpis(df: pd.DataFrame, role_map: Dict[str, str]) -> Dict:
    revenue = _revenue(df, role_map)
    total_revenue = revenue.sum()
    total_orders = len(df)

    kpis = {
        "total_revenue": round_num(total_revenue),
        "total_orders": int(total_orders),
        "has_revenue": "subtotal" in role_map,
    }

    if "customer_id" in role_map:
        kpis["total_customers"] = int(df[role_map["customer_id"]].nunique())
    if "subtotal" in role_map and total_orders:
        kpis["avg_order_value"] = round_num(total_revenue / total_orders)
    if "profit" in df.columns:
        kpis["total_profit"] = round_num(df["profit"].sum())
    if "actual_delivery_time" in role_map:
        kpis["avg_delivery_time"] = round_num(pd.to_numeric(df[role_map["actual_delivery_time"]], errors="coerce").mean())
    if "order_status" in role_map:
        status = df[role_map["order_status"]].astype(str)
        cancelled = status.str.lower().isin(["cancelled", "canceled", "failed"]).sum()
        kpis["cancellation_rate"] = round_num(cancelled / len(status) * 100) if len(status) else 0
    if "customer_rating" in role_map:
        kpis["avg_rating"] = round_num(pd.to_numeric(df[role_map["customer_rating"]], errors="coerce").mean())

    return kpis


def revenue_trend_by_month(df, role_map):
    if "order_month" not in df.columns or "order_year" not in df.columns:
        return None
    revenue = _revenue(df, role_map)
    tmp = pd.DataFrame({"y": df["order_year"], "m": df["order_month"], "rev": revenue})
    grouped = tmp.groupby(["y", "m"]).agg(revenue=("rev", "sum"), orders=("rev", "count")).reset_index()
    grouped = grouped.sort_values(["y", "m"])
    labels = [f"{int(y)}-{int(m):02d}" for y, m in zip(grouped["y"], grouped["m"])]
    return {
        "labels": labels,
        "revenue": [round_num(v) for v in grouped["revenue"]],
        "orders": [int(v) for v in grouped["orders"]],
    }


def group_metric(df, role_map, group_role, top_n=None, sort_by="revenue"):
    if group_role not in role_map:
        return None
    revenue = _revenue(df, role_map)
    tmp = pd.DataFrame({"group": df[role_map[group_role]].astype(str), "revenue": revenue})
    if "quantity" in role_map:
        tmp["quantity"] = pd.to_numeric(df[role_map["quantity"]], errors="coerce").fillna(0)
    else:
        tmp["quantity"] = 1
    if "profit" in df.columns:
        tmp["profit"] = df["profit"].fillna(0)
    agg = {"revenue": "sum", "quantity": "sum"}
    if "profit" in tmp.columns:
        agg["profit"] = "sum"
    grouped = tmp.groupby("group").agg(agg)
    grouped["orders"] = tmp.groupby("group").size()
    grouped = grouped.reset_index().sort_values(sort_by, ascending=False)
    if top_n:
        grouped = grouped.head(top_n)
    return grouped.to_dict(orient="records")


def sales_analytics(df, role_map):
    result = {
        "kpis": overview_kpis(df, role_map),
        "revenue_by_month": revenue_trend_by_month(df, role_map),
        "revenue_by_cuisine": group_metric(df, role_map, "cuisine"),
        "revenue_by_restaurant": group_metric(df, role_map, "restaurant_name", top_n=15),
        "revenue_by_city": group_metric(df, role_map, "customer_city"),
        "revenue_by_food_category": group_metric(df, role_map, "food_category"),
        "orders_by_status": group_metric(df, role_map, "order_status"),
        "orders_by_payment_method": group_metric(df, role_map, "payment_method"),
    }
    if "food_item" in role_map:
        top_products = group_metric(df, role_map, "food_item", top_n=10, sort_by="revenue")
        result["top_products"] = top_products
    return result
