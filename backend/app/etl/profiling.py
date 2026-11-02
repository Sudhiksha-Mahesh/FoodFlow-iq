"""Data profiling: column typing, missing values, duplicates, outliers, quality score."""
import pandas as pd
import numpy as np
from typing import Dict, Any


def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "Numeric"

    non_null = series.dropna()
    if len(non_null) == 0:
        return "String"

    # A column can end up as object dtype purely because a handful of rows
    # contain invalid tokens ("N/A", "-999", etc) alongside otherwise-numeric
    # values -- exactly the kind of data-quality issue this platform is meant
    # to catch. Treat it as Numeric (with those bad values later flagged as
    # "Invalid values") if the large majority of non-null entries parse as numbers.
    numeric_coerced = pd.to_numeric(non_null, errors="coerce")
    if numeric_coerced.notna().mean() > 0.7:
        return "Numeric"

    # try date
    sample = non_null.astype(str).head(50)
    if len(sample) > 0:
        parsed = pd.to_datetime(sample, errors="coerce")
        if parsed.notna().mean() > 0.8:
            return "Date"
    return "String"


def detect_outliers_iqr(series: pd.Series) -> int:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 10:
        return 0
    q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((numeric < lower) | (numeric > upper)).sum())


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    n_rows, n_cols = df.shape
    duplicate_rows = int(df.duplicated().sum())

    column_profiles = []
    total_missing = 0
    total_issues = 0
    numeric_cols, categorical_cols, date_cols = 0, 0, 0

    for col in df.columns:
        series = df[col]
        col_type = infer_column_type(series)
        missing = int(series.isna().sum() + (series.astype(str).str.strip() == "").sum())
        # avoid double counting NaN as empty string
        missing = int(series.isna().sum())
        blank = int((series.astype(str).str.strip().isin(["", "nan", "NaT", "None", "N/A", "n/a", "NA"])).sum())
        missing = max(missing, blank)
        unique = int(series.nunique(dropna=True))

        issues = []
        if missing > 0:
            issues.append("Missing")
        outliers = 0
        if col_type == "Numeric":
            numeric_cols += 1
            outliers = detect_outliers_iqr(series)
            if outliers > 0:
                issues.append("Outliers")
            # invalid numeric strings mixed in an otherwise numeric column
            coerced = pd.to_numeric(series, errors="coerce")
            invalid = int(coerced.isna().sum() - series.isna().sum())
            if invalid > 0:
                issues.append("Invalid values")
        elif col_type == "Date":
            date_cols += 1
            coerced = pd.to_datetime(series, errors="coerce")
            invalid = int(coerced.isna().sum() - series.isna().sum())
            if invalid > 0:
                issues.append("Invalid dates")
        else:
            categorical_cols += 1

        total_missing += missing
        total_issues += len(issues)

        column_profiles.append({
            "column": col,
            "type": col_type,
            "missing": missing,
            "missing_pct": round(missing / n_rows * 100, 2) if n_rows else 0,
            "unique": unique,
            "outliers": outliers,
            "issues": issues if issues else ["None"],
        })

    # Simple, transparent data quality score (Section 6)
    completeness = 1 - (total_missing / (n_rows * n_cols)) if n_rows and n_cols else 0
    duplicate_penalty = min(duplicate_rows / n_rows, 0.2) if n_rows else 0
    quality_score = max(0, round((completeness - duplicate_penalty) * 100, 1))

    return {
        "rows": n_rows,
        "columns": n_cols,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "missing_values": total_missing,
        "duplicate_rows": duplicate_rows,
        "data_quality_score": quality_score,
        "column_profiles": column_profiles,
    }
