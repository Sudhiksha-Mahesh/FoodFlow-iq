from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CleanOptions(BaseModel):
    missing_strategy: str = "auto"          # auto | drop_rows | fill_mean | fill_median | fill_mode | leave
    remove_duplicates: bool = True
    handle_invalid_numeric: bool = True


class FilterParams(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    city: Optional[List[str]] = None
    restaurant: Optional[List[str]] = None
    cuisine: Optional[List[str]] = None
    order_status: Optional[List[str]] = None
    payment_method: Optional[List[str]] = None
    customer_type: Optional[List[str]] = None
    food_category: Optional[List[str]] = None


class ForecastRequest(BaseModel):
    group_by: Optional[str] = None   # city | restaurant | cuisine | None (overall)
    group_value: Optional[str] = None
    horizon: int = 7


class ChurnRequest(BaseModel):
    churn_threshold_days: int = 60
    low_max: int = 30
    medium_max: int = 60


class AprioriRequest(BaseModel):
    min_support: float = 0.01
    min_confidence: float = 0.2
    min_lift: float = 1.0
