# FoodFlow IQ: Analytics Modules and Core Concepts

This project is built around the idea of turning raw food-delivery transaction data into business intelligence, operational insight, and predictive analytics without assuming one fixed CSV layout.

The key design principle is: detect what columns exist, map them to canonical business roles, and run only the modules that are valid for that dataset.

---

## 1. Core concepts used in the project

### 1.1 Canonical role mapping
The system does not depend on fixed column names like `order_date` or `customer_id` existing in a single exact format. Instead, it normalizes and matches incoming columns to a standard internal vocabulary.

Example:
- `Order Date` -> `order_date`
- `cust_id` -> `customer_id`
- `revenue` or `amount` -> `subtotal`
- `Restaurant Name` -> `restaurant_name`

This logic is implemented in:
- `backend/app/utils/schema_detection.py`

The role map is stored as a dictionary such as:

```python
role_map = {
    "order_date": "Order Date",
    "customer_id": "cust_id",
    "subtotal": "Revenue",
    "restaurant_name": "Restaurant Name",
}
```

This is the foundation of the whole app. Once the roles are known, every module operates on business concepts instead of raw spreadsheet column names.

### 1.2 Graceful degradation
If a dataset lacks a required field, the app does not invent fake values. Instead, it marks the module as unavailable or partial.

This is implemented using compatibility checks and status values such as:
- Available
- Partial
- Unavailable

This is handled in:
- `backend/app/utils/schema_detection.py`

So the system is robust even when the uploaded CSV is messy or incomplete.

### 1.3 Dynamic filtering
The dashboard uses filters only for fields that actually exist in the dataset.

Examples of supported filters:
- date range
- city
- restaurant
- cuisine
- payment method
- order status

This is implemented in:
- `backend/app/analytics/common.py`

These functions dynamically build valid filter options from the detected columns and filter the dataframe before running analytics.

### 1.4 Data preparation and transformation pipeline
Every dataset goes through a standard pipeline:
1. Upload
2. Validate file structure
3. Inspect and profile columns
4. Clean invalid values / duplicates / nulls
5. Transform derived fields
6. Run analytics or ML modules

The cleaning logic is in:
- `backend/app/etl/cleaning.py`

The transformation logic is in:
- `backend/app/etl/transform.py`

Examples of derived fields:
- `total_amount`
- `profit`
- `profit_margin`
- `order_year`
- `order_month`
- `day_of_week`
- `order_hour`
- `is_peak_hour`
- `delivery_delay`
- `is_late`

These fields are created only when their source columns exist, which keeps the logic safe and realistic.

### 1.5 KPI-based analytics
Most modules are implemented as aggregations over the transformed data frame. They calculate metrics such as:
- revenue
- orders
- average order value (AOV)
- cancellation rate
- average delivery time
- ratings
- profit
- customer counts

The project uses pandas groupby, aggregation, filtering, and summary statistics instead of hard-coded business rules.

### 1.6 Business logic without fabrication
The product follows a strict rule: never fabricate data. If a metric cannot be computed because the underlying field is missing, the module returns a reason like:
- "No customer identifier column detected."
- "Delivery time columns unavailable in this dataset."

This is one of the most important design principles behind the app.

---

## 2. Dashboard module

### Concept
The dashboard is the executive overview layer. It brings together high-level KPIs and performance summaries in a single place.

### Implementation
The API endpoints are defined in:
- `backend/app/api/dashboard.py`

It uses the same pattern for every dashboard page:
1. load dataset from storage
2. resolve role map
3. apply filters
4. call a module-specific analytics function
5. return JSON to the frontend

Examples:
- sales overview
- customer summary
- restaurant summary
- delivery summary
- time and location views

### What it shows
- total revenue
- total orders
- average order value
- total customers
- cancellation rate
- average rating
- delivery time summaries
- sales trends over time
- top-performing restaurants or cities

### Implementation detail
The dashboard page calls functions like:
- `sales_mod.sales_analytics(filtered, role_map)`
- `customer_mod.customer_analytics(filtered, role_map)`
- `restaurant_mod.restaurant_analytics(filtered, role_map)`
- `delivery_mod.delivery_analytics(filtered, role_map)`

This makes the frontend a presentation layer while the backend performs the actual logic.

---

## 3. Data preparation module

### Concept
This module prepares the raw uploaded CSV into a clean, usable, analysis-ready table. It focuses on quality and consistency.

### Implementation
The main logic is in:
- `backend/app/etl/cleaning.py`

### Core ideas used
- blank strings are converted to null values
- duplicates are removed
- invalid numeric values are coerced to NaN
- date-like columns are parsed with pandas
- missing values are handled according to chosen strategies such as:
  - mean
  - median
  - mode
  - drop rows
  - leave as-is
- rows with unusable primary date data are dropped for time-based analysis

### Why it matters
Without data preparation, the analytics layer would produce wrong or misleading numbers. This stage ensures the final dataset is consistent enough for KPI, segmentation, and ML workflows.

---

## 4. Sales analytics module

