
# FoodFlow IQ

**From every order to smarter delivery decisions.**

FoodFlow IQ is a dataset-driven **Business Intelligence** and **predictive analytics** platform for food-delivery operations. You upload a transactional CSV (or load the bundled sample). The app then detects the schema, profiles data quality, cleans and transforms the file, and unlocks analytics modules based on which columns actually exist.

Nothing is hard-coded to one retailer or one column layout. If a column is missing, that module is marked unavailable or partial — the app does not invent numbers.

---

## What the project does

A typical session looks like this:

1. **Upload** a food-delivery CSV (orders, customers, restaurants, items, delivery times, and so on).
2. **Validate and profile** the file: row/column counts, missing values, duplicates, inferred types, a data-quality score.
3. **Detect schema** by mapping messy column names (`Order Date`, `cust_id`, `amount`) onto canonical roles (`order_date`, `customer_id`, `subtotal`).
4. **Clean** (optional, configurable): fill or drop missing values, remove duplicates, parse dates, flag invalid numbers.
5. **Transform**: compute derived fields only when source columns exist (`total_amount`, date parts, peak-hour flags, delivery delay).
6. **Analyse** sales, customers (including RFM), restaurants, delivery, and time.
7. **Predict**: demand forecast, churn risk, market-basket product pairs.
8. **Recommend** operational actions from *computed* metric thresholds, not canned copy.

The UI is a React dashboard. The engine is a FastAPI backend that stores dataset *session metadata* in SQLite (or Postgres) and caches working tables as Parquet.

---

## Architecture (end to end)

```
CSV upload
  → validation
  → profiling
  → schema detection (column → role)
  → ETL / cleaning
  → transformation (derived fields)
  → descriptive analytics (sales / customer / restaurant / delivery / time)
  → ML (forecast / churn / Apriori)
  → rule-based recommendation engine
  → REST API
  → React dashboard
```

Conceptually the data is a **star / snowflake warehouse**: a central order fact plus customer, restaurant, food, date, partner, location, and payment dimensions. See `database/schema.sql` for the reference model. The running app keeps that as a *logical* model: metadata in SQL, bulk rows in Parquet — the same split real BI tools use.

```
foodflow-iq/
├── frontend/          React + TypeScript + Tailwind + ECharts + Leaflet
├── backend/           FastAPI + Pandas + scikit-learn + statsmodels + mlxtend
├── data/              Bundled sample CSV
├── database/          Reference star-schema DDL
├── scripts/           Sample-data generator and Windows start script
└── docker-compose.yml
```

---

## Modules and how they work

Each frontend page maps to backend analytics or ML. After upload, a **compatibility panel** shows which modules can run given the detected columns.

### 1. Dataset upload & session manager

**Pages:** Upload, Dataset Manager  
**Backend:** `backend/app/api/datasets.py`, `backend/app/services/dataset_store.py`

- Accepts `.csv` only, with size limits.
- Rejects empty files, duplicate column names, or files with **neither** a date column **nor** a numeric amount column.
- Creates a dataset session (id, name, row/column counts, status).
- Persists raw (and later cleaned) frames as Parquet under `STORAGE_DIR`.
- Sample load uses `data/sample_food_delivery_orders.csv` so you can demo without your own file.

### 2. Schema detection

**Backend:** `backend/app/utils/schema_detection.py`

The rest of the pipeline never looks at raw header strings. It uses **canonical roles**.

- Column names are normalized (`Order ID` → `order_id`) and matched with regex aliases (`cust_id` → `customer_id`, `revenue` → `subtotal`).
- If no amount column is named, a numeric column with large typical magnitude can be used as revenue.
- If no date column is named, object columns are parsed; a column that mostly converts to dates becomes `order_date`.
- Each analytics module declares **required roles**. Missing roles → `Unavailable` / `Partial`, with a reason — never silent zeros.

This is the main reason the product works on “any reasonable transactional CSV,” not only the sample schema. Full recommended columns: [CSV_DATASET_FORMAT.md](./CSV_DATASET_FORMAT.md).

### 3. Data profiling

**Backend:** `backend/app/etl/profiling.py`  
**Page:** shown immediately after upload; also Data Preparation

For every column the profiler infers **Numeric / Date / String**, counts missing and blank values, uniqueness, IQR outliers on numerics, and invalid mixed types. A simple **data-quality score** combines completeness with a penalty for duplicate rows.

### 4. ETL / data preparation

**Page:** Data Preparation  
**Backend:** `backend/app/etl/cleaning.py`, `backend/app/etl/transform.py`

**Cleaning (configurable):**

- Missing-value strategy: mean / median / mode fill, drop rows, or leave as-is.
- Duplicate-row removal.
- Date parsing; invalid primary dates are dropped because most time analytics need them.
- Invalid numeric strings coerced or flagged.

**Transformation — derived fields (only if sources exist):**

