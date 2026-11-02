# CSV Dataset Format — FoodFlow IQ

FoodFlow IQ works with **any transactional CSV** as long as it contains, at minimum,
a date column and a numeric amount/revenue column (or the columns needed for the
specific module you want to use — see the compatibility table shown after upload).

The table below documents the **recommended full schema** (also used to generate
`data/sample_food_delivery_orders.csv`). Column names are matched flexibly and
case-insensitively — `Order ID`, `order_id`, and `OrderID` are all recognised —
so you rarely need to rename anything before uploading.

| Column                        | Type      | Required for                          | Notes |
|--------------------------------|-----------|----------------------------------------|-------|
| `order_id`                    | String    | Recommendation engine (Apriori)        | Same value across rows of a multi-item order |
| `order_date`                  | Date      | Almost every module                    | Any common date format |
| `order_time`                  | Time      | Peak-hour / time analytics             | `HH:MM:SS` |
| `customer_id`                 | String    | Customer analytics, RFM, churn         | |
| `customer_age`                | Numeric   | Optional demographic breakdowns        | |
| `customer_gender`             | String    | Optional demographic breakdowns        | |
| `customer_city`               | String    | Location filters/analytics             | |
| `customer_area`               | String    | Location filters/analytics             | |
| `customer_type`                | String    | Segmentation filter                    | e.g. New / Regular / Premium |
| `restaurant_id`               | String    | Restaurant analytics                   | |
| `restaurant_name`             | String    | Restaurant analytics (display name)    | |
| `cuisine`                     | String    | Sales/restaurant breakdowns            | |
| `food_category`               | String    | Sales breakdowns                       | |
| `food_item`                   | String    | Top products, Apriori                  | |
| `quantity`                    | Numeric   | Quantity-based rankings                | |
| `unit_price`                  | Numeric   | Derived revenue fallback               | |
| `subtotal`                    | Numeric   | **Revenue/amount** — core KPI driver   | Falls back to any large-magnitude numeric column if absent |
| `discount`                    | Numeric   | `total_amount`, discount-usage feature | |
| `delivery_fee`                | Numeric   | `total_amount`                         | |
| `payment_method`              | String    | Payment-method breakdown                | |
| `order_status`                | String    | Cancellation rate, churn features       | Delivered / Cancelled / Failed |
| `delivery_partner_id`         | String    | Delivery partner ranking                | |
| `delivery_partner_experience` | String    | Delivery partner analysis               | |
| `distance_km`                 | Numeric   | Distance vs. time scatter               | |
| `estimated_delivery_time`     | Numeric (min) | `delivery_delay`                    | |
| `actual_delivery_time`        | Numeric (min) | Delivery analytics                  | |
| `customer_rating`             | Numeric (1–5) | Rating KPIs                          | |
| `delivery_rating`             | Numeric (1–5) | Delivery partner ratings              | |
| `latitude` / `longitude`      | Numeric   | Map visualisation                       | Optional |

## Minimum viable dataset

At minimum, upload a CSV with:
- A date column
- A numeric amount/revenue column
- Ideally a customer identifier (for customer analytics, RFM, churn) and a
  restaurant/product identifier (for restaurant and sales analytics)

If a column is missing, the corresponding module is marked **Unavailable** or
**Partial** in the app rather than being silently skipped or fabricated — see
the "Dataset Compatibility" panel shown right after upload.

## Data-quality expectations

The ETL layer will happily handle:
- Missing values (multiple strategies: mean/median/mode fill, drop rows, leave as-is)
- Duplicate rows
- Invalid numeric values (non-numeric strings, negative amounts)
- Unparseable dates (rows are excluded only for the primary date column, since most analytics require it)

It will **reject** a CSV outright only if:
- The file isn't a `.csv`
- It's empty or unreadable/corrupt
- It has duplicate column names
- It has no date column **and** no numeric amount/revenue column
