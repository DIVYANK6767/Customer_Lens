"""Unit tests for the PostgreSQL database connection and loading modules.

Tests verify environment configuration parsing, credential masking, error handling,
schema and validation SQL files, and CSV path resolution without requiring a live
PostgreSQL server. Opt-in live integration tests are guarded by RUN_POSTGRES_TESTS=1.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg
import pytest

from src.database import (
    get_connection,
    get_database_config,
    get_masked_config,
    get_project_root,
    load_env_file,
    test_connection as check_db_connection,
)
from src.load_to_postgres import (
    EXPECTED_COLUMNS,
    EXPECTED_ROW_COUNT,
    ensure_schema_exists,
    load_customer_transactions,
)


# ---------------------------------------------------------------------------
# 1. Project Root & Path Resolution Tests
# ---------------------------------------------------------------------------

def test_get_project_root():
    """Verify that get_project_root() resolves to CustomerLens directory."""
    root = get_project_root()
    assert root.is_dir()
    assert (root / "src").is_dir()
    assert (root / "sql").is_dir()
    assert (root / "data").is_dir()


def test_csv_source_path_resolution():
    """Verify that customer_transactions.csv exists at the project-relative path."""
    root = get_project_root()
    csv_path = root / "data" / "processed" / "customer_transactions.csv"
    assert csv_path.is_file(), f"Expected CSV file not found at: {csv_path}"


# ---------------------------------------------------------------------------
# 2. Configuration & Credential Masking Tests
# ---------------------------------------------------------------------------

def test_get_database_config_defaults(monkeypatch, tmp_path):
    """Verify default database settings when no environment variables are set."""
    # Clear any active database env vars
    for var in [
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD",
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"
    ]:
        monkeypatch.delenv(var, raising=False)

    # Use empty env path so developer local .env is not loaded
    config = get_database_config(env_path=tmp_path / "empty.env")
    assert config["host"] == "localhost"
    assert config["port"] == 5432
    assert config["dbname"] == "customer_lens"
    assert config["user"] == "postgres"
    assert config["password"] == ""


def test_get_database_config_env_vars(monkeypatch, tmp_path):
    """Verify that POSTGRES_* environment variables are correctly parsed."""
    monkeypatch.setenv("POSTGRES_HOST", "analytics-host")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_USER", "analyst_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "super_secret_123")

    config = get_database_config(env_path=tmp_path / "empty.env")
    assert config["host"] == "analytics-host"
    assert config["port"] == 5433
    assert config["dbname"] == "test_db"
    assert config["user"] == "analyst_user"
    assert config["password"] == "super_secret_123"


def test_get_database_config_fallback_db_vars(monkeypatch, tmp_path):
    """Verify fallback to DB_* environment variables if POSTGRES_* are unset."""
    for var in ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]:
        monkeypatch.delenv(var, raising=False)

    monkeypatch.setenv("DB_HOST", "fallback-host")
    monkeypatch.setenv("DB_PORT", "5439")
    monkeypatch.setenv("DB_NAME", "fallback_db")
    monkeypatch.setenv("DB_USER", "fallback_user")
    monkeypatch.setenv("DB_PASSWORD", "fallback_secret")

    config = get_database_config(env_path=tmp_path / "empty.env")
    assert config["host"] == "fallback-host"
    assert config["port"] == 5439
    assert config["dbname"] == "fallback_db"
    assert config["user"] == "fallback_user"
    assert config["password"] == "fallback_secret"


def test_get_database_config_invalid_port(monkeypatch):
    """Verify ValueError is raised when port cannot be parsed as an integer."""
    monkeypatch.setenv("POSTGRES_PORT", "invalid_port")
    with pytest.raises(ValueError, match="Invalid POSTGRES_PORT value"):
        get_database_config()


def test_get_masked_config():
    """Verify that get_masked_config hides credentials while preserving other parameters."""
    cfg = {
        "host": "localhost",
        "port": 5432,
        "dbname": "customer_lens",
        "user": "postgres",
        "password": "secret_password_value",
    }
    masked = get_masked_config(cfg)
    assert masked["password"] == "********"
    assert masked["host"] == "localhost"
    assert masked["user"] == "postgres"
    assert masked["dbname"] == "customer_lens"
    assert cfg["password"] == "secret_password_value"  # Original unchanged


# ---------------------------------------------------------------------------
# 3. Connection Error Handling & Password Security
# ---------------------------------------------------------------------------

def test_get_connection_masks_password_on_failure():
    """Verify that connection failure exceptions do NOT reveal plaintext passwords."""
    sensitive_pw = "ultra_sensitive_secret_password_123"
    cfg = {
        "host": "invalid-host-9999",
        "port": 5432,
        "dbname": "test_db",
        "user": "test_user",
        "password": sensitive_pw,
    }

    with pytest.raises(ConnectionError) as exc_info:
        get_connection(cfg)

    error_msg = str(exc_info.value)
    assert sensitive_pw not in error_msg
    assert "invalid-host-9999" in error_msg
    assert "test_db" in error_msg


def test_test_connection_returns_false_on_failure():
    """Verify test_connection returns False safely when database is unreachable."""
    cfg = {
        "host": "non-existent-host-99999",
        "port": 5432,
        "dbname": "fake_db",
        "user": "fake_user",
        "password": "fake_password",
    }
    assert check_db_connection(cfg) is False


# ---------------------------------------------------------------------------
# 4. Schema & Validation SQL Structure Tests
# ---------------------------------------------------------------------------

def test_schema_sql_contents():
    """Verify that sql/schema.sql exists and specifies required DDL objects."""
    root = get_project_root()
    schema_path = root / "sql" / "schema.sql"
    assert schema_path.is_file()

    sql_text = schema_path.read_text(encoding="utf-8")
    assert "CREATE SCHEMA IF NOT EXISTS analytics;" in sql_text
    assert "CREATE TABLE analytics.customer_transactions" in sql_text
    for col in EXPECTED_COLUMNS:
        assert col in sql_text, f"Column '{col}' missing from schema.sql"

    # Verify key constraints are present in DDL
    assert "chk_customer_transactions_quantity" in sql_text
    assert "chk_customer_transactions_unitprice" in sql_text
    assert "chk_customer_transactions_transaction_type" in sql_text
    assert "chk_customer_transactions_revenue" in sql_text


def test_validation_sql_contents():
    """Verify that sql/validation.sql exists and covers all required checks."""
    root = get_project_root()
    validation_path = root / "sql" / "validation.sql"
    assert validation_path.is_file()

    sql_text = validation_path.read_text(encoding="utf-8")
    assert "Row Count" in sql_text
    assert "392692" in sql_text
    assert "Distinct Customers" in sql_text
    assert "4338" in sql_text
    assert "Distinct Orders" in sql_text
    assert "18532" in sql_text
    assert "8887208.89" in sql_text


# ---------------------------------------------------------------------------
# 5. Data Ingestion Contract & Idempotency Safeguards
# ---------------------------------------------------------------------------

def test_expected_analytical_columns_match_csv():
    """Verify EXPECTED_COLUMNS matches the actual header of customer_transactions.csv."""
    root = get_project_root()
    csv_path = root / "data" / "processed" / "customer_transactions.csv"

    with open(csv_path, "r", encoding="utf-8") as f:
        header_cols = [c.strip() for c in f.readline().strip().split(",")]

    assert header_cols == EXPECTED_COLUMNS
    assert len(EXPECTED_COLUMNS) == 11
    assert EXPECTED_ROW_COUNT == 392692


def test_load_customer_transactions_missing_csv(tmp_path):
    """Verify load_customer_transactions raises FileNotFoundError for missing CSV."""
    fake_csv = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError, match="not found"):
        load_customer_transactions(csv_path=fake_csv)


def test_load_customer_transactions_invalid_header(tmp_path):
    """Verify load_customer_transactions rejects CSVs with corrupted/mismatched headers."""
    bad_csv = tmp_path / "bad_headers.csv"
    bad_csv.write_text("InvoiceNo,StockCode,WrongColumn\n1,2,3\n", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV header mismatch"):
        load_customer_transactions(csv_path=bad_csv)


def test_ensure_schema_exists_missing_file(tmp_path):
    """Verify ensure_schema_exists raises FileNotFoundError if schema.sql is missing."""
    fake_schema = tmp_path / "missing_schema.sql"
    mock_conn = MagicMock()
    with pytest.raises(FileNotFoundError, match="Schema definition file not found"):
        ensure_schema_exists(mock_conn, schema_file=fake_schema)


# ---------------------------------------------------------------------------
# 6. Opt-In Live PostgreSQL Integration Test
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_TESTS") != "1",
    reason="Live PostgreSQL tests require RUN_POSTGRES_TESTS=1",
)
def test_live_postgres_end_to_end_loading():
    """Live end-to-end integration test against local PostgreSQL database."""
    # Ensure database is reachable
    assert check_db_connection() is True, "Cannot connect to live PostgreSQL database"

    # Execute data loading
    summary = load_customer_transactions()
    assert summary["status"] == "success"
    assert summary["rows_loaded"] == EXPECTED_ROW_COUNT

    # Query loaded table
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM analytics.customer_transactions;")
            count = cur.fetchone()[0]
            assert count == EXPECTED_ROW_COUNT
