import pandas as pd
import numpy as np
from typing import Dict
from app.analytics.common import round_num
from app.analytics.rfm import compute_rfm


def customer_analytics(df: pd.DataFrame, role_map: Dict[str, str]):
    if "customer_id" not in role_map:
        return {"available": False, "reason": "No customer identifier column detected."}

    rfm = compute_rfm(df, role_map)
    result = {"available": True}

    cust_col = role_map["customer_id"]
    total_customers = df[cust_col].nunique()
    result["total_customers"] = int(total_customers)

    if rfm is not None:
        new_customers = int((rfm["frequency"] == 1).sum())
        returning = int((rfm["frequency"] > 1).sum())
        result["new_customers"] = new_customers
        result["returning_customers"] = returning
        result["avg_orders_per_customer"] = round_num(rfm["frequency"].mean())
        if "subtotal" in role_map:
            result["avg_customer_spend"] = round_num(rfm["monetary"].mean())

        top_customers = rfm.sort_values("monetary", ascending=False).head(10)
        result["top_customers"] = top_customers[["customer_id", "frequency", "monetary", "recency", "segment"]].to_dict(orient="records")

        segment_counts = rfm["segment"].value_counts().to_dict()
        result["segments"] = [{"segment": k, "count": int(v)} for k, v in segment_counts.items()]

        table = rfm.copy()
        if "subtotal" in role_map:
            table["avg_order_value"] = table["monetary"] / table["frequency"]
        else:
            table["avg_order_value"] = np.nan
        table["last_order_date"] = table["last_order"].dt.date.astype(str)
        result["customer_table"] = table[[
            "customer_id", "frequency", "monetary", "avg_order_value",
            "last_order_date", "recency", "segment"
        ]].rename(columns={
            "frequency": "orders", "monetary": "total_spending"
        }).sort_values("total_spending", ascending=False).head(500).to_dict(orient="records")
    else:
        result["note"] = "Date column unavailable — RFM segmentation requires order dates."

    return result
