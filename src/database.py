"""Database connection and configuration module for CustomerLens.

Manages PostgreSQL connection configuration, environment variable parsing,
and safe context-managed database connections using psycopg.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import psycopg
try:
    from dotenv import dotenv_values, load_dotenv
except ImportError:
    dotenv_values = None
    load_dotenv = None

# Project Root Resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_project_root() -> Path:
    """Return the absolute path to the CustomerLens project root."""
    return PROJECT_ROOT


def load_env_file(env_path: Optional[Union[str, Path]] = None) -> None:
    """Load environment variables from a .env file if it exists.

    Args:
        env_path: Optional path to .env file. Defaults to PROJECT_ROOT / '.env'.
    """
    if env_path is not None:
        target = Path(env_path)
    else:
        target = PROJECT_ROOT / ".env"

    if target.is_file():
        if dotenv_values is not None:
            # Parse key-values directly from target .env file
            env_vars = dotenv_values(target)
            for key, val in env_vars.items():
                if val is not None:
                    # Set if key is missing or currently set to an empty string in os.environ
                    if key not in os.environ or not os.environ[key]:
                        os.environ[key] = val
        else:
            # Fallback simple parser if python-dotenv is not installed
            for line in target.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ or not os.environ[key]:
                        os.environ[key] = val


def get_database_config(env_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Retrieve database connection parameters from environment variables.

    Supports standard POSTGRES_* variable names with fallback to DB_* names.

    Args:
        env_path: Optional path to a specific .env file.

    Returns:
        Dict with keys: host, port, dbname, user, password.
    """
    load_env_file(env_path)

    host = os.environ.get("POSTGRES_HOST") or os.environ.get("DB_HOST") or "localhost"
    port_str = os.environ.get("POSTGRES_PORT") or os.environ.get("DB_PORT") or "5432"
    dbname = os.environ.get("POSTGRES_DB") or os.environ.get("DB_NAME") or "customer_lens"
    user = os.environ.get("POSTGRES_USER") or os.environ.get("DB_USER") or "postgres"
    password = os.environ.get("POSTGRES_PASSWORD") or os.environ.get("DB_PASSWORD") or ""

    try:
        port = int(port_str)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid POSTGRES_PORT value: '{port_str}'. Must be an integer.")

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
    }


def get_masked_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of the configuration with sensitive credentials masked.

    Args:
        config: Connection configuration dictionary.

    Returns:
        Dict with masked password suitable for logging and error reporting.
    """
    masked = dict(config)
    if "password" in masked and masked["password"]:
        masked["password"] = "********"
    elif "password" in masked:
        masked["password"] = ""
    return masked


def get_connection(
    config: Optional[Dict[str, Any]] = None,
    autocommit: bool = False,
) -> psycopg.Connection:
    """Establish and return a connection to the PostgreSQL database.

    Args:
        config: Optional dictionary with connection parameters. If None,
            loads configuration via get_database_config().
        autocommit: Whether to enable autocommit mode on the connection.

    Returns:
        psycopg.Connection instance.

    Raises:
        ConnectionError: If connection cannot be established, without exposing
            the plaintext password in the exception message.
    """
    cfg = config if config is not None else get_database_config()
    masked = get_masked_config(cfg)

    try:
        conn = psycopg.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            autocommit=autocommit,
        )
        return conn
    except psycopg.Error as exc:
        raise ConnectionError(
            f"Failed to connect to PostgreSQL database '{masked['dbname']}' "
            f"at {masked['host']}:{masked['port']} as user '{masked['user']}': "
            f"{type(exc).__name__} - {exc}"
        ) from None


def test_connection(config: Optional[Dict[str, Any]] = None) -> bool:
    """Test whether a connection can be successfully opened to PostgreSQL.

    Args:
        config: Optional connection configuration dictionary.

    Returns:
        True if connection succeeds, False otherwise.
    """
    try:
        with get_connection(config) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
                return result == (1,)
    except Exception:
        return False
