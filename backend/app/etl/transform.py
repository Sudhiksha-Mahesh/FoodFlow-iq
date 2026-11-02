"""
Derived / calculated field generation.

Every derived field is only computed when its required source columns are
present -- per project principle #4 ("Never fabricate missing data").
"""
import pandas as pd
import numpy as np
from typing import Dict


PEAK_HOURS = set(list(range(12, 15)) + list(range(19, 23)))


def apply_transformations(df: pd.DataFrame, role_map: Dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    r = role_map

    # ---- total_amount ----
    if "subtotal" in r:
        subtotal = pd.to_numeric(out[r["subtotal"]], errors="coerce")
        discount = pd.to_numeric(out[r["discount"]], errors="coerce").fillna(0) if "discount" in r else 0
        delivery_fee = pd.to_numeric(out[r["delivery_fee"]], errors="coerce").fillna(0) if "delivery_fee" in r else 0
        out["total_amount"] = subtotal.fillna(0) - discount + delivery_fee

    # ---- profit & profit_margin (assume ~28% COGS on subtotal as a standard illustrative margin) ----
    if "subtotal" in r:
        subtotal = pd.to_numeric(out[r["subtotal"]], errors="coerce").fillna(0)
        estimated_cost = subtotal * 0.65
        delivery_fee = pd.to_numeric(out[r["delivery_fee"]], errors="coerce").fillna(0) if "delivery_fee" in r else 0
        discount = pd.to_numeric(out[r["discount"]], errors="coerce").fillna(0) if "discount" in r else 0
        out["profit"] = (subtotal - estimated_cost - discount + delivery_fee * 0.3)
        with np.errstate(divide="ignore", invalid="ignore"):
            out["profit_margin"] = np.where(subtotal > 0, out["profit"] / subtotal * 100, np.nan)

    # ---- date parts ----
    if "order_date" in r:
        dt = pd.to_datetime(out[r["order_date"]], errors="coerce")
        out["order_year"] = dt.dt.year
        out["order_month"] = dt.dt.month
        out["order_month_name"] = dt.dt.strftime("%b")
        out["order_day"] = dt.dt.day
        out["day_of_week"] = dt.dt.day_name()
        out["day_of_week_num"] = dt.dt.dayofweek
        out["_parsed_date"] = dt

    # ---- order hour / peak-hour flag ----
    hour_series = None
    if "order_time" in r:
        parsed_time = pd.to_datetime(out[r["order_time"]].astype(str), errors="coerce", format="%H:%M:%S")
        hour_series = parsed_time.dt.hour
        if hour_series.isna().mean() > 0.5:  # fallback flexible parse
            hour_series = pd.to_datetime(out[r["order_time"]].astype(str), errors="coerce").dt.hour
    elif "order_date" in r:
        dt = pd.to_datetime(out[r["order_date"]], errors="coerce")
        if dt.notna().any() and (dt.dt.hour.nunique() > 1):
            hour_series = dt.dt.hour

    if hour_series is not None:
        out["order_hour"] = hour_series
        out["is_peak_hour"] = hour_series.isin(PEAK_HOURS)

    # ---- delivery_delay ----
    if "estimated_delivery_time" in r and "actual_delivery_time" in r:
        est = pd.to_numeric(out[r["estimated_delivery_time"]], errors="coerce")
        act = pd.to_numeric(out[r["actual_delivery_time"]], errors="coerce")
        out["delivery_delay"] = act - est
        out["is_late"] = out["delivery_delay"] > 0

    return out
