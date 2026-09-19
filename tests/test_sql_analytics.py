"""Tests for the CustomerLens SQL Analytical Layer.

Verifies the integrity, structural completeness, and numerical correctness
of SQL queries and analytical aggregations in PostgreSQL.
"""

from __future__ import annotations

import decimal
from pathlib import Path
import pytest

from src.database import (
    get_connection,
    get_project_root,
    test_connection as check_db_connection,
)

# Baseline empirical invariants from validated dataset
EXPECTED_CUSTOMERS = 4338
EXPECTED_ORDERS = 18532
EXPECTED_REVENUE = decimal.Decimal("8887208.89")
EXPECTED_ONE_TIME_CUSTOMERS = 1493
EXPECTED_REPEAT_CUSTOMERS = 2845
EXPECTED_ONE_TIME_ORDERS = 1493
EXPECTED_REPEAT_ORDERS = 17039


# Helper fixture to determine if PostgreSQL is available
@pytest.fixture(scope="module")
def db_conn():
    """Yield a live database connection if available, otherwise skip."""
    if not check_db_connection():
        pytest.skip("PostgreSQL database is not reachable. Skipping live SQL analytics tests.")
    with get_connection() as conn:
        yield conn


# -----------------------------------------------------------------------------
# 1. SQL File Integrity & Presence Tests
# -----------------------------------------------------------------------------

def test_sql_files_exist():
    """Verify that all required Phase 7.2 SQL files and documentation exist."""
    root = get_project_root()
    sql_dir = root / "sql"
    assert sql_dir.is_dir(), "sql/ directory is missing"
    
    expected_files = [
        "exploration.sql",
        "customer_metrics.sql",
        "revenue_analysis.sql",
        "business_questions.sql",
        "README.md",
    ]
    for filename in expected_files:
        filepath = sql_dir / filename
        assert filepath.is_file(), f"Missing required SQL file: {filename}"
        assert filepath.stat().st_size > 0, f"File {filename} is empty"


def test_sql_files_contain_advanced_techniques():
    """Verify that SQL files contain required analytical techniques (CTEs, Window Functions)."""
    root = get_project_root()
    sql_dir = root / "sql"
    
    # customer_metrics.sql must use window functions and CTEs
    cust_sql = (sql_dir / "customer_metrics.sql").read_text(encoding="utf-8").upper()
    assert "WITH" in cust_sql
    assert "OVER" in cust_sql
    assert "RANK()" in cust_sql or "DENSE_RANK()" in cust_sql or "ROW_NUMBER()" in cust_sql
    assert "SUM(" in cust_sql
    
    # revenue_analysis.sql must use LAG, PERCENTILE_CONT, and DATE_TRUNC
    rev_sql = (sql_dir / "revenue_analysis.sql").read_text(encoding="utf-8").upper()
    assert "LAG(" in rev_sql
    assert "PERCENTILE_CONT" in rev_sql
    assert "DATE_TRUNC" in rev_sql
    
    # business_questions.sql must answer Q1 to Q20
    biz_sql = (sql_dir / "business_questions.sql").read_text(encoding="utf-8")
    for i in range(1, 21):
        assert f"Q{i}." in biz_sql, f"Missing Q{i} in business_questions.sql"


# -----------------------------------------------------------------------------
# 2. Live Database Validation Tests (12 Required Invariants)
# -----------------------------------------------------------------------------

def test_01_customer_count_matches_validated_baseline(db_conn):
    """Test 1: Customer count matches validated value of 4,338."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(DISTINCT customerid) FROM analytics.customer_transactions;")
        count = cur.fetchone()[0]
        assert count == EXPECTED_CUSTOMERS, f"Expected {EXPECTED_CUSTOMERS} customers, got {count}"


def test_02_order_count_matches_validated_baseline(db_conn):
    """Test 2: Order count matches validated value of 18,532."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT COUNT(DISTINCT invoiceno) FROM analytics.customer_transactions;")
        count = cur.fetchone()[0]
        assert count == EXPECTED_ORDERS, f"Expected {EXPECTED_ORDERS} orders, got {count}"


