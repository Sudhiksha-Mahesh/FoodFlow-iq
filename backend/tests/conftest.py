import os
import sys
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "order_id": [f"O{i}" for i in range(1, 21)],
        "order_date": pd.date_range("2026-01-01", periods=20).astype(str).tolist(),
        "customer_id": [f"C{i % 5}" for i in range(20)],
        "restaurant_name": [f"Restaurant {i % 3}" for i in range(20)],
        "cuisine": ["Indian", "Chinese", "Italian"] * 6 + ["Indian", "Chinese"],
        "subtotal": [100 + i * 10 for i in range(20)],
        "discount": [0] * 20,
        "delivery_fee": [30] * 20,
        "quantity": [1 + (i % 3) for i in range(20)],
        "order_status": ["Delivered"] * 17 + ["Cancelled", "Failed", "Delivered"],
        "customer_rating": [4.0, 3.5, 5.0, None] * 5,
        "actual_delivery_time": [30 + i for i in range(20)],
        "estimated_delivery_time": [28] * 20,
    })


@pytest.fixture
def messy_df():
    df = pd.DataFrame({
        "order_id": ["O1", "O2", "O3", "O3", "O4"],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-03", "31/31/2025"],
        "customer_id": ["C1", "C2", "C3", "C3", "C4"],
        "subtotal": [100, -50, 200, 200, "N/A"],
    })
    return df
