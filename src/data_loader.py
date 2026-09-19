"""Raw data ingestion and schema validation module for CustomerLens.

This module provides functions to load the raw e-commerce transaction dataset
using project-relative paths, validate the expected schema, and return the
unaltered raw DataFrame without performing business cleaning or transformations.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import pandas as pd

# Define project root relative to this file's location (src/ -> Customer_Lens/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default relative path to raw transaction dataset
DEFAULT_RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "Online_Retail.csv"

# Expected schema based on the verified UCI Online Retail dataset
EXPECTED_COLUMNS: List[str] = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]

# Recommended default dtypes to preserve identifier precision and leading characters
DEFAULT_DTYPES: Dict[str, type] = {
    "InvoiceNo": str,
    "StockCode": str,
    "CustomerID": str,
}


class SchemaValidationError(ValueError):
    """Raised when the dataset schema does not match expected columns."""
    pass


def get_project_root() -> Path:
    """Return the absolute Path to the CustomerLens project root directory."""
    return PROJECT_ROOT


def validate_schema(
    df: pd.DataFrame,
    expected_columns: Optional[List[str]] = None,
) -> bool:
    """Validate that the DataFrame contains all expected columns.

    Args:
        df: The pandas DataFrame to validate.
        expected_columns: List of required column names. Defaults to EXPECTED_COLUMNS.

    Returns:
        bool: True if schema is valid.

    Raises:
        SchemaValidationError: If one or more required columns are missing from df.
    """
    if expected_columns is None:
        expected_columns = EXPECTED_COLUMNS

    actual_columns = set(df.columns)
    missing_columns = [col for col in expected_columns if col not in actual_columns]

    if missing_columns:
        raise SchemaValidationError(
            f"Schema validation failed. Missing required column(s): {missing_columns}. "
            f"Expected: {expected_columns}. Found: {list(df.columns)}."
        )

    return True


def load_raw_data(
    file_path: Optional[Union[str, Path]] = None,
    validate: bool = True,
    encoding: str = "utf-8",
    dtype: Optional[dict] = None,
    **kwargs,
) -> pd.DataFrame:
    """Load the raw transactional dataset from CSV.

    Preserves raw data integrity without performing cleaning, filtering,
    or deduplication.

    Args:
        file_path: Path to the CSV file. If None, defaults to data/raw/Online_Retail.csv
            relative to the project root.
        validate: Whether to run schema validation on the loaded data.
        encoding: File encoding (defaults to 'utf-8').
        dtype: Data type mapping for columns. Defaults to DEFAULT_DTYPES.
        **kwargs: Additional keyword arguments forwarded to pd.read_csv.

    Returns:
        pd.DataFrame: The loaded raw DataFrame.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        SchemaValidationError: If schema validation is enabled and required columns are missing.
    """
    if file_path is None:
        target_path = DEFAULT_RAW_DATA_PATH
    else:
        target_path = Path(file_path)
        if not target_path.is_absolute():
            # Resolve relative paths against the project root
            target_path = PROJECT_ROOT / target_path

    if not target_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at '{target_path}'. "
            f"Please ensure 'Online_Retail.csv' exists in 'data/raw/'."
        )

    if dtype is None and "dtype" not in kwargs:
        dtype = DEFAULT_DTYPES

    df = pd.read_csv(target_path, encoding=encoding, dtype=dtype, **kwargs)

    if validate:
        validate_schema(df)

    return df
