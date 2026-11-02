-- FoodFlow IQ — Reference Dimensional Model (Star / Snowflake Schema)
--
-- This schema documents the BI dimensional-modelling concept the platform is
-- built around (Section 9 / 35 of the spec). The live application stores
-- dataset session metadata in `datasets` (see backend/app/models/db.py) and
-- caches the actual working dataframe as Parquet for performance — but this
-- file shows how the same data maps onto a classic star schema if you want
-- to load processed exports into a physical warehouse for BI tools
-- (Power BI, Tableau, Metabase, etc.).
--
-- FactOrders is the central fact table; Dim* tables are shared dimensions.
-- DimLocation is snowflaked out of DimCustomer (city -> area) to show the
-- snowflake variant without over-normalizing the rest of the model.

CREATE TABLE IF NOT EXISTS datasets (
    id              VARCHAR PRIMARY KEY,
    name            VARCHAR NOT NULL,
    uploaded_at     TIMESTAMP DEFAULT now(),
    rows            INTEGER,
    columns         INTEGER,
    status          VARCHAR DEFAULT 'uploaded',
    raw_path        TEXT,
    clean_path      TEXT,
    schema_json     TEXT,
    profile_json    TEXT,
    is_sample       BOOLEAN DEFAULT FALSE,
    error_message   TEXT
);

-- ============ DIMENSIONS ============

CREATE TABLE IF NOT EXISTS dim_date (
    date_id         SERIAL PRIMARY KEY,
    full_date       DATE UNIQUE NOT NULL,
    year            SMALLINT,
    month           SMALLINT,
    month_name      VARCHAR(10),
    day             SMALLINT,
    day_of_week     VARCHAR(10),
    is_weekend      BOOLEAN,
    is_peak_hour    BOOLEAN
);

CREATE TABLE IF NOT EXISTS dim_location (
    location_id     SERIAL PRIMARY KEY,
    city            VARCHAR NOT NULL,
    area            VARCHAR,
    UNIQUE(city, area)
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id             VARCHAR PRIMARY KEY,
    age                     SMALLINT,
    gender                  VARCHAR(20),
    customer_type           VARCHAR(20),
    location_id             INTEGER REFERENCES dim_location(location_id),
    first_order_date        DATE,
    rfm_segment             VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS dim_restaurant (
    restaurant_id           VARCHAR PRIMARY KEY,
    restaurant_name         VARCHAR NOT NULL,
    cuisine                 VARCHAR(50),
    location_id             INTEGER REFERENCES dim_location(location_id)
);

CREATE TABLE IF NOT EXISTS dim_food (
    food_id                 SERIAL PRIMARY KEY,
    food_item               VARCHAR NOT NULL,
    food_category           VARCHAR(50),
    UNIQUE(food_item, food_category)
);

CREATE TABLE IF NOT EXISTS dim_delivery_partner (
    delivery_partner_id     VARCHAR PRIMARY KEY,
    experience_level        VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS dim_payment (
    payment_id              SERIAL PRIMARY KEY,
    payment_method          VARCHAR(30) UNIQUE NOT NULL
);

-- ============ FACT TABLE ============

CREATE TABLE IF NOT EXISTS fact_orders (
    order_line_id           BIGSERIAL PRIMARY KEY,
    order_id                VARCHAR NOT NULL,
    customer_id             VARCHAR REFERENCES dim_customer(customer_id),
    restaurant_id           VARCHAR REFERENCES dim_restaurant(restaurant_id),
    food_id                 INTEGER REFERENCES dim_food(food_id),
    date_id                 INTEGER REFERENCES dim_date(date_id),
    delivery_partner_id     VARCHAR REFERENCES dim_delivery_partner(delivery_partner_id),
    location_id             INTEGER REFERENCES dim_location(location_id),
    payment_id              INTEGER REFERENCES dim_payment(payment_id),

    order_status            VARCHAR(20),
    quantity                NUMERIC,
    unit_price              NUMERIC(10,2),
    revenue                 NUMERIC(12,2),   -- subtotal
    discount                NUMERIC(10,2),
    delivery_fee            NUMERIC(10,2),
    total_amount            NUMERIC(12,2),
    profit                  NUMERIC(12,2),

    distance_km             NUMERIC(6,2),
    estimated_delivery_time NUMERIC(6,1),
    actual_delivery_time    NUMERIC(6,1),
    delivery_delay          NUMERIC(6,1),

    customer_rating         NUMERIC(2,1),
    delivery_rating         NUMERIC(2,1)
);

CREATE INDEX IF NOT EXISTS idx_fact_orders_date ON fact_orders(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_orders_customer ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_orders_restaurant ON fact_orders(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_fact_orders_order_id ON fact_orders(order_id);
