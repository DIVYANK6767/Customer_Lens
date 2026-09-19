# CustomerLens — SQL Analytics Layer

## Overview & Architecture

The SQL analytics layer provides an enterprise-grade relational foundation for querying, segmenting, and analyzing customer transactional data in **CustomerLens**. Built on **PostgreSQL**, this layer ingests cleaned, validated transactions from the Phase 5 pipeline and serves as the single source of truth for business intelligence, cohort metrics, windowed aggregation, and customer feature preparation.

---

## Directory Structure

```text
sql/
├── schema.sql        # DDL definitions: analytics schema and customer_transactions table
├── validation.sql    # Data audit queries and invariant validation scorecard
└── README.md         # Architecture, usage guidelines, and workflow documentation
```

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

### 2. Creating the Schema (`schema.sql`)
You can initialize the schema using `psql`:
```bash
psql -h localhost -U postgres -d customer_lens -f sql/schema.sql
```
Alternatively, the Python ingestion script automatically applies `schema.sql` if the schema is not yet initialized.

### 3. Loading the Data (`src/load_to_postgres.py`)
Execute the automated Python ingestion script:
```bash
python -m src.load_to_postgres
```
**Idempotency Strategy:** The loader executes `TRUNCATE TABLE` followed by streaming `COPY` inside an atomic transaction block. Running the script multiple times will never duplicate rows or create partial data states.

### 4. Validating Invariants (`validation.sql`)
Execute the validation queries and inspection scorecard via `psql`:
```bash
psql -h localhost -U postgres -d customer_lens -f sql/validation.sql
```

Expected validation baselines:
- **Total Rows:** `392,692`
- **Active Customers:** `4,338`
- **Completed Orders:** `18,532`
- **Total Revenue:** `£8,887,208.89`
- **Missing CustomerID:** `0`
- **TransactionType:** `100% Sale`

---

## Why PostgreSQL?

1. **Analytical Query Power:** Native support for window functions (`ROW_NUMBER()`, `RANK()`, `NTILE()`), Common Table Expressions (CTEs), and complex multi-level aggregations required for cohort and Pareto analysis.
2. **Reliability & ACID Compliance:** Enforces data integrity through foreign keys, check constraints, and atomic transactions.
3. **Enterprise Standard:** Reflects realistic corporate data engineering workflows where data warehouses/relational databases serve downstream analytics rather than flat CSV files.
4. **Tool Agnostic Integration:** Directly integrates with BI tools (e.g., Power BI), web applications (e.g., Streamlit), and machine learning pipelines.

---

## Distinction Between Python EDA and SQL Analytics

| Dimension | Python EDA (Phase 6) | SQL Analytics (Phase 7+) |
| :--- | :--- | :--- |
| **Primary Tooling** | Pandas, NumPy, Matplotlib, Seaborn | PostgreSQL, SQL CTEs, Window Functions |
| **Environment** | Interactive Jupyter Notebooks (`03_eda.ipynb`) | Database Engine (`customer_lens`), `psql` |
| **Primary Objective** | Exploratory inspection, distribution visualization, anomaly detection, statistical tests | Relational reporting, KPI metric aggregation, RFM data marts, business query answers |
| **Data Mutability** | Read-only in-memory Pandas DataFrames | Relational tables, views, and persistent analytical marts |
| **Data Scope** | Single dataset exploration | Multi-table joins, relational indexing, and reproducible enterprise queries |
