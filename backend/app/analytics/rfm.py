import pandas as pd
import numpy as np
from typing import Dict


def compute_rfm(df: pd.DataFrame, role_map: Dict[str, str]):
    """Returns None if required columns (customer_id, order_date) unavailable."""
    if "customer_id" not in role_map or "_parsed_date" not in df.columns:
        return None

    cust_col = role_map["customer_id"]
    has_amount = "subtotal" in role_map

    observation_date = df["_parsed_date"].max() + pd.Timedelta(days=1)

    agg = {"_parsed_date": ["max", "count"]}
    grouped = df.groupby(cust_col).agg(
        last_order=("_parsed_date", "max"),
        frequency=("_parsed_date", "count"),
    )
    if has_amount:
        monetary = df.groupby(cust_col)[role_map["subtotal"]].sum()
        grouped["monetary"] = monetary
    else:
        grouped["monetary"] = np.nan

    grouped["recency"] = (observation_date - grouped["last_order"]).dt.days
    grouped = grouped.reset_index().rename(columns={cust_col: "customer_id"})

    # Quantile-based scores (1 = worst, 5 = best). Guard against too few unique values.
    def qscore(series, ascending):
        try:
            ranked = pd.qcut(series.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
            scores = ranked.astype(int)
            return scores if ascending else (6 - scores)
        except Exception:
            return pd.Series([3] * len(series), index=series.index)

    grouped["r_score"] = qscore(grouped["recency"], ascending=False)  # low recency = good = high score
    grouped["f_score"] = qscore(grouped["frequency"], ascending=True)
    if has_amount:
        grouped["m_score"] = qscore(grouped["monetary"], ascending=True)
    else:
        grouped["m_score"] = 3

    grouped["rfm_score"] = grouped["r_score"].astype(int) + grouped["f_score"].astype(int) + grouped["m_score"].astype(int)

    def segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r >= 3 and f >= 4:
            return "Loyal Customers"
        if r >= 4 and f <= 2:
            return "New Customers"
        if r >= 3 and f >= 2 and m >= 3:
            return "Potential Loyalists"
        if r <= 2 and f >= 3 and m >= 3:
            return "At Risk"
        if r <= 2 and f >= 4 and m >= 4:
            return "Cannot Lose Them"
        if r <= 2 and f <= 2:
            return "Lost Customers"
        return "Potential Loyalists"

    grouped["segment"] = grouped.apply(segment, axis=1)

    return grouped