| Derived field | Needs | Meaning |
|---|---|---|
| `total_amount` | subtotal (+ discount, delivery fee) | Paid amount after discount + fee |
| `profit`, `profit_margin` | subtotal | Illustrative margin (assumed cost share; not true COGS) |
| `order_year` / `month` / `day_of_week` | order_date | Time hierarchy for BI grouping |
| `order_hour`, `is_peak_hour` | order_time or datetime | Lunch/dinner peaks (12–15, 19–23) |
| `delivery_delay`, `is_late` | estimated + actual delivery time | Actual minus ETA |

Before/after quality stats are returned so you can see what cleaning changed.

### 5. Executive dashboard

**Page:** Dashboard  
**Backend:** `backend/app/api/dashboard.py` + analytics packages

High-level KPIs (orders, revenue, AOV, ratings, cancellations — whatever columns allow), plus a **global filter bar** (city, cuisine, restaurant, date range, and so on). Filters are built dynamically from columns that actually exist. Charts use Apache ECharts; maps use Leaflet when lat/long exist, otherwise a city breakdown.

### 6. Sales analytics

**Page:** Sales  
**Backend:** `backend/app/analytics/sales.py`

Aggregations over the fact-like order table:

- Revenue and orders by month, cuisine, restaurant, city, food category
- Top products by revenue or quantity
- Payment-method mix
- Cancellation rate when `order_status` exists

**Concepts:** measures vs dimensions, group-by aggregation, KPI definition (AOV = revenue / orders).

### 7. Customer analytics + RFM

**Page:** Customer Analytics  
**Backend:** `backend/app/analytics/customer.py`, `backend/app/analytics/rfm.py`

Per-customer metrics: order count, spend, average order value, last order date.

**RFM segmentation** (classic CRM):

- **R**ecency — days since last order (relative to max date in the file + 1 day)
- **F**requency — number of orders
- **M**onetary — sum of amount

Each is scored 1–5 with quantiles (`qcut`). Segments such as Champions, Loyal, New, At Risk, Cannot Lose Them, Lost are assigned from R/F/M score combinations.

Needs `customer_id` and a date; monetary scoring is weaker without an amount column.

### 8. Restaurant analytics

**Page:** Restaurant Analytics  
**Backend:** `backend/app/analytics/restaurant.py`

Ranks restaurants by revenue, orders, and ratings. Highlights **high revenue + low rating** vs **high rating + low revenue** so operations and growth teams see different problems (quality vs under-marketing).

### 9. Delivery and time analytics

**Page:** Delivery Analytics  
**Backend:** `backend/app/analytics/delivery.py`

- Average actual delivery time, late %, delay distribution
- Partner ranking (when partner id / ratings exist)
- Distance vs time scatter (`distance_km` × delivery time)
- Day-of-week × hour **demand heatmap**
- Peak-hour identification from `order_hour`

### 10. Demand forecasting

**Page:** Demand Forecast  
**Backend:** `backend/app/ml/forecasting.py`

Daily order counts are built from parsed dates (optionally filtered to a city / restaurant / cuisine). Requires **at least 14 days**.

Three models compete on a **holdout** window (last few days):

| Model | Role |
|---|---|
| Moving average | Naive baseline |
| Simple exponential smoothing | Weighted recent history (statsmodels) |
| ARIMA(2,1,2) or smaller if short series | Autoregressive integrated moving average |

Winner is chosen by **RMSE**, then refit on the full series for a 7 / 14 / 30-day horizon. Metrics reported: MAE, MSE, RMSE.

### 11. Churn prediction

**Page:** Churn Prediction  
**Backend:** `backend/app/ml/churn.py`

**Label (transparent, not a black box):** a customer is *churned* if recency exceeds a threshold (default **60 days**) vs the observation date (max order date + 1).

**Leakage control:** `recency` is **not** used as a feature (it would trivially predict the label). Features are behavioural: frequency, monetary value, AOV, average delivery time, cancellations, ratings, discount usage.

Three classifiers (75/25 split): **Logistic Regression**, **Decision Tree**, **Random Forest**. Compared on Accuracy, Precision, Recall, F1, ROC-AUC. Best ROC-AUC model scores every customer. Training is refused below ~30 customers or if class balance is too poor.

### 12. Product recommendations (Apriori)

**Page:** Recommendations (association rules)  
**Backend:** `backend/app/ml/apriori.py`

Market-basket analysis: items sharing the same `order_id` form a basket. **Apriori** finds frequent itemsets; association rules keep pairs above support / confidence / lift.

Example: if `{Burger} → {Fries}` has high lift, fries are bought more often with burgers than by chance — useful for combos.

Needs `order_id` + `food_item` and enough **multi-item** orders (default ≥ 50).

### 13. Data-driven recommendation engine

**Backend:** `backend/app/analytics/recommendations_engine.py`  
**Surfaced on:** Recommendations / insights APIs

This is **not** collaborative filtering. It is a **rule engine** over already-computed metrics, for example:

