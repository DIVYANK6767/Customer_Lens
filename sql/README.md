# CustomerLens — SQL Analytics Layer

## Overview & Architecture

The SQL analytics layer provides an enterprise-grade relational foundation for querying, segmenting, and analyzing customer transactional data in **CustomerLens**. Built on **PostgreSQL**, this layer ingests cleaned, validated transactions from the Phase 5 pipeline and serves as the single source of truth for business intelligence, cohort metrics, windowed aggregation, and customer feature preparation.

---

## Directory Structure

```text
sql/
├── schema.sql              # DDL definitions: analytics schema and customer_transactions table
├── validation.sql          # Data audit queries and invariant validation scorecard
├── exploration.sql         # Foundational exploration queries (12 baseline inquiries)
├── customer_metrics.sql    # Customer-level metrics, window rankings, and concentration curves
├── revenue_analysis.sql    # Revenue velocity, MoM growth (LAG), diurnal, and percentiles
├── business_questions.sql  # 20 executive and commercial business questions answered via SQL
└── README.md               # Architecture, catalog, execution guidelines, and documentation
```

---

## SQL Scripts Catalog

### 1. `schema.sql` (Phase 7.1)
- Establishes the `analytics` schema and `analytics.customer_transactions` table.
- Defines robust relational types (`TEXT`, `TIMESTAMP`, `INTEGER`, `NUMERIC(12, 4)`, `NUMERIC(14, 2)`).
- Applies check constraints safeguarding positive quantities, prices, and identified customer records.

### 2. `validation.sql` (Phase 7.1)
- Validates data fidelity immediately following `COPY` ingestion.
- Asserts strict compliance against core dataset invariants (392,692 rows, 4,338 customers, 18,532 orders, £8,887,208.89 revenue).

### 3. `exploration.sql` (Phase 7.2)
- Contains 12 foundational exploratory SQL queries establishing baseline operational metrics.
- Computes overall transaction rows, active customers, orders, revenue, physical units, unique SKUs, geographic footprint, and temporal horizons.
- Provides customer, country, and monthly aggregated summaries.

