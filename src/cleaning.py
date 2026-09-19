"""Data cleaning and quality pipeline for CustomerLens.

This module provides modular, deterministic, and business-rule-driven functions
to clean e-commerce transaction data, identify transaction types, handle anomalies,
compute revenue, and produce analytical datasets without mutating raw source data.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.data_loader import get_project_root, load_raw_data

PROJECT_ROOT = get_project_root()
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------------------------
# 1. Date Parsing
# ---------------------------------------------------------------------------

def parse_invoice_date(
    df: pd.DataFrame,
    column: str = "InvoiceDate",
    date_format: Optional[str] = "%m/%d/%Y %H:%M",
) -> pd.DataFrame:
    """Parse transaction date column into pandas datetime dtype.

    Detects and explicitly raises an error if invalid date strings are present.

    Args:
        df: Input DataFrame.
        column: Name of the date column to parse.
        date_format: Expected datetime format string.

    Returns:
        pd.DataFrame: A copy of df with the date column converted to datetime64[ns].

    Raises:
        ValueError: If unparseable or invalid date values are detected.
    """
    df_out = df.copy()
    if df_out.empty:
        df_out[column] = pd.to_datetime(df_out[column])
        return df_out

    # Parse with coercion to detect invalid dates explicitly
    parsed = pd.to_datetime(df_out[column], format=date_format, errors="coerce")
    
    # If explicit format fails for any non-null date, attempt general parsing fallback
    if parsed.isna().any() and df_out[column].notna().any():
        parsed = pd.to_datetime(df_out[column], errors="coerce")

    # Detect any unparseable values
    invalid_mask = df_out[column].notna() & parsed.isna()
    if invalid_mask.any():
        invalid_samples = df_out.loc[invalid_mask, column].head(5).tolist()
        invalid_count = int(invalid_mask.sum())
        raise ValueError(
            f"Detected {invalid_count} unparseable date value(s) in column '{column}'. "
            f"Sample invalid values: {invalid_samples}"
        )

    df_out[column] = parsed
    return df_out


# ---------------------------------------------------------------------------
# 2. Text Normalization
# ---------------------------------------------------------------------------

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize string columns by stripping whitespace and standardizing casing.

    Preserves CustomerID formatting and treats NaNs cleanly without fabricating IDs.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: A copy of df with standardized text representations.
    """
    df_out = df.copy()

    for col in ["InvoiceNo", "StockCode", "Country"]:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str).str.strip()

    if "Description" in df_out.columns:
        # Strip whitespace for non-null descriptions, preserve None/NaN
        mask = df_out["Description"].notna()
        df_out.loc[mask, "Description"] = df_out.loc[mask, "Description"].astype(str).str.strip().str.upper()

    if "CustomerID" in df_out.columns:
        # Standardize CustomerID: strip '.0' if parsed as float string, preserve NaN as None
        def _clean_cust_id(val):
            if pd.isna(val) or val is None or val == "" or str(val).lower() in ("nan", "none"):
                return None
            val_str = str(val).strip()
            if val_str.endswith(".0"):
                val_str = val_str[:-2]
            return val_str if val_str else None

        df_out["CustomerID"] = df_out["CustomerID"].apply(_clean_cust_id)

    return df_out


# ---------------------------------------------------------------------------
# 3. Transaction Classification
# ---------------------------------------------------------------------------

def identify_transaction_types(df: pd.DataFrame) -> pd.DataFrame:
    """Classify each row into a deterministic TransactionType.

    Categories:
    - 'Cancellation': InvoiceNo begins with 'C' or 'c'.
    - 'Adjustment': InvoiceNo begins with 'A' or 'a' (accounting bad debt entries)
                    OR Quantity < 0 without 'C' prefix (unprefixed warehouse write-offs).
    - 'Invalid': Quantity == 0 OR UnitPrice <= 0 (where not already Cancellation/Adjustment).
    - 'Sale': Standard completed purchase (Quantity > 0, UnitPrice > 0, standard InvoiceNo).

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: A copy of df with the added 'TransactionType' column.
    """
    df_out = df.copy()
    if df_out.empty:
        df_out["TransactionType"] = pd.Series(dtype="object")
        return df_out

    inv = df_out["InvoiceNo"].astype(str)
    qty = pd.to_numeric(df_out["Quantity"], errors="coerce").fillna(0)
    price = pd.to_numeric(df_out["UnitPrice"], errors="coerce").fillna(0)

    # Deterministic condition masks
    is_canc = inv.str.startswith(("C", "c"))
    is_adj = inv.str.startswith(("A", "a")) | ((qty < 0) & (~is_canc))
    is_invalid = ((qty == 0) | (price <= 0)) & (~is_canc) & (~is_adj)
    is_sale = (~is_canc) & (~is_adj) & (~is_invalid)

    types = pd.Series("Sale", index=df_out.index, dtype="object")
    types[is_canc] = "Cancellation"
    types[is_adj] = "Adjustment"
    types[is_invalid] = "Invalid"
    types[is_sale] = "Sale"

    df_out["TransactionType"] = types
    return df_out