### Concept
Sales analytics tracks revenue and demand patterns across dimensions such as time, city, cuisine, and restaurant.

### Implementation
The module is in:
- `backend/app/analytics/sales.py`

### Core concepts used
- aggregation by group
- revenue calculation using `subtotal`
- KPI summaries
- time-series grouping by month/year
- dimension-based analysis using `groupby` on fields like:
  - `customer_city`
  - `cuisine`
  - `restaurant_name`
  - `food_category`
  - `order_status`
  - `payment_method`

### Example outputs
- revenue by month
- revenue by city
- revenue by cuisine
- leading restaurants by revenue
- top products by revenue
- payment method mix
- order status distribution

### Implementation pattern
The project uses a reusable helper called `group_metric()` to aggregate columns and return records like:

```python
{
  "group": "Bangalore",
  "revenue": 120000,
  "orders": 540,
  "quantity": 1300
}
```

This is then passed to the frontend for charts or tables.

---

## 5. Customer analytics module

### Concept
Customer analytics focuses on understanding who the customers are, how often they order, how much they spend, and which customer segments matter most.

### Implementation
The module is in:
- `backend/app/analytics/customer.py`

### Core concepts used
- customer-level aggregation
- RFM analysis
- customer segmentation
- top customer ranking
- repeat vs new customer comparison

### RFM concept
RFM stands for:
- Recency: how recently the customer ordered
- Frequency: how often the customer orders
- Monetary: how much revenue the customer brings

The project computes this in:
- `backend/app/analytics/rfm.py`

It assigns score bands and segments such as:
- Champions
- Loyal Customers
- New Customers
- At Risk
- Lost

### Why it matters
This gives a business view of customer value, retention potential, and churn risk. It is widely used in CRM and marketing analytics.

---

## 6. Restaurant analytics module

### Concept
Restaurant analytics evaluates which outlets are performing well and which ones need operational attention.

### Implementation
The module is in:
- `backend/app/analytics/restaurant.py`

### Core concepts used
- restaurant grouping
- revenue and order aggregation
- profit and profitability measures
- ratings analysis
- operation health comparison

### Business interpretation
The module highlights:
- high revenue + low rating restaurants
- high rating + low revenue restaurants
- top restaurants by revenue
- underperforming restaurants by order count or revenue

This helps the business separate two different problems:
- restaurants with poor quality or service
- restaurants with good quality but low demand exposure

### Implementation detail
The code groups rows by restaurant name or ID and calculates aggregates like:
- total revenue
- total orders
- avg rating
- avg delivery time
- cancellation rate
- profit margin

---

## 7. Delivery analytics module

### Concept
Delivery analytics evaluates operational performance such as speed, delay, efficiency, and route quality.

### Implementation
The module is in:
- `backend/app/analytics/delivery.py`

### Core concepts used
- delivery time analysis
- late delivery percentage
- partner ranking
- city-wise performance
- time-of-day delivery patterns
- distance vs time scatter analysis
- map-ready location aggregation

### Typical outputs
- average delivery time
- late delivery percentage
- restaurant-wise delivery performance
- city-wise average delivery time
- time-of-day hourly demand and execution pattern
- distance vs. time relationship
- partner ranking by speed and score

### Important note
The system checks if actual delivery columns are present before running this module. If not, it returns a clear informational error instead of pretending delivery data exists.

---

## 8. Implementation pattern across all modules

The project follows a consistent architecture across all analytics modules:

1. Read dataset from storage
2. Retrieve role map from schema detection
3. Apply dynamic filters
4. Validate required columns
5. Group or aggregate data with pandas
6. Produce structured JSON for the frontend
7. Render charts or tables in React using the returned result

This is implemented in:
- `backend/app/api/dashboard.py`
- `backend/app/analytics/common.py`
- each analytics file under `backend/app/analytics/`

This pattern makes the app modular, reusable, and resilient to varying dataset schemas.

---

## 9. Why this design is important

The project is not just a dashboard. It is an analytics engine for business intelligence.

It combines:
- schema-aware processing
- ETL and cleaning
- derived field creation
- KPI computation
- segmentation analytics
- operational monitoring
- ML and forecasting

This makes it useful for both descriptive analytics and predictive decision support.

---

## 10. Summary of the main modules

| Module | Main Concept | Typical Output |
|---|---|---|
| Dashboard | Executive overview | KPIs and summary cards |
| Data Preparation | Data quality and cleaning | Cleaned dataset and derived fields |
| Sales Analytics | Revenue and categories | Revenue trends, top products, segment reports |
| Customer Analytics | customer value and retention | RFM, top customers, churn-related segments |
| Restaurant Analytics | restaurant performance | revenue, rating, cancellation and quality gaps |
| Delivery Analytics | operations and fulfillment | speed, delays, city/partner metrics |

---

## 11. Final takeaway
FoodFlow IQ is built around a simple but powerful idea: treat data as a set of business roles, not as rigid spreadsheet columns. Once the roles are mapped, the platform can run meaningful business analytics across various modules without depending on a specific data format.

That is the central concept behind the entire application.
