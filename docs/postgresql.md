# PostgreSQL Analytical Layer Foundation
## CustomerLens — Customer Segmentation & Targeted Marketing Analytics

---

## 1. PostgreSQL Role in CustomerLens

In the CustomerLens architecture, **PostgreSQL** serves as the centralized, persistent **analytical database**. While exploratory data analysis (EDA) and data cleaning were prototyped in Python (Pandas/NumPy), an enterprise analytics platform requires a durable relational data store to:
- Serve as the authoritative single source of truth for validated customer transactions.
- Enable high-performance analytical querying using native SQL constructs (CTEs, window functions, complex aggregations).
- Support automated data validation and data quality audit scorecards.
- Provide a clean, decoupleable integration point for business intelligence dashboards (e.g., Power BI) and interactive web applications (e.g., Streamlit).

> [!IMPORTANT]
> **Separation of Concerns:** PostgreSQL consumes the cleaned, validated analytical dataset (`data/processed/customer_transactions.csv`). The Phase 5 data cleaning pipeline logic is not duplicated in SQL; rather, SQL enforces and verifies the resulting analytical invariants.

---

## 2. Database, Schema & Table Architecture

- **Database Name:** `customer_lens`
- **Schema Name:** `analytics`
- **Table Name:** `analytics.customer_transactions`

By creating an isolated `analytics` schema, the project cleanly separates analytical models, views, and marts from administrative schemas (`public`, `pg_catalog`).

---

## 3. Column Mapping & Schema Specification

The `analytics.customer_transactions` table exactly mirrors the 11-column validated contract established in Phase 5 and analyzed in Phase 6:

| CSV Column | PostgreSQL Type | Nullable? | Invariant Constraints | Description |
| :--- | :--- | :---: | :--- | :--- |
| `InvoiceNo` | `TEXT` | No | `NOT NULL` | 6-digit invoice identifier for completed orders. |
| `StockCode` | `TEXT` | No | `NOT NULL` | Alphanumeric product/catalog identifier. |
| `Description` | `TEXT` | Yes | — | Standardized product description. |
| `Quantity` | `INTEGER` | No | `CHECK (Quantity > 0)` | Physical units transacted; strictly positive in sales. |
| `InvoiceDate` | `TIMESTAMP` | No | `NOT NULL` | Transaction timestamp (`YYYY-MM-DD HH:MM:SS`). |
| `UnitPrice` | `NUMERIC(12, 4)` | No | `CHECK (UnitPrice > 0)` | Unit price in British Pound Sterling (£ / GBP). |
| `CustomerID` | `TEXT` | No | `CHECK (length(trim(CustomerID)) > 0)` | 5-digit identified customer account string. |
| `Country` | `TEXT` | No | `NOT NULL` | Destination / billing country. |
| `TransactionType`| `TEXT` | No | `CHECK (TransactionType = 'Sale')` | Operational type; strictly `'Sale'` in this table. |
| `DescriptionMissing` | `BOOLEAN` | No | `DEFAULT FALSE` | Flag indicating if description was missing in raw logs. |
| `Revenue` | `NUMERIC(14, 2)` | No | `CHECK (Revenue >= 0)` | Gross monetary spend (`Quantity × UnitPrice`). |

---

## 4. Local Environment Setup

### Prerequisites
- **PostgreSQL Version:** 18.6 (or 14+)
- **Windows Service:** `postgresql-x64-18` (or local PostgreSQL daemon)
- **Port:** `5432` (default)
- **Database Client:** `psql` command-line utility available in system `PATH`
- **Python Driver:** `psycopg[binary]>=3.1.0` (installed via `requirements.txt`)

### Service Verification
To check that the PostgreSQL service is running on Windows:
```powershell
Get-Service -Name postgresql-x64-18
```

---

## 5. Environment Variables & Configuration

CustomerLens uses environment variables for database configuration to ensure portability across development, staging, and CI environments.

### Supported Environment Variables
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `POSTGRES_HOST` (or `DB_HOST`) | `localhost` | Hostname or IP address of the PostgreSQL server. |
| `POSTGRES_PORT` (or `DB_PORT`) | `5432` | TCP port on which PostgreSQL listens. |
| `POSTGRES_DB` (or `DB_NAME`) | `customer_lens` | Target database name. |
| `POSTGRES_USER` (or `DB_USER`) | `postgres` | Database user account. |
| `POSTGRES_PASSWORD` (or `DB_PASSWORD`) | `""` | User password (never committed to version control). |