# ---------------------------------------------------------------------------
# 4. Duplicate Removal
# ---------------------------------------------------------------------------

def remove_exact_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Identify and remove exact duplicate rows across all columns.

    Args:
        df: Input DataFrame.

    Returns:
        Tuple[pd.DataFrame, int]: Deduplicated DataFrame and the count of removed rows.
    """
    duplicate_count = int(df.duplicated().sum())
    df_clean = df.drop_duplicates(keep="first").copy()
    return df_clean, duplicate_count


# ---------------------------------------------------------------------------
# 5. Price & Adjustment Filters
# ---------------------------------------------------------------------------

def identify_invalid_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Return all rows with non-positive unit prices (UnitPrice <= 0).

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: Filtered DataFrame containing only invalid price rows.
    """
    return df[df["UnitPrice"] <= 0].copy()


def identify_non_customer_adjustments(df: pd.DataFrame) -> pd.DataFrame:
    """Return all rows representing adjustments or lacking a customer identifier.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: Rows that are adjustments or missing CustomerID.
    """
    type_col = df["TransactionType"] if "TransactionType" in df.columns else pd.Series(index=df.index)
    mask = (df["CustomerID"].isna()) | (type_col == "Adjustment")
    return df[mask].copy()


# ---------------------------------------------------------------------------
# 6. Missing Identifiers & Descriptions
# ---------------------------------------------------------------------------

