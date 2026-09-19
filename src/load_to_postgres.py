"""Data ingestion module to load cleaned customer transactions into PostgreSQL.

Loads data/processed/customer_transactions.csv into the analytics.customer_transactions
table using an atomic truncate-and-copy strategy to guarantee idempotency.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import psycopg
from psycopg import sql

from src.database import get_connection, get_database_config, get_masked_config, get_project_root

# Configure module logger
logger = logging.getLogger(__name__)

# Expected CSV Column Order & Mapping
EXPECTED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
    "TransactionType",
    "DescriptionMissing",
    "Revenue",
]

EXPECTED_ROW_COUNT = 392692


def ensure_schema_exists(conn: psycopg.Connection, schema_file: Optional[Path] = None) -> None:
    """Ensure that the analytics schema and customer_transactions table exist.

    Args:
        conn: Active psycopg connection.
        schema_file: Optional path to schema.sql. Defaults to sql/schema.sql.
    """
    project_root = get_project_root()
    if schema_file is None:
        schema_file = project_root / "sql" / "schema.sql"

    if not schema_file.is_file():
        raise FileNotFoundError(f"Schema definition file not found at: {schema_file}")

    schema_sql = schema_file.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()


def load_customer_transactions(
    csv_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
    ensure_schema: bool = True,
) -> Dict[str, Any]:
    """Atomically load customer transactions CSV into analytics.customer_transactions.

    Idempotency Strategy:
        Executes TRUNCATE TABLE followed by streaming COPY FROM STDIN within a single
        database transaction. If any error occurs, PostgreSQL rolls back completely,
        preventing duplicate, partial, or corrupted data.

    Args:
        csv_path: Optional path to customer_transactions.csv.
        config: Optional connection configuration dictionary.
        ensure_schema: If True, creates the analytics schema and table if missing.

    Returns:
        Dict with execution summary (rows_loaded, duration_seconds, table_name).

    Raises:
        FileNotFoundError: If the source CSV does not exist.
        ValueError: If CSV headers do not match expected analytical schema.
        ConnectionError: If database connection fails.
    """
    project_root = get_project_root()
    if csv_path is None:
        csv_path = project_root / "data" / "processed" / "customer_transactions.csv"

    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed customer transactions CSV not found at: {csv_path}")

    # Verify CSV headers match analytical contract before touching the database
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        header_line = f.readline().strip()
        csv_headers = [col.strip() for col in header_line.split(",")]

    if csv_headers != EXPECTED_COLUMNS:
        raise ValueError(
            f"CSV header mismatch in '{csv_path.name}'.\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Found:    {csv_headers}"
        )

    db_config = config or get_database_config()
    masked_config = get_masked_config(db_config)
    logger.info(
        "Connecting to PostgreSQL database '%s' at %s:%s to load transactions...",
        masked_config["dbname"],
        masked_config["host"],
        masked_config["port"],
    )

    start_time = time.time()

    with get_connection(db_config) as conn:
        if ensure_schema:
            ensure_schema_exists(conn)

        # Atomic transaction: TRUNCATE + COPY
        with conn.transaction():
            with conn.cursor() as cur:
                # 1. Truncate existing rows for complete idempotency
                cur.execute("TRUNCATE TABLE analytics.customer_transactions;")

                # 2. Fast streaming bulk copy using PostgreSQL native COPY protocol
                copy_query = sql.SQL(
                    "COPY analytics.customer_transactions ({fields}) "
                    "FROM STDIN WITH (FORMAT csv, HEADER true, ENCODING 'utf-8')"
                ).format(
                    fields=sql.SQL(", ").join(sql.Identifier(col.lower()) for col in EXPECTED_COLUMNS)
                )

                with open(csv_path, "r", encoding="utf-8", errors="replace") as csv_file:
                    with cur.copy(copy_query) as copy:
                        while chunk := csv_file.read(65536):
                            copy.write(chunk)

                # 3. Verify row count inside the transaction
                cur.execute("SELECT COUNT(*) FROM analytics.customer_transactions;")
                loaded_count = cur.fetchone()[0]

    duration = time.time() - start_time
    logger.info(
        "Successfully loaded %s rows into analytics.customer_transactions in %.2f seconds.",
        f"{loaded_count:,}",
        duration,
    )

    return {
        "status": "success",
        "table": "analytics.customer_transactions",
        "rows_loaded": loaded_count,
        "expected_rows": EXPECTED_ROW_COUNT,
        "duration_seconds": round(duration, 3),
        "source_csv": str(csv_path.relative_to(project_root)),
    }


def main() -> None:
    """CLI entrypoint to execute data ingestion."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        result = load_customer_transactions()
        print("\n==================================================")
        print("CustomerLens PostgreSQL Ingestion Complete")
        print("==================================================")
        print(f"Destination Table: {result['table']}")
        print(f"Source CSV:        {result['source_csv']}")
        print(f"Rows Loaded:       {result['rows_loaded']:,} (Expected: {result['expected_rows']:,})")
        print(f"Duration:          {result['duration_seconds']} seconds")
        print("Status:            SUCCESS (Idempotent Load Verified)")
        print("==================================================\n")
    except Exception as err:
        logger.error("Failed to load customer transactions into PostgreSQL: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