### 4. `customer_metrics.sql` (Phase 7.2)
- **Section A: Customer Revenue & Lifetime Value:** Lifetime spend, order volume, total units, AOV, first/last purchase timestamps.
- **Section B: Purchase Frequency Distribution:** Order frequency tiers, customer count shares, and revenue generation.
- **Section C: Customer Ranking by Revenue:** Demonstrates `RANK()` and `DENSE_RANK()` window functions.
- **Section D: Customer Revenue Contribution:** Windowed individual percentage share using `SUM() OVER ()`.
- **Section E: Cumulative Revenue Contribution:** Cumulative Lorenz curve using `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
- **Section F: Repeat vs. One-Time Customers:** Granular breakdown of 2,845 repeat buyers (65.58%) vs 1,493 one-time buyers (34.42%).
- **Section G: Customer Inactivity Analysis:** Recency calculation using dynamic anchor `MAX(invoicedate) + INTERVAL '1 day'`.
- **Section H: Top Customers by Revenue:** Top 10, top 20, and top 50 accounts with strict 1-to-1 customer grouping.

### 5. `revenue_analysis.sql` (Phase 7.2)
- **Section A: Monthly Sales Velocity:** 13-month time series tracking orders, active customers, units, gross revenue, and AOV.
- **Section B: Month-over-Month Revenue Growth:** Employs `LAG()` window function to track monthly trajectory, absolute delta, and percentage change.
- **Section C: Country Revenue Breakdown:** Destination market sales distribution, order counts, customer counts, and AOV.
- **Section D: Country Revenue Ranking:** `RANK()` and `DENSE_RANK()` geographic market evaluation.
- **Section E: Daily Revenue Time Series:** High-resolution daily sales trajectory tracking.
- **Section F: Day-of-Week Operational Analysis:** Weekday purchasing rhythms using `EXTRACT(ISODOW ...)` and `TO_CHAR(..., 'FMDay')`.
- **Section G: Hourly Diurnal Rhythms:** Hourly order patterns across the 24-hour cycle.
- **Section H: Order Value Distribution & Percentiles:** Basket monetary spend percentiles using `PERCENTILE_CONT(0.25, 0.50, 0.75, 0.90, 0.95, 0.99)`.

### 6. `business_questions.sql` (Phase 7.2)
- Answers 20 dedicated executive and commercial business questions (Q1 through Q20).
- Employs CTEs, window functions, percentile benchmarks, and cohort breakdowns.
- Solves key commercial problems including Pareto threshold identification (Q11: rank 1,130 accounts generate ~80% of revenue), churn/inactivity detection (Q12), wholesale customer identification (Q17), and revenue decile concentration (Q20).

---

## Database, Schema & Table Structure

| Entity | Identifier | Description |
| :--- | :--- | :--- |
| **Database** | `customer_lens` | Dedicated PostgreSQL database instance. |
| **Schema** | `analytics` | Isolated analytical schema separating presentation/analytical tables from system catalogs. |
| **Table** | `analytics.customer_transactions` | Analytical fact table containing verified customer purchase records. |

### Schema & Column Specifications

```sql
CREATE TABLE analytics.customer_transactions (
    InvoiceNo           TEXT            NOT NULL,
    StockCode           TEXT            NOT NULL,
    Description         TEXT,
    Quantity            INTEGER         NOT NULL,
    InvoiceDate         TIMESTAMP       NOT NULL,
    UnitPrice           NUMERIC(12, 4)  NOT NULL,
    CustomerID          TEXT            NOT NULL,
    Country             TEXT            NOT NULL,
    TransactionType     TEXT            NOT NULL,
    DescriptionMissing  BOOLEAN         NOT NULL DEFAULT FALSE,
    Revenue             NUMERIC(14, 2)  NOT NULL
);
```

### Table Invariants & Constraints
- **Positive Volume:** `Quantity > 0`
- **Positive Pricing:** `UnitPrice > 0`
- **Validated Sales:** `TransactionType = 'Sale'`
- **Non-Negative Spend:** `Revenue >= 0`
- **Identified Customers:** `CustomerID IS NOT NULL`

---

## How to Execute

### 1. Database Configuration
Configure environment variables using a local `.env` file (copied from `.env.example`):
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=customer_lens
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
```

### 2. Loading the Data (`src/load_to_postgres.py`)
Execute the automated Python ingestion script:
```bash
python -m src.load_to_postgres
```

### 3. Running SQL Queries via `psql`
Execute any analytical script against the database:
```bash
psql -h localhost -U postgres -d customer_lens -f sql/exploration.sql
psql -h localhost -U postgres -d customer_lens -f sql/customer_metrics.sql
psql -h localhost -U postgres -d customer_lens -f sql/revenue_analysis.sql
psql -h localhost -U postgres -d customer_lens -f sql/business_questions.sql
```

### 4. Running Automated Analytical Tests
Execute the SQL analytical test suite verifying all 12 analytical invariants:
```bash
python -m pytest tests/test_sql_analytics.py -v
```

---

## Distinction Between Python EDA and SQL Analytics

| Dimension | Python EDA (Phase 6) | SQL Analytics (Phase 7+) |
| :--- | :--- | :--- |
| **Primary Tooling** | Pandas, NumPy, Matplotlib, Seaborn | PostgreSQL, SQL CTEs, Window Functions |
| **Environment** | Interactive Jupyter Notebooks (`03_eda.ipynb`) | Database Engine (`customer_lens`), `psql` |
| **Primary Objective** | Exploratory inspection, distribution visualization, anomaly detection, statistical tests | Relational reporting, KPI metric aggregation, RFM data marts, business query answers |
| **Data Mutability** | Read-only in-memory Pandas DataFrames | Relational tables, views, and persistent analytical marts |
| **Data Scope** | Single dataset exploration | Multi-table joins, relational indexing, and reproducible enterprise queries |