### Template Configuration (`.env.example`)
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=customer_lens
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
```

To configure local credentials:
1. Copy `.env.example` to `.env`.
2. Add your local PostgreSQL password to `.env`.
3. `.env` is automatically ignored by `.gitignore` and must never be committed.

---

## 6. How to Initialize the Schema

The schema definition script is located at [`sql/schema.sql`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/sql/schema.sql).

### Using `psql`:
```bash
psql -h localhost -U postgres -d customer_lens -f sql/schema.sql
```

### Using Python:
The ingestion script [`src/load_to_postgres.py`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/src/load_to_postgres.py) automatically checks for and applies `sql/schema.sql` if the table does not exist.

---

## 7. How to Ingest Data

Data ingestion is orchestrated by [`src/load_to_postgres.py`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/src/load_to_postgres.py).

### Execution:
```bash
python -m src.load_to_postgres
```

### Ingestion & Idempotency Strategy:
- **Streaming Bulk Copy:** Uses the native PostgreSQL `COPY ... FROM STDIN (FORMAT csv)` protocol via `psycopg`, streaming the 392,692 rows in chunks without loading the entire dataset into unmanaged memory.
- **Atomic Idempotency:** Inside a single database transaction (`with conn.transaction():`), the script executes:
  1. `TRUNCATE TABLE analytics.customer_transactions;`
  2. Streaming `COPY` from `data/processed/customer_transactions.csv`.
  3. Immediate count verification (`SELECT COUNT(*)`).
- If any network, disk, or constraint error occurs, PostgreSQL automatically rolls back the transaction, preserving database integrity with zero partial or duplicate rows.

---

## 8. How to Validate Data Invariants

Validation queries are maintained in [`sql/validation.sql`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/sql/validation.sql).

### Execution:
```bash
psql -h localhost -U postgres -d customer_lens -f sql/validation.sql
```

### Verified Baseline Scorecard:
The validation suite programmatically verifies the following known empirical invariants:
1. **Row Count:** Exactly `392,692` rows.
2. **Column Availability:** All 11 expected fields present with correct data types.
3. **Missing CustomerID:** `0` rows with null or whitespace-only customer ID.
4. **Missing or Negative Revenue:** `0` rows.
5. **Quantity Constraints:** `0` rows with $\text{Quantity} \le 0$.
6. **UnitPrice Constraints:** `0` rows with $\text{UnitPrice} \le 0$.
7. **TransactionType Distribution:** Exactly `100.0%` `'Sale'` transactions.
8. **Active Customer Count:** Exactly `4,338` unique identified accounts.
9. **Completed Orders:** Exactly `18,532` distinct invoices.
10. **Revenue Reconciliation:** Sum of `Revenue` matches gross spend of **£8,887,208.89**.
11. **Date Range:** Earliest transaction `2010-12-01 08:26:00` to latest `2011-12-09 12:50:00`.
12. **Country Breadth:** Exactly `37` distinct destination countries.

---

## 9. Security Principles & Credential Protection

1. **Zero Secret Leakage:**
   - Plaintext passwords are never committed to repository files, documentation, or test fixtures.
   - `.env` is permanently excluded via `.gitignore`.
2. **Error Message Sanitization:**
   - [`src/database.py`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/src/database.py) includes `get_masked_config()` to mask credentials (`"password": "********"`).
   - If a connection error occurs, custom exception handling intercepts the `psycopg.Error` and raises a clean `ConnectionError` displaying host, port, database, and user while redacting passwords.
3. **Least Privilege:**
   - Database operations require only standard DDL and DML privileges (`CREATE SCHEMA`, `CREATE TABLE`, `SELECT`, `INSERT`, `TRUNCATE`) on the `customer_lens` database.

---

## 10. How This Layer Supports Future Analytical Phases

The PostgreSQL analytical layer established in Phase 7.1 enables upcoming analytical workflows without requiring heavy in-memory Python scripts:

1. **Analytical SQL Queries (Phase 7.2+):**
   - Customer recency, frequency, and monetary aggregations directly calculated via SQL.
   - Window functions (`NTILE()`, `ROW_NUMBER()`, `DENSE_RANK()`) for RFM quantile scoring.
   - Monthly revenue run-rates, cohort retention matrices, and country-level breakdowns.
2. **Dashboard Direct Querying (Phase 9+):**
   - Connects directly to **Power BI** via PostgreSQL ODBC/DirectQuery connector.
   - Serves **Streamlit** multi-page interactive dashboards with sub-second parameter queries.
3. **Feature Store for Machine Learning:**
   - Extracts transformed customer vectors directly into Scikit-learn pipelines for K-Means clustering.
