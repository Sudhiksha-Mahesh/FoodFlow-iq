import pandas as pd
import numpy as np
from typing import Dict
from app.analytics.common import round_num


def delivery_analytics(df: pd.DataFrame, role_map: Dict[str, str]):
    if "actual_delivery_time" not in role_map:
        return {"available": False, "reason": "Delivery time columns unavailable in this dataset."}

    delivery_time = pd.to_numeric(df[role_map["actual_delivery_time"]], errors="coerce")
    result = {"available": True, "avg_delivery_time": round_num(delivery_time.mean())}

    if "delivery_delay" in df.columns:
        result["avg_delivery_delay"] = round_num(df["delivery_delay"].mean())
        result["late_delivery_pct"] = round_num((df["delivery_delay"] > 0).mean() * 100)

    if "order_status" in role_map:
        status = df[role_map["order_status"]].astype(str)
        result["cancellation_rate"] = round_num(status.str.lower().isin(["cancelled", "canceled", "failed"]).mean() * 100)

    if "restaurant_name" in role_map:
        result["delivery_time_by_restaurant"] = (
            df.groupby(role_map["restaurant_name"])[role_map["actual_delivery_time"]]
            .apply(lambda s: pd.to_numeric(s, errors="coerce").mean())
            .sort_values(ascending=False).head(15).round(1)
            .reset_index().rename(columns={role_map["restaurant_name"]: "restaurant", role_map["actual_delivery_time"]: "avg_delivery_time"})
            .to_dict(orient="records")
        )

    if "customer_city" in role_map:
        result["delivery_time_by_city"] = (
            df.groupby(role_map["customer_city"])[role_map["actual_delivery_time"]]
            .apply(lambda s: pd.to_numeric(s, errors="coerce").mean())
            .round(1).reset_index()
            .rename(columns={role_map["customer_city"]: "city", role_map["actual_delivery_time"]: "avg_delivery_time"})
            .to_dict(orient="records")
        )

    if "order_hour" in df.columns:
        result["delivery_time_by_hour"] = (
            df.groupby("order_hour")[role_map["actual_delivery_time"]]
            .apply(lambda s: pd.to_numeric(s, errors="coerce").mean())
            .round(1).reset_index()
            .rename(columns={role_map["actual_delivery_time"]: "avg_delivery_time"})
            .sort_values("order_hour").to_dict(orient="records")
        )

    if "distance_km" in role_map:
        dist = pd.to_numeric(df[role_map["distance_km"]], errors="coerce")
        scatter = pd.DataFrame({"distance": dist, "time": delivery_time}).dropna()
        if len(scatter) > 500:
            scatter = scatter.sample(500, random_state=42)
        result["distance_vs_time"] = scatter.round(2).to_dict(orient="records")

    if "delivery_partner_id" in role_map:
        agg = {"orders": (role_map["delivery_partner_id"], "count")}
        partner_group = df.groupby(role_map["delivery_partner_id"]).agg(
            orders=(role_map["delivery_partner_id"], "count"),
            avg_delivery_time=(role_map["actual_delivery_time"], lambda s: pd.to_numeric(s, errors="coerce").mean()),
        ).reset_index().rename(columns={role_map["delivery_partner_id"]: "partner_id"})
        if "delivery_rating" in role_map:
            partner_group["avg_delivery_rating"] = df.groupby(role_map["delivery_partner_id"])[role_map["delivery_rating"]].apply(
                lambda s: pd.to_numeric(s, errors="coerce").mean()
            ).values
        result["delivery_partner_ranking"] = partner_group.sort_values("orders", ascending=False).head(15).round(2).to_dict(orient="records")

    if "order_hour" in df.columns and "is_peak_hour" in df.columns:
        peak = df.groupby("is_peak_hour")[role_map["actual_delivery_time"]].apply(
            lambda s: pd.to_numeric(s, errors="coerce").mean()
        )
        result["peak_hour_avg_delivery_time"] = round_num(peak.get(True, np.nan))
        result["offpeak_hour_avg_delivery_time"] = round_num(peak.get(False, np.nan))

    return result


def location_analytics(df: pd.DataFrame, role_map: Dict[str, str]):
    """Geographic breakdown for map visualization (Section 15). Only returns real
    lat/long points when both columns are present -- never fabricates coordinates."""
    has_latlong = "latitude" in role_map and "longitude" in role_map

    if not has_latlong:
        if "customer_city" not in role_map:
            return {"available": False, "reason": "Location columns (latitude/longitude or city) unavailable."}
        # Fallback: city-level aggregate without a map (Leaflet needs coordinates)
        agg = df.groupby(role_map["customer_city"]).size().reset_index(name="orders")
        return {
            "available": True, "has_coordinates": False,
            "city_breakdown": agg.sort_values("orders", ascending=False).to_dict(orient="records"),
        }

    lat = pd.to_numeric(df[role_map["latitude"]], errors="coerce")
    lon = pd.to_numeric(df[role_map["longitude"]], errors="coerce")
    tmp = pd.DataFrame({"lat": lat, "lon": lon})
    if "subtotal" in role_map:
        tmp["revenue"] = pd.to_numeric(df[role_map["subtotal"]], errors="coerce").fillna(0)
    tmp = tmp.dropna(subset=["lat", "lon"])

    # Round to ~3 decimal places (~100m) to cluster nearby points rather than
    # plotting every single raw order coordinate.
    tmp["lat_r"] = tmp["lat"].round(3)
    tmp["lon_r"] = tmp["lon"].round(3)
    agg_spec = {"orders": ("lat", "count")}
    grouped = tmp.groupby(["lat_r", "lon_r"]).agg(orders=("lat", "count"))
    if "revenue" in tmp.columns:
        grouped["revenue"] = tmp.groupby(["lat_r", "lon_r"])["revenue"].sum()
    grouped = grouped.reset_index().rename(columns={"lat_r": "lat", "lon_r": "lon"})
    grouped = grouped.sort_values("orders", ascending=False).head(300)

    return {"available": True, "has_coordinates": True, "points": grouped.round(2).to_dict(orient="records")}


def time_analytics(df: pd.DataFrame, role_map: Dict[str, str]):
    if "order_hour" not in df.columns and "day_of_week" not in df.columns:
        return {"available": False, "reason": "Date/time columns unavailable."}

    result = {"available": True}

    if "order_hour" in df.columns:
        by_hour = df.groupby("order_hour").size().reset_index(name="orders").sort_values("order_hour")
        result["orders_by_hour"] = by_hour.to_dict(orient="records")
        result["peak_hour"] = int(by_hour.loc[by_hour["orders"].idxmax(), "order_hour"]) if len(by_hour) else None

    if "day_of_week" in df.columns:
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        by_dow = df.groupby("day_of_week").size().reindex(order).fillna(0).reset_index()
        by_dow.columns = ["day_of_week", "orders"]
        result["orders_by_day_of_week"] = by_dow.to_dict(orient="records")
        result["peak_day"] = by_dow.loc[by_dow["orders"].idxmax(), "day_of_week"] if len(by_dow) else None

    if "order_month_name" in df.columns and "order_year" in df.columns:
        by_month = df.groupby(["order_year", "order_month", "order_month_name"]).size().reset_index(name="orders")
        by_month = by_month.sort_values(["order_year", "order_month"])
        result["orders_by_month"] = by_month[["order_month_name", "orders"]].to_dict(orient="records")

    if "order_hour" in df.columns and "day_of_week" in df.columns:
        heat = df.groupby(["day_of_week", "order_hour"]).size().reset_index(name="orders")
        result["heatmap_day_hour"] = heat.to_dict(orient="records")

    return result
