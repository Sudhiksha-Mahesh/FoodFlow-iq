"""Configurable data cleaning: missing values, duplicates, invalid values."""
import pandas as pd
import numpy as np
from typing import Dict, Any
from app.etl.profiling import infer_column_type


def clean_dataset(df: pd.DataFrame, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    options:
      missing_strategy: "auto" | "drop_rows" | "fill_mean" | "fill_median" | "fill_mode" | "leave"
      remove_duplicates: bool
      handle_invalid_numeric: bool
    Returns dict with cleaned dataframe + before/after stats (Section 7).
    """
    options = options or {}
    missing_strategy = options.get("missing_strategy", "auto")
    remove_duplicates = options.get("remove_duplicates", True)
    handle_invalid_numeric = options.get("handle_invalid_numeric", True)

    before_rows, before_cols = df.shape
    before_missing = int(df.isna().sum().sum())
    before_dupes = int(df.duplicated().sum())

    cleaned = df.copy()

    # Normalize blank strings to NaN first
    cleaned = cleaned.replace(r"^\s*$", np.nan, regex=True)
    cleaned = cleaned.replace(["nan", "NaN", "None", "N/A", "n/a", "NA"], np.nan)

    # Handle invalid numeric values (coerce, keeping NaN for genuinely invalid entries)
    if handle_invalid_numeric:
        for col in cleaned.columns:
            col_type = infer_column_type(df[col])
            if col_type == "Numeric":
                cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
                # domain-sanity: negative money/quantity fields are invalid -> null them out
                if any(k in col.lower() for k in ["price", "amount", "subtotal", "fee", "revenue", "quantity", "distance"]):
                    cleaned.loc[cleaned[col] < 0, col] = np.nan

    # Parse date-like columns
    for col in cleaned.columns:
        col_type = infer_column_type(df[col])
        if col_type == "Date":
            cleaned[col] = pd.to_datetime(cleaned[col], errors="coerce")

    # Remove duplicates
    if remove_duplicates:
        cleaned = cleaned.drop_duplicates()

    # Missing value handling
    if missing_strategy != "leave":
        for col in cleaned.columns:
            col_type = infer_column_type(df[col])
            n_missing = cleaned[col].isna().sum()
            if n_missing == 0:
                continue
            if missing_strategy == "drop_rows":
                continue  # handled after loop
            if col_type == "Numeric":
                if missing_strategy in ("auto", "fill_median"):
                    cleaned[col] = cleaned[col].fillna(cleaned[col].median())
                elif missing_strategy == "fill_mean":
                    cleaned[col] = cleaned[col].fillna(cleaned[col].mean())
            elif col_type == "Date":
                # cannot safely fabricate a date -> leave as NaT, drop only if row entirely unusable later
                continue
            else:
                if missing_strategy in ("auto", "fill_mode"):
                    mode = cleaned[col].mode(dropna=True)
                    if len(mode) > 0:
                        cleaned[col] = cleaned[col].fillna(mode.iloc[0])
                    else:
                        cleaned[col] = cleaned[col].fillna("Unknown")

        if missing_strategy == "drop_rows":
            cleaned = cleaned.dropna()

    # Always drop rows with an unrecoverable (NaT) primary date, since most analytics need it
    date_cols = [c for c in cleaned.columns if infer_column_type(df[c]) == "Date"]
    if date_cols:
        cleaned = cleaned.dropna(subset=[date_cols[0]])

    after_rows, after_cols = cleaned.shape
    after_missing = int(cleaned.isna().sum().sum())
    after_dupes = int(cleaned.duplicated().sum())

    return {
        "dataframe": cleaned,
        "before": {"rows": before_rows, "missing": before_missing, "duplicates": before_dupes},
        "after": {"rows": after_rows, "missing": after_missing, "duplicates": after_dupes},
        "rows_removed": before_rows - after_rows,
    }