def test_03_revenue_matches_validated_baseline(db_conn):
    """Test 3: Revenue matches validated value of £8,887,208.89."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT ROUND(SUM(revenue), 2) FROM analytics.customer_transactions;")
        revenue = cur.fetchone()[0]
        assert revenue == EXPECTED_REVENUE, f"Expected revenue £{EXPECTED_REVENUE}, got £{revenue}"


def test_04_customer_revenue_aggregation_equals_total_revenue(db_conn):
    """Test 4: Customer-level revenue aggregation equals total table revenue."""
    with db_conn.cursor() as cur:
        query = """
            WITH customer_totals AS (
                SELECT customerid, SUM(revenue) AS customer_revenue
                FROM analytics.customer_transactions
                GROUP BY customerid
            )
            SELECT 
                ROUND(SUM(customer_revenue), 2) AS aggregated_customer_revenue,
                (SELECT ROUND(SUM(revenue), 2) FROM analytics.customer_transactions) AS table_revenue
            FROM customer_totals;
        """
        cur.execute(query)
        agg_rev, table_rev = cur.fetchone()
        assert agg_rev == table_rev == EXPECTED_REVENUE


def test_05_repeat_plus_onetime_customers_equals_total_active_customers(db_conn):
    """Test 5: Repeat + one-time customers equals total active customers (1,493 + 2,845 = 4,338)."""
    with db_conn.cursor() as cur:
        query = """
            WITH customer_orders AS (
                SELECT customerid, COUNT(DISTINCT invoiceno) AS order_count
                FROM analytics.customer_transactions
                GROUP BY customerid
            )
            SELECT 
                COUNT(CASE WHEN order_count = 1 THEN 1 END) AS one_time_customers,
                COUNT(CASE WHEN order_count > 1 THEN 1 END) AS repeat_customers,
                COUNT(*) AS total_customers
            FROM customer_orders;
        """
        cur.execute(query)
        one_time, repeat, total = cur.fetchone()
        assert one_time == EXPECTED_ONE_TIME_CUSTOMERS
        assert repeat == EXPECTED_REPEAT_CUSTOMERS
        assert one_time + repeat == total == EXPECTED_CUSTOMERS


def test_06_revenue_percentages_sum_to_100(db_conn):
    """Test 6: Revenue percentages across cohorts and categories sum to ~100%."""
    with db_conn.cursor() as cur:
        query = """
            WITH customer_orders AS (
                SELECT customerid, COUNT(DISTINCT invoiceno) AS order_count, SUM(revenue) AS customer_revenue
                FROM analytics.customer_transactions
                GROUP BY customerid
            )
            SELECT 
                ROUND(
                    SUM(CASE WHEN order_count = 1 THEN customer_revenue ELSE 0 END) * 100.0 / 
                    NULLIF(SUM(customer_revenue), 0),
                    2
                ) AS one_time_pct,
                ROUND(
                    SUM(CASE WHEN order_count > 1 THEN customer_revenue ELSE 0 END) * 100.0 / 
                    NULLIF(SUM(customer_revenue), 0),
                    2
                ) AS repeat_pct
            FROM customer_orders;
        """
        cur.execute(query)
        one_time_pct, repeat_pct = cur.fetchone()
        assert abs((one_time_pct + repeat_pct) - decimal.Decimal("100.00")) <= decimal.Decimal("0.01")


def test_07_country_revenue_aggregation_equals_total_revenue(db_conn):
    """Test 7: Country revenue aggregation equals total revenue."""
    with db_conn.cursor() as cur:
        query = """
            WITH country_totals AS (
                SELECT country, SUM(revenue) AS country_revenue
                FROM analytics.customer_transactions
                GROUP BY country
            )
            SELECT 
                ROUND(SUM(country_revenue), 2) AS aggregated_country_revenue,
                COUNT(*) AS country_count
            FROM country_totals;
        """
        cur.execute(query)
        agg_country_rev, country_count = cur.fetchone()
        assert agg_country_rev == EXPECTED_REVENUE
        assert country_count == 37


def test_08_monthly_revenue_aggregation_equals_total_revenue(db_conn):
    """Test 8: Monthly revenue aggregation equals total revenue."""
    with db_conn.cursor() as cur:
        query = """
            WITH monthly_totals AS (
                SELECT DATE_TRUNC('month', invoicedate) AS m, SUM(revenue) AS monthly_revenue
                FROM analytics.customer_transactions
                GROUP BY DATE_TRUNC('month', invoicedate)
            )
            SELECT 
                ROUND(SUM(monthly_revenue), 2) AS aggregated_monthly_revenue,
                COUNT(*) AS month_count
            FROM monthly_totals;
        """
        cur.execute(query)
        agg_monthly_rev, month_count = cur.fetchone()
        assert agg_monthly_rev == EXPECTED_REVENUE
        assert month_count == 13  # Dec 2010 through Dec 2011


def test_09_customer_ranking_integrity(db_conn):
    """Test 9: Customer ranking contains no invalid gaps or ordering anomalies."""
    with db_conn.cursor() as cur:
        query = """
            WITH customer_spend AS (
                SELECT customerid, SUM(revenue) AS total_revenue
                FROM analytics.customer_transactions
                GROUP BY customerid
            ),
            ranked_customers AS (
                SELECT 
                    customerid,
                    total_revenue,
                    ROW_NUMBER() OVER (ORDER BY total_revenue DESC) AS row_num,
                    RANK() OVER (ORDER BY total_revenue DESC) AS rank_pos
                FROM customer_spend
            )
            SELECT 
                MIN(row_num) AS min_row,
                MAX(row_num) AS max_row,
                COUNT(DISTINCT row_num) AS distinct_ranks,
                MIN(rank_pos) AS min_rank
            FROM ranked_customers;
        """
        cur.execute(query)
        min_row, max_row, distinct_ranks, min_rank = cur.fetchone()
        assert min_row == 1
        assert max_row == EXPECTED_CUSTOMERS
        assert distinct_ranks == EXPECTED_CUSTOMERS
        assert min_rank == 1


def test_10_customer_level_revenue_contains_one_row_per_customer(db_conn):
    """Test 10: Customer-level revenue aggregation contains exactly one row per customer."""
    with db_conn.cursor() as cur:
        query = """
            WITH customer_summary AS (
                SELECT customerid, COUNT(DISTINCT invoiceno) AS orders, SUM(revenue) AS rev
                FROM analytics.customer_transactions
                GROUP BY customerid
            )
            SELECT 
                COUNT(*) AS total_rows,
                COUNT(DISTINCT customerid) AS distinct_customers
            FROM customer_summary;
        """
        cur.execute(query)
        total_rows, distinct_custs = cur.fetchone()
        assert total_rows == EXPECTED_CUSTOMERS
        assert distinct_custs == EXPECTED_CUSTOMERS


def test_11_order_level_aggregation_contains_one_row_per_invoice(db_conn):
    """Test 11: Order-level aggregation contains exactly one row per invoice."""
    with db_conn.cursor() as cur:
        query = """
            WITH order_summary AS (
                SELECT invoiceno, customerid, SUM(revenue) AS order_rev
                FROM analytics.customer_transactions
                GROUP BY invoiceno, customerid
            )
            SELECT 
                COUNT(*) AS total_orders,
                COUNT(DISTINCT invoiceno) AS distinct_invoices
            FROM order_summary;
        """
        cur.execute(query)
        total_orders, distinct_invoices = cur.fetchone()
        assert total_orders == EXPECTED_ORDERS
        assert distinct_invoices == EXPECTED_ORDERS


def test_12_no_null_customer_ids_in_customer_metrics(db_conn):
    """Test 12: No NULL customer IDs appear in customer-level metrics."""
    with db_conn.cursor() as cur:
        query = """
            SELECT 
                COUNT(*) AS null_customer_rows
            FROM analytics.customer_transactions
            WHERE customerid IS NULL;
        """
        cur.execute(query)
        null_rows = cur.fetchone()[0]
        assert null_rows == 0, f"Found {null_rows} rows with NULL customerid"