def handle_missing_customer_ids(
    df: pd.DataFrame,
    drop: bool = False,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
    """Handle missing CustomerID values conservatively.

    Does not fabricate or impute fake customer IDs.

    Args:
        df: Input DataFrame.
        drop: If True, returns only rows with non-null CustomerID.
              If False, returns a tuple of (valid_customers_df, missing_customers_df).

    Returns:
        DataFrame or Tuple of DataFrames based on drop argument.
    """
    valid_mask = df["CustomerID"].notna()
    if drop:
        return df[valid_mask].copy()
    return df[valid_mask].copy(), df[~valid_mask].copy()


def handle_missing_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Flag missing Description values without removing rows or inventing product names.

    Adds a boolean 'DescriptionMissing' column.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with 'DescriptionMissing' column.
    """
    df_out = df.copy()
    if "Description" in df_out.columns:
        df_out["DescriptionMissing"] = df_out["Description"].isna() | (df_out["Description"].astype(str).str.strip() == "")
    else:
        df_out["DescriptionMissing"] = False
    return df_out


# ---------------------------------------------------------------------------
# 7. Revenue Calculation
# ---------------------------------------------------------------------------

def create_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate monetary revenue as Quantity * UnitPrice.

    Uses vectorized arithmetic and rounds to 2 decimal places.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with added 'Revenue' column.
    """
    df_out = df.copy()
    if df_out.empty:
        df_out["Revenue"] = pd.Series(dtype="float64")
        return df_out

    qty = pd.to_numeric(df_out["Quantity"], errors="coerce").fillna(0)
    price = pd.to_numeric(df_out["UnitPrice"], errors="coerce").fillna(0)
    df_out["Revenue"] = (qty * price).round(2)
    return df_out


# ---------------------------------------------------------------------------
# 8. Full Transaction Pipeline & Customer Dataset Extraction
# ---------------------------------------------------------------------------

def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Execute the complete data cleaning and transformation pipeline.

    Orchestrates:
    1. Duplicate removal (exact duplicates across all 8 fields).
    2. Text normalization (whitespace strip, uppercase descriptions).
    3. Datetime parsing of InvoiceDate.
    4. Transaction classification ('Sale', 'Cancellation', 'Adjustment', 'Invalid').
    5. DescriptionMissing boolean flag creation.
    6. Line-item Revenue calculation.

    Preserves all transaction records and types for downstream auditing.

    Args:
        df: Raw transactional DataFrame.

    Returns:
        pd.DataFrame: Cleaned, typed, and enriched transaction DataFrame.
    """
    # 1. Deduplication
    df_clean, _ = remove_exact_duplicates(df)

    # 2. Text normalization
    df_clean = normalize_columns(df_clean)

    # 3. Datetime parsing
    df_clean = parse_invoice_date(df_clean)

    # 4. Classification
    df_clean = identify_transaction_types(df_clean)

    # 5. Missing description handling
    df_clean = handle_missing_descriptions(df_clean)

    # 6. Revenue calculation
    df_clean = create_revenue(df_clean)

    # Reorder columns logically
    cols = [
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
    existing_cols = [c for c in cols if c in df_clean.columns]
    return df_clean[existing_cols]


def get_customer_transactions(clean_df: pd.DataFrame) -> pd.DataFrame:
    """Extract primary customer completed purchases for SQL analysis and RFM.

    Applies strict business filters:
    - TransactionType == 'Sale'
    - Quantity > 0
    - UnitPrice > 0
    - CustomerID is not null

    Args:
        clean_df: Cleaned transaction DataFrame output from clean_transactions().

    Returns:
        pd.DataFrame: Filtered customer purchase transactions.
    """
    if clean_df.empty:
        return clean_df.copy()

    mask = (
        (clean_df["TransactionType"] == "Sale")
        & (clean_df["Quantity"] > 0)
        & (clean_df["UnitPrice"] > 0)
        & (clean_df["CustomerID"].notna())
    )
    return clean_df[mask].copy().reset_index(drop=True)


# ---------------------------------------------------------------------------
# 9. Cleaning Metrics & Reporting
# ---------------------------------------------------------------------------

def get_cleaning_report(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    customer_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Union[int, float]]:
    """Compute comprehensive before and after cleaning metrics.

    Args:
        raw_df: Raw input DataFrame before cleaning.
        clean_df: Comprehensive cleaned transaction DataFrame.
        customer_df: Primary customer purchase DataFrame.

    Returns:
        Dict: Dictionary of verified cleaning metrics.
    """
    if customer_df is None:
        customer_df = get_customer_transactions(clean_df)

    raw_rows = len(raw_df)
    clean_rows = len(clean_df)
    cust_rows = len(customer_df)

    exact_dups = int(raw_df.duplicated().sum())

    # Raw metrics
    raw_missing_cust = int(raw_df["CustomerID"].isna().sum()) if "CustomerID" in raw_df.columns else 0
    raw_missing_desc = int(raw_df["Description"].isna().sum()) if "Description" in raw_df.columns else 0
    raw_c_invoices = int(raw_df["InvoiceNo"].astype(str).str.startswith(("C", "c")).sum()) if "InvoiceNo" in raw_df.columns else 0
    raw_neg_qty = int((raw_df["Quantity"] < 0).sum()) if "Quantity" in raw_df.columns else 0
    raw_zero_qty = int((raw_df["Quantity"] == 0).sum()) if "Quantity" in raw_df.columns else 0
    raw_zero_price = int((raw_df["UnitPrice"] == 0).sum()) if "UnitPrice" in raw_df.columns else 0
    raw_neg_price = int((raw_df["UnitPrice"] < 0).sum()) if "UnitPrice" in raw_df.columns else 0

    # Clean metrics
    type_counts = clean_df["TransactionType"].value_counts().to_dict() if "TransactionType" in clean_df.columns else {}
    clean_sales = type_counts.get("Sale", 0)
    clean_cancellations = type_counts.get("Cancellation", 0)
    clean_adjustments = type_counts.get("Adjustment", 0)
    clean_invalid = type_counts.get("Invalid", 0)

    clean_missing_cust = int(clean_df["CustomerID"].isna().sum()) if "CustomerID" in clean_df.columns else 0
    clean_missing_desc = int(clean_df["DescriptionMissing"].sum()) if "DescriptionMissing" in clean_df.columns else 0

    # Customer dataset metrics
    unique_customers = int(customer_df["CustomerID"].nunique()) if "CustomerID" in customer_df.columns else 0
    unique_orders = int(customer_df["InvoiceNo"].nunique()) if "InvoiceNo" in customer_df.columns else 0
    total_customer_revenue = float(customer_df["Revenue"].sum()) if "Revenue" in customer_df.columns else 0.0

    pct_retained_clean = round((clean_rows / raw_rows * 100), 2) if raw_rows > 0 else 0.0
    pct_retained_cust = round((cust_rows / raw_rows * 100), 2) if raw_rows > 0 else 0.0
    excluded_from_cust = raw_rows - cust_rows

    return {
        "raw_total_rows": raw_rows,
        "exact_duplicates_removed": exact_dups,
        "clean_total_rows": clean_rows,
        "customer_transactions_rows": cust_rows,
        "excluded_from_customer_analytics": excluded_from_cust,
        "pct_retained_in_clean": pct_retained_clean,
        "pct_retained_in_customer_analytics": pct_retained_cust,
        # Raw observations
        "raw_missing_customer_id": raw_missing_cust,
        "raw_missing_description": raw_missing_desc,
        "raw_cancellation_rows": raw_c_invoices,
        "raw_negative_quantity_rows": raw_neg_qty,
        "raw_zero_quantity_rows": raw_zero_qty,
        "raw_zero_unit_price_rows": raw_zero_price,
        "raw_negative_unit_price_rows": raw_neg_price,
        # Cleaned classifications
        "clean_sales_rows": clean_sales,
        "clean_cancellation_rows": clean_cancellations,
        "clean_adjustment_rows": clean_adjustments,
        "clean_invalid_rows": clean_invalid,
        "clean_missing_customer_id": clean_missing_cust,
        "clean_missing_description": clean_missing_desc,
        # Primary Customer Analytics metrics
        "customer_unique_customers": unique_customers,
        "customer_unique_orders": unique_orders,
        "customer_total_revenue": round(total_customer_revenue, 2),
    }


def save_cleaned_data(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    """Save DataFrame to CSV at the designated project-relative path.

    Args:
        df: DataFrame to persist.
        output_path: Target destination path.

    Returns:
        Path: Resolved Path where data was saved.
    """
    target = Path(output_path)
    if not target.is_absolute():
        target = PROJECT_ROOT / target

    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False)
    return target


# ---------------------------------------------------------------------------
# 10. High-Level Orchestrator
# ---------------------------------------------------------------------------

def clean_dataset(
    raw_path: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    save: bool = True,
) -> Dict[str, Union[pd.DataFrame, Dict[str, Union[int, float]]]]:
    """Execute the full end-to-end data cleaning pipeline.

    Loads raw data, validates schema, applies transformations, produces
    clean_transactions and customer_transactions, generates reports,
    and optionally persists results to disk.

    Args:
        raw_path: Path to raw CSV. Defaults to data/raw/Online_Retail.csv.
        output_dir: Output folder. Defaults to data/processed/.
        save: If True, writes processed CSVs and Markdown report to disk.

    Returns:
        Dict: Contains 'clean_transactions', 'customer_transactions', and 'report'.
    """
    # 1. Ingestion via existing data_loader
    raw_df = load_raw_data(file_path=raw_path)

    # 2. Comprehensive Cleaning
    clean_df = clean_transactions(raw_df)

    # 3. Primary Customer Analytics Extraction
    customer_df = get_customer_transactions(clean_df)

    # 4. Generate Audit Report
    report = get_cleaning_report(raw_df, clean_df, customer_df)

    if save:
        out_dir = Path(output_dir) if output_dir else DEFAULT_PROCESSED_DIR
        if not out_dir.is_absolute():
            out_dir = PROJECT_ROOT / out_dir

        out_dir.mkdir(parents=True, exist_ok=True)

        # Save processed datasets
        save_cleaned_data(clean_df, out_dir / "clean_transactions.csv")
        save_cleaned_data(customer_df, out_dir / "customer_transactions.csv")

        # Save machine-readable report CSV
        report_df = pd.DataFrame([report])
        save_cleaned_data(report_df, out_dir / "cleaning_report.csv")

    return {
        "clean_transactions": clean_df,
        "customer_transactions": customer_df,
        "report": report,
    }


if __name__ == "__main__":
    print("Running CustomerLens data cleaning pipeline...")
    results = clean_dataset()
    rep = results["report"]
    print("Cleaning completed successfully!")
    print(f"Raw rows: {rep['raw_total_rows']}")
    print(f"Duplicates removed: {rep['exact_duplicates_removed']}")
    print(f"Clean transactions: {rep['clean_total_rows']}")
    print(f"Customer transactions: {rep['customer_transactions_rows']}")
    print(f"Unique customers: {rep['customer_unique_customers']}")
    print(f"Total customer revenue: £{rep['customer_total_revenue']:,.2f}")
