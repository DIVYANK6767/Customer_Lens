"""Unit and integration tests for the raw data loader and schema validator."""

import pytest
import pandas as pd
from pathlib import Path

from src.data_loader import (
    load_raw_data,
    validate_schema,
    SchemaValidationError,
    EXPECTED_COLUMNS,
    DEFAULT_RAW_DATA_PATH,
    get_project_root,
)


@pytest.fixture
def sample_valid_data():
    """Return a dictionary representing a minimal valid transaction row."""
    return {
        "InvoiceNo": ["536365"],
        "StockCode": ["85123A"],
        "Description": ["WHITE HANGING HEART T-LIGHT HOLDER"],
        "Quantity": [6],
        "InvoiceDate": ["12/1/2010 8:26"],
        "UnitPrice": [2.55],
        "CustomerID": ["17850"],
        "Country": ["United Kingdom"],
    }


@pytest.fixture
def sample_csv(tmp_path, sample_valid_data):
    """Create a temporary valid CSV file."""
    df = pd.DataFrame(sample_valid_data)
    csv_path = tmp_path / "valid_sample.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


# --- 1. Successful Loading ---
def test_successful_loading_with_sample_csv(sample_csv):
    """Test that a valid CSV file loads successfully and returns expected DataFrame."""
    df = load_raw_data(file_path=sample_csv)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == EXPECTED_COLUMNS
    assert df.loc[0, "InvoiceNo"] == "536365"
    assert df.loc[0, "Quantity"] == 6


# --- 2. Missing-File Handling ---
def test_missing_file_handling():
    """Test that attempting to load a non-existent file raises FileNotFoundError with clear message."""
    missing_path = "data/raw/does_not_exist.csv"
    with pytest.raises(FileNotFoundError) as exc_info:
        load_raw_data(file_path=missing_path)

    error_msg = str(exc_info.value)
    assert "Raw dataset not found" in error_msg
    assert "does_not_exist.csv" in error_msg


# --- 3. Required-Column Validation ---
def test_required_column_validation_valid_df(sample_valid_data):
    """Test that validate_schema returns True when all expected columns exist."""
    df = pd.DataFrame(sample_valid_data)
    assert validate_schema(df) is True


def test_required_column_validation_custom_columns():
    """Test that validate_schema works with a custom list of expected columns."""
    df = pd.DataFrame({"col1": [1], "col2": [2]})
    assert validate_schema(df, expected_columns=["col1", "col2"]) is True


# --- 4. Invalid-Schema Handling & 5. Error Messages ---
def test_invalid_schema_missing_single_column(sample_valid_data):
    """Test that validate_schema raises SchemaValidationError when a required column is missing."""
    del sample_valid_data["CustomerID"]
    df = pd.DataFrame(sample_valid_data)

    with pytest.raises(SchemaValidationError) as exc_info:
        validate_schema(df)

    error_msg = str(exc_info.value)
    assert "Schema validation failed" in error_msg
    assert "CustomerID" in error_msg
    assert "Found:" in error_msg


def test_invalid_schema_missing_multiple_columns():
    """Test that validate_schema identifies all missing columns in the error message."""
    incomplete_df = pd.DataFrame({
        "InvoiceNo": ["536365"],
        "StockCode": ["85123A"],
    })

    with pytest.raises(SchemaValidationError) as exc_info:
        validate_schema(incomplete_df)

    error_msg = str(exc_info.value)
    assert "CustomerID" in error_msg
    assert "InvoiceDate" in error_msg
    assert "UnitPrice" in error_msg
    assert "Quantity" in error_msg
    assert "Description" in error_msg
    assert "Country" in error_msg


def test_load_raw_data_raises_on_invalid_schema(tmp_path):
    """Test that load_raw_data fails schema validation when loading a CSV with missing columns."""
    bad_csv = tmp_path / "bad_schema.csv"
    pd.DataFrame({"A": [1], "B": [2]}).to_csv(bad_csv, index=False)

    with pytest.raises(SchemaValidationError) as exc_info:
        load_raw_data(file_path=bad_csv)

    assert "Schema validation failed" in str(exc_info.value)


# --- Preservation of Raw Data (No Business Cleaning in Loader) ---
def test_raw_data_preserved_uncleaned(tmp_path):
    """Test that load_raw_data does NOT drop cancellations, negative quantities, or NaNs."""
    raw_anomalies = {
        "InvoiceNo": ["C536379", "536380", "536381"],
        "StockCode": ["D", "85123A", "71053"],
        "Description": ["Discount", None, "WHITE METAL LANTERN"],
        "Quantity": [-1, 0, 10],
        "InvoiceDate": ["12/1/2010 8:26", "12/1/2010 8:30", "12/1/2010 8:35"],
        "UnitPrice": [-10.0, 0.0, 3.39],
        "CustomerID": [None, None, "17850"],
        "Country": ["United Kingdom", "United Kingdom", "United Kingdom"],
    }
    csv_path = tmp_path / "anomalies_sample.csv"
    pd.DataFrame(raw_anomalies).to_csv(csv_path, index=False)

    df = load_raw_data(file_path=csv_path)

    # Assert row count is preserved
    assert len(df) == 3

    # Assert cancellations are NOT removed
    assert (df["InvoiceNo"] == "C536379").any()

    # Assert negative quantities are NOT removed
    assert (df["Quantity"] == -1).any()

    # Assert zero quantities are NOT removed
    assert (df["Quantity"] == 0).any()

    # Assert zero/negative prices are NOT removed
    assert (df["UnitPrice"] == -10.0).any()
    assert (df["UnitPrice"] == 0.0).any()

    # Assert missing CustomerIDs are NOT dropped
    assert df["CustomerID"].isna().sum() == 2


# --- Project-Relative Paths ---
def test_project_root_resolution():
    """Verify that get_project_root returns a valid directory containing data/."""
    root = get_project_root()
    assert root.exists()
    assert (root / "data").exists()


# --- Integration Test: Production Raw Dataset ---
@pytest.mark.skipif(
    not DEFAULT_RAW_DATA_PATH.exists(),
    reason="Production raw dataset not found in data/raw/",
)
def test_production_raw_dataset_integration():
    """Integration test verifying that the actual production dataset loads with expected dimensions."""
    df = load_raw_data()
    assert len(df) == 541909
    assert list(df.columns) == EXPECTED_COLUMNS
    # Verify raw anomalies are preserved
    assert df["CustomerID"].isna().sum() == 135080
    assert (df["Quantity"] < 0).sum() == 10624
