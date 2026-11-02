"""
Demand forecasting: aggregates historical order counts by day and compares
three approaches (Moving Average baseline, Simple Exponential Smoothing,
ARIMA), selecting whichever scores best on a holdout window.
"""
import warnings
import numpy as np
import pandas as pd
from typing import Dict, Optional

warnings.filterwarnings("ignore")


def _daily_series(df: pd.DataFrame, role_map: Dict[str, str], group_by: Optional[str] = None, group_value: Optional[str] = None) -> Optional[pd.Series]:
    if "_parsed_date" not in df.columns:
        return None
    working = df
    if group_by and group_by in role_map and group_value:
        working = working[working[role_map[group_by]].astype(str) == str(group_value)]
    daily = working.groupby(working["_parsed_date"].dt.date).size()
    if daily.empty:
        return None
    idx = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily.index = pd.to_datetime(daily.index)
    daily = daily.reindex(idx, fill_value=0)
    return daily


def _eval(actual, predicted):
    actual, predicted = np.array(actual, dtype=float), np.array(predicted, dtype=float)
    mae = float(np.mean(np.abs(actual - predicted)))
    mse = float(np.mean((actual - predicted) ** 2))
    rmse = float(np.sqrt(mse))
    return {"mae": round(mae, 2), "mse": round(mse, 2), "rmse": round(rmse, 2)}


def moving_average_forecast(series: pd.Series, window: int, horizon: int):
    ma = series.rolling(window).mean()
    last_val = ma.iloc[-1] if not np.isnan(ma.iloc[-1]) else series.mean()
    return [round(max(0, last_val), 1)] * horizon, ma


def ses_forecast(series: pd.Series, horizon: int):
    from statsmodels.tsa.holtwinters import SimpleExpSmoothing
    model = SimpleExpSmoothing(series.values, initialization_method="estimated").fit()
    fitted = model.fittedvalues
    forecast = model.forecast(horizon)
    return [round(max(0, v), 1) for v in forecast], fitted, model


def arima_forecast(series: pd.Series, horizon: int):
    from statsmodels.tsa.arima.model import ARIMA
    order = (2, 1, 2) if len(series) > 30 else (1, 1, 1)
    model = ARIMA(series.values, order=order).fit()
    fitted = model.fittedvalues
    forecast = model.forecast(horizon)
    return [round(max(0, v), 1) for v in forecast], fitted, model


def run_forecast(df: pd.DataFrame, role_map: Dict[str, str], group_by: Optional[str] = None,
                  group_value: Optional[str] = None, horizon: int = 7) -> Dict:
    series = _daily_series(df, role_map, group_by, group_value)
    if series is None or len(series) < 14:
        return {
            "available": False,
            "reason": f"At least 14 days of order history are required for reliable forecasting; "
                      f"{0 if series is None else len(series)} days found."
        }

    n_test = max(3, min(7, len(series) // 5))
    train, test = series.iloc[:-n_test], series.iloc[-n_test:]

    results = {}

    # Baseline: Moving Average
    window = min(7, max(2, len(train) // 4))
    ma_pred_test = [train.rolling(window).mean().iloc[-1]] * len(test)
    results["moving_average"] = {"metrics": _eval(test.values, ma_pred_test)}

    # SES
    try:
        ses_pred_test, _, _ = ses_forecast(train, len(test))
        results["exponential_smoothing"] = {"metrics": _eval(test.values, ses_pred_test)}
    except Exception as e:
        results["exponential_smoothing"] = {"error": str(e)}

    # ARIMA
    try:
        arima_pred_test, _, _ = arima_forecast(train, len(test))
        results["arima"] = {"metrics": _eval(test.values, arima_pred_test)}
    except Exception as e:
        results["arima"] = {"error": str(e)}

    # Pick best by RMSE among models that succeeded
    valid = {k: v["metrics"]["rmse"] for k, v in results.items() if "metrics" in v}
    best_model = min(valid, key=valid.get) if valid else "moving_average"

    # Refit best model on FULL series to produce the actual future forecast
    if best_model == "moving_average":
        future, _ = moving_average_forecast(series, window, horizon)
    elif best_model == "exponential_smoothing":
        future, _, _ = ses_forecast(series, horizon)
    else:
        future, _, _ = arima_forecast(series, horizon)

    future_dates = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=horizon)

    # Peak day / hour insight (only if defensible from data)
    peak_day = None
    if "day_of_week" in df.columns:
        by_dow = df.groupby("day_of_week").size()
        peak_day = by_dow.idxmax()
    peak_hour_range = None
    if "order_hour" in df.columns:
        by_hour = df.groupby("order_hour").size()
        h = int(by_hour.idxmax())
        peak_hour_range = f"{h:02d}:00–{(h + 2) % 24:02d}:00"

    return {
        "available": True,
        "historical": {
            "dates": [d.date().isoformat() for d in series.index],
            "orders": [int(v) for v in series.values],
        },
        "forecast": {
            "dates": [d.date().isoformat() for d in future_dates],
            "orders": future,
        },
        "model_comparison": results,
        "best_model": best_model,
        "forecast_tomorrow": future[0] if future else None,
        "expected_peak_day": peak_day,
        "expected_peak_hour": peak_hour_range,
    }