- High-order city with low revenue → raise AOV / restaurant coverage
- High-revenue restaurant with poor ratings (and slow delivery) → quality / ops review
- High-value customers with high churn probability → retention offers
- Peak hour known → extra rider allocation
- Cancellation rate or late-% above thresholds → fulfilment / SLA work

Every item is labelled as a data-driven recommendation and tied to a real number.

### 14. Location analytics

When `latitude` / `longitude` exist, the dashboard shows an order-density map. If only `customer_city` exists, it falls back to a city table. Same graceful-degradation idea as everywhere else.

---

## Concepts used (and where)

| Concept | Where it appears |
|---|---|
| **ETL** (extract, transform, load) | Upload → profile → clean → Parquet cache |
| **Data profiling & quality scoring** | Completeness, duplicates, outliers, invalid types |
| **Schema-on-read / role mapping** | Flexible CSVs without a rigid header contract |
| **Calculated / derived fields** | `total_amount`, date parts, delay, peak hour |
| **Dimensional modelling (star / snowflake)** | `FactOrders` + `Dim*` in `database/schema.sql`; logical grain is still the order line |
| **Measures vs dimensions** | Revenue, orders vs city, cuisine, month |
| **KPIs** | AOV, cancellation rate, late %, ratings |
| **Interactive filtering** | Global filter bar; APIs take a filter body |
| **RFM segmentation** | Quantile scores + CRM-style segments |
| **Time-series forecasting** | Daily demand, holdout, MAE/RMSE, MA / SES / ARIMA |
| **Supervised classification** | Churn models, train/test split, ROC-AUC, confusion matrix |
| **Label leakage avoidance** | Recency excluded from churn features |
| **Association-rule mining** | Support, confidence, lift (Apriori) |
| **Rule-based decisioning** | Thresholds on live metrics → business recs |
| **Graceful degradation** | Unavailable modules explain *why* |
| **Separation of metadata and bulk data** | SQL session rows vs Parquet frames |

---

## Technology stack

| Layer | Tech |
|---|---|
| Frontend | React 18, TypeScript, Tailwind CSS, Apache ECharts, Leaflet, Lucide |
| Backend | FastAPI, Pandas, NumPy, SQLAlchemy |
| ML | scikit-learn, statsmodels, mlxtend (Apriori) |
| Storage | SQLite by default; PostgreSQL via Docker; Parquet caches |
| Containers | Docker Compose (frontend nginx → backend → Postgres) |

---

## How to run

**Windows (local):** keep two processes running — backend on port **8000**, frontend on **5173**.

```powershell
# From foodflow-iq/
.\scripts\start-dev.ps1
```

Or manually:

```powershell
cd backend
.\.venv313\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` to `http://localhost:8000`.

**Docker:**

```bash
docker-compose up --build
```

- UI: http://localhost:3000  
- API health: http://localhost:8000/api/health  
- Interactive OpenAPI: http://localhost:8000/docs  

### Environment

See `.env.example`. Defaults: SQLite (`sqlite:///./foodflow.db`), `STORAGE_DIR=./storage`, CORS for localhost Vite/Docker, `VITE_API_PROXY_TARGET=http://localhost:8000`.

---

## API surface (summary)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/datasets/upload` | Upload and profile CSV |
| POST | `/api/datasets/load-sample` | Load bundled sample |
| GET/DELETE | `/api/datasets`, `/api/datasets/{id}` | List, detail, delete sessions |
| GET | `/api/datasets/{id}/profile` | Data-quality profile |
| POST | `/api/datasets/{id}/clean` | ETL + derived fields |
| GET | `/api/datasets/{id}/filters` | Dynamic filter options |
| POST | `/api/datasets/{id}/dashboard/*` | Overview, sales, customers, restaurants, delivery, time, locations |
| POST | `/api/datasets/{id}/insights` | Combined insights |
| POST | `/api/datasets/{id}/rfm` | RFM table |
| POST | `/api/datasets/{id}/forecast` | Demand forecast |
| POST | `/api/datasets/{id}/churn` | Churn models + scores |
| POST | `/api/datasets/{id}/apriori` | Association rules |
| POST | `/api/datasets/{id}/recommendations` | Data-driven recs |

---

## Testing

```bash
cd backend && pytest -v
cd frontend && npm test
```

Backend tests cover ETL, schema detection, sales/RFM/restaurant analytics, and ML safety (forecast/churn refusal on thin data). Frontend tests cover shared UI states and the API client.

---

## Design principles

1. **Never fabricate missing data.** Missing columns disable or partially disable modules.
2. **Dataset-agnostic.** Analytics consume *roles*, not a fixed spreadsheet.
3. **Transparent ML.** Churn labels and forecast model choice are explained; metrics are shown, not only a chart.
4. **Recommendations from numbers.** Copy always cites a computed threshold or ranking.

#Food flow-iq<br>
-An analysis and prediction application for the restaurants<br>
Thank you for reading :)
