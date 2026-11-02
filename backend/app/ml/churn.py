"""
Customer churn prediction.

Churn label definition (transparent, configurable):
  A customer is "churned" if days-since-last-order (recency) exceeds the
  configured threshold, measured relative to the observation date
  (max order date + 1 day found in the dataset).

To avoid trivial label leakage, `recency` itself is EXCLUDED from the model's
feature set — the model instead has to learn churn risk from behavioural
signals (frequency, spend, delivery experience, ratings, discount usage),
which is what makes the prediction genuinely useful.
"""
import numpy as np
import pandas as pd
from typing import Dict
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)

MIN_CUSTOMERS_RECOMMENDED = 200


def build_customer_features(df: pd.DataFrame, role_map: Dict[str, str], churn_threshold_days: int = 60) -> pd.DataFrame:
    if "customer_id" not in role_map or "_parsed_date" not in df.columns:
        return None

    cust_col = role_map["customer_id"]
    observation_date = df["_parsed_date"].max() + pd.Timedelta(days=1)

    g = df.groupby(cust_col)
    feats = pd.DataFrame(index=g.size().index)
    feats["total_orders"] = g.size()
    feats["recency"] = (observation_date - g["_parsed_date"].max()).dt.days

    if "subtotal" in role_map:
        feats["monetary"] = g[role_map["subtotal"]].sum()
        feats["avg_order_value"] = feats["monetary"] / feats["total_orders"]
    else:
        feats["monetary"] = 0
        feats["avg_order_value"] = 0

    if "actual_delivery_time" in role_map:
        feats["avg_delivery_time"] = g[role_map["actual_delivery_time"]].apply(lambda s: pd.to_numeric(s, errors="coerce").mean())
    else:
        feats["avg_delivery_time"] = np.nan

    if "order_status" in role_map:
        feats["cancellation_count"] = g[role_map["order_status"]].apply(
            lambda s: s.astype(str).str.lower().isin(["cancelled", "canceled", "failed"]).sum()
        )
    else:
        feats["cancellation_count"] = 0

    if "customer_rating" in role_map:
        feats["avg_rating"] = g[role_map["customer_rating"]].apply(lambda s: pd.to_numeric(s, errors="coerce").mean())
    else:
        feats["avg_rating"] = np.nan

    if "discount" in role_map:
        feats["discount_usage"] = g[role_map["discount"]].apply(lambda s: (pd.to_numeric(s, errors="coerce").fillna(0) > 0).mean())
    else:
        feats["discount_usage"] = 0

    feats = feats.reset_index().rename(columns={cust_col: "customer_id"})
    feats["churned"] = (feats["recency"] > churn_threshold_days).astype(int)
    feats = feats.fillna(feats.median(numeric_only=True))
    return feats


def train_churn_models(features: pd.DataFrame) -> Dict:
    n = len(features)
    if n < 30:
        return {"available": False, "reason": f"Only {n} customers detected — at least 30 are required to train a churn model, 200+ recommended for reliable results."}

    class_counts = features["churned"].value_counts()
    if len(class_counts) < 2 or class_counts.min() < 5:
        return {"available": False, "reason": "Insufficient churned/active class balance to train a reliable model (need examples of both classes)."}

    feature_cols = ["total_orders", "monetary", "avg_order_value", "avg_delivery_time",
                     "cancellation_count", "avg_rating", "discount_usage"]
    feature_cols = [c for c in feature_cols if c in features.columns]

    X = features[feature_cols].fillna(0)
    y = features["churned"]

    test_size = 0.25 if n >= 100 else 0.3
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, features.index, test_size=test_size, random_state=42, stratify=y if class_counts.min() >= 2 else None
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "decision_tree": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=200, max_depth=8, class_weight="balanced", random_state=42),
    }

    model_results = {}
    fitted_models = {}
    for name, model in models.items():
        Xtr = X_train_scaled if name == "logistic_regression" else X_train
        Xte = X_test_scaled if name == "logistic_regression" else X_test
        model.fit(Xtr, y_train)
        preds = model.predict(Xte)
        probs = model.predict_proba(Xte)[:, 1]

        metrics = {
            "accuracy": round(accuracy_score(y_test, preds), 3),
            "precision": round(precision_score(y_test, preds, zero_division=0), 3),
            "recall": round(recall_score(y_test, preds, zero_division=0), 3),
            "f1_score": round(f1_score(y_test, preds, zero_division=0), 3),
        }
        try:
            metrics["roc_auc"] = round(roc_auc_score(y_test, probs), 3)
        except Exception:
            metrics["roc_auc"] = None
        cm = confusion_matrix(y_test, preds).tolist()
        model_results[name] = {"metrics": metrics, "confusion_matrix": cm}
        fitted_models[name] = model

    best_name = max(model_results, key=lambda k: (model_results[k]["metrics"]["roc_auc"] or 0))
    best_model = fitted_models[best_name]

    # Predict probability for ALL customers using the best model
    X_all = features[feature_cols].fillna(0)
    X_all_input = scaler.transform(X_all) if best_name == "logistic_regression" else X_all
    all_probs = best_model.predict_proba(X_all_input)[:, 1]

    features_out = features.copy()
    features_out["churn_probability"] = (all_probs * 100).round(1)

    return {
        "available": True,
        "feature_columns": feature_cols,
        "model_comparison": model_results,
        "best_model": best_name,
        "customer_predictions": features_out,
    }


def risk_level(prob_pct: float, low_max=30, medium_max=60) -> str:
    if prob_pct <= low_max:
        return "Low"
    if prob_pct <= medium_max:
        return "Medium"
    return "High"
