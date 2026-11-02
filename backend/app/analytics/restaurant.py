import pandas as pd
import numpy as np
from typing import Dict
from app.analytics.common import round_num


def restaurant_analytics(df: pd.DataFrame, role_map: Dict[str, str]):
    rest_role = "restaurant_name" if "restaurant_name" in role_map else "restaurant_id"
    if rest_role not in role_map:
        return {"available": False, "reason": "No restaurant identifier/name column detected."}

    rest_col = role_map[rest_role]
    tmp = pd.DataFrame({"restaurant": df[rest_col].astype(str)})

    if "subtotal" in role_map:
        tmp["revenue"] = pd.to_numeric(df[role_map["subtotal"]], errors="coerce").fillna(0)
    if "profit" in df.columns:
        tmp["profit"] = df["profit"].fillna(0)
    if "customer_rating" in role_map:
        tmp["rating"] = pd.to_numeric(df[role_map["customer_rating"]], errors="coerce")
    if "actual_delivery_time" in role_map:
        tmp["delivery_time"] = pd.to_numeric(df[role_map["actual_delivery_time"]], errors="coerce")
    if "order_status" in role_map:
        tmp["is_cancelled"] = df[role_map["order_status"]].astype(str).str.lower().isin(["cancelled", "canceled", "failed"])

    agg_spec = {"orders": ("restaurant", "count")}
    grouped = tmp.groupby("restaurant").agg(orders=("restaurant", "count"))
    if "revenue" in tmp.columns:
        grouped["revenue"] = tmp.groupby("restaurant")["revenue"].sum()
        grouped["avg_order_value"] = grouped["revenue"] / grouped["orders"]
    if "profit" in tmp.columns:
        grouped["profit"] = tmp.groupby("restaurant")["profit"].sum()
        grouped["profit_margin"] = np.where(grouped.get("revenue", 1) > 0, grouped["profit"] / grouped["revenue"] * 100, np.nan)
    if "rating" in tmp.columns:
        grouped["avg_rating"] = tmp.groupby("restaurant")["rating"].mean()
    if "delivery_time" in tmp.columns:
        grouped["avg_delivery_time"] = tmp.groupby("restaurant")["delivery_time"].mean()
    if "is_cancelled" in tmp.columns:
        grouped["cancellation_rate"] = tmp.groupby("restaurant")["is_cancelled"].mean() * 100

    grouped = grouped.reset_index().fillna(0)

    result = {"available": True, "restaurants": grouped.round(2).to_dict(orient="records")}

    if "revenue" in grouped.columns:
        result["top_performing"] = grouped.sort_values("revenue", ascending=False).head(10).round(2).to_dict(orient="records")
        result["underperforming"] = grouped.sort_values("revenue", ascending=True).head(10).round(2).to_dict(orient="records")

    if "revenue" in grouped.columns and "avg_rating" in grouped.columns:
        rev_median = grouped["revenue"].median()
        rating_median = grouped["avg_rating"].median()
        result["high_revenue_low_rating"] = grouped[
            (grouped["revenue"] >= rev_median) & (grouped["avg_rating"] < rating_median)
        ].sort_values("revenue", ascending=False).round(2).to_dict(orient="records")
        result["high_rating_low_revenue"] = grouped[
            (grouped["avg_rating"] >= rating_median) & (grouped["revenue"] < rev_median)
        ].sort_values("avg_rating", ascending=False).round(2).to_dict(orient="records")

        insights = []
        if len(result["high_revenue_low_rating"]) > 0:
            names = ", ".join([r["restaurant"] for r in result["high_revenue_low_rating"][:3]])
            insights.append(
                f"Data-Driven Recommendation: {names} generate strong revenue despite below-median ratings — "
                f"investigate food quality and delivery operations before reputation impacts future demand."
            )
        if len(result["high_rating_low_revenue"]) > 0:
            names = ", ".join([r["restaurant"] for r in result["high_rating_low_revenue"][:3]])
            insights.append(
                f"Data-Driven Recommendation: {names} have excellent ratings but low revenue — "
                f"consider increased promotion or platform visibility to convert satisfaction into volume."
            )
        result["insights"] = insights

    return result
