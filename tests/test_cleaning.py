"""Unit tests for the data cleaning and quality pipeline."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.cleaning import (
    parse_invoice_date,
    normalize_columns,
    identify_transaction_types,
    remove_exact_duplicates,
    identify_invalid_prices,
    identify_non_customer_adjustments,
    handle_missing_customer_ids,
    handle_missing_descriptions,
    create_revenue,
    clean_transactions,
    get_customer_transactions,
    get_cleaning_report,
    save_cleaned_data,
)


@pytest.fixture
def synthetic_raw_data():
    """Return a synthetic DataFrame capturing all edge cases and transaction types."""
    return pd.DataFrame({
        "InvoiceNo": [
            "536365",      # 0: Standard valid sale
            "536365",      # 1: Exact duplicate of row 0
            "536366",      # 2: Valid sale with missing Description
            "536367",      # 3: Valid sale with missing CustomerID
            "C536379",     # 4: Customer Cancellation
            "A563185",     # 5: Accounting adjustment
            "536380",      # 6: Warehouse adjustment (negative qty, no C, missing CustomerID)
            "536381",      # 7: Zero quantity anomaly
            "536382",      # 8: Zero price anomaly (gift/promotional)
            "536383",      # 9: Negative price anomaly
        ],
        "StockCode": [
            "85123A ",
            "85123A ",
            "22423",
            "71053",
            "D",
            "B",
            "84406B",
            "22841",
            "22580",
            "B",
        ],
        "Description": [
            " white hanging heart ",
            " white hanging heart ",
            None,
            "WHITE METAL LANTERN",
            "Discount",
            "Adjust bad debt",
            "damaged",
            "ROUND SNACK BOXES",
            "PLASTERS IN TIN",
            "Adjust bad debt",
        ],
        "Quantity": [
            6,
            6,
            4,
            2,
            -1,
            1,
            -10,
            0,
            1,
            1,
        ],
        "InvoiceDate": [
            "12/1/2010 8:26",
            "12/1/2010 8:26",
            "12/1/2010 8:28",
            "12/1/2010 8:30",
            "12/1/2010 8:34",
            "8/12/2011 14:50",
            "12/1/2010 9:00",
            "12/1/2010 9:15",
            "12/1/2010 9:20",
            "8/12/2011 14:51",
        ],
        "UnitPrice": [
            2.55,
            2.55,
            12.75,
            3.39,
            27.50,
            11062.06,
            0.0,
            2.10,
            0.0,
            -11062.06,
        ],
        "CustomerID": [
            "17850",
            "17850",
            "13047",
            None,
            "14527",
            None,
            None,
            "16560",
            None,
            None,
        ],
        "Country": [
            " United Kingdom ",
            " United Kingdom ",
            "United Kingdom",
            "France",
            "United Kingdom",
            "United Kingdom",
            "United Kingdom",
            "Germany",
            "EIRE",
            "United Kingdom",
        ],
    })


# --- 1. InvoiceDate parsing ---
def test_parse_invoice_date_valid(synthetic_raw_data):
    df_parsed = parse_invoice_date(synthetic_raw_data)
    assert pd.api.types.is_datetime64_any_dtype(df_parsed["InvoiceDate"])
    assert df_parsed["InvoiceDate"].iloc[0] == pd.Timestamp("2010-12-01 08:26:00")
    assert df_parsed["InvoiceDate"].isna().sum() == 0


# --- 2. Invalid date detection ---
def test_parse_invoice_date_invalid_detection():
    df_invalid = pd.DataFrame({
        "InvoiceDate": ["12/1/2010 8:26", "invalid-date-string", "2020-99-99"]
    })
    with pytest.raises(ValueError) as exc_info:
        parse_invoice_date(df_invalid)
    assert "unparseable date value" in str(exc_info.value)
    assert "invalid-date-string" in str(exc_info.value)


# --- 3. Exact duplicate removal ---
def test_remove_exact_duplicates(synthetic_raw_data):
    df_dedup, dups_removed = remove_exact_duplicates(synthetic_raw_data)
    assert dups_removed == 1
    assert len(df_dedup) == len(synthetic_raw_data) - 1
    assert df_dedup.duplicated().sum() == 0


# --- 4. Cancellation classification ---
def test_cancellation_classification(synthetic_raw_data):
    df_types = identify_transaction_types(synthetic_raw_data)
    cancellation_row = df_types[df_types["InvoiceNo"] == "C536379"]
    assert len(cancellation_row) == 1
    assert cancellation_row["TransactionType"].iloc[0] == "Cancellation"


# --- 5. Adjustment classification ---
def test_adjustment_classification(synthetic_raw_data):
    df_types = identify_transaction_types(synthetic_raw_data)
    # A-prefix row
    a_row = df_types[df_types["InvoiceNo"] == "A563185"]
    assert a_row["TransactionType"].iloc[0] == "Adjustment"

    # Unprefixed negative quantity warehouse adjustment
    adj_qty_row = df_types[df_types["InvoiceNo"] == "536380"]
    assert adj_qty_row["TransactionType"].iloc[0] == "Adjustment"


# --- 6. Zero Quantity handling ---
def test_zero_quantity_handling(synthetic_raw_data):
    df_types = identify_transaction_types(synthetic_raw_data)
    zero_qty_row = df_types[df_types["InvoiceNo"] == "536381"]
    assert zero_qty_row["TransactionType"].iloc[0] == "Invalid"


# --- 7. Negative Quantity handling ---
def test_negative_quantity_handling(synthetic_raw_data):
    df_types = identify_transaction_types(synthetic_raw_data)
    # Neither negative quantity should be classified as Sale
    neg_qty_rows = df_types[df_types["Quantity"] < 0]
    assert len(neg_qty_rows) == 2
    assert "Sale" not in neg_qty_rows["TransactionType"].values


# --- 8. Zero UnitPrice handling ---
def test_zero_unit_price_handling(synthetic_raw_data):
    df_types = identify_transaction_types(synthetic_raw_data)
    zero_price_row = df_types[df_types["InvoiceNo"] == "536382"]
    assert zero_price_row["TransactionType"].iloc[0] == "Invalid"
    assert zero_price_row["UnitPrice"].iloc[0] == 0.0  # Not mutated


# --- 9. Negative UnitPrice handling ---
def test_negative_unit_price_handling(synthetic_raw_data):
    df_types = identify_transaction_types(synthetic_raw_data)
    neg_price_row = df_types[df_types["InvoiceNo"] == "536383"]
    assert neg_price_row["TransactionType"].iloc[0] in ("Adjustment", "Invalid")
    assert neg_price_row["UnitPrice"].iloc[0] < 0  # Not mutated


# --- 10. Missing CustomerID handling ---
def test_missing_customer_id_handling(synthetic_raw_data):
    valid_cust, missing_cust = handle_missing_customer_ids(synthetic_raw_data, drop=False)
    assert len(valid_cust) + len(missing_cust) == len(synthetic_raw_data)
    assert missing_cust["CustomerID"].isna().all()
    # Ensure no synthetic filler IDs are generated
    assert not (valid_cust["CustomerID"] == "Unknown").any()
    assert not (valid_cust["CustomerID"] == "0").any()


# --- 11. Missing Description preservation ---
def test_missing_description_preservation(synthetic_raw_data):
    df_desc = handle_missing_descriptions(synthetic_raw_data)
    assert "DescriptionMissing" in df_desc.columns
    # Row 2 had None description
    assert df_desc.loc[2, "DescriptionMissing"] == True
    # Row 0 had valid description
    assert df_desc.loc[0, "DescriptionMissing"] == False
    # Row 2 is NOT dropped
    assert len(df_desc) == len(synthetic_raw_data)


# --- 12. Revenue calculation ---
def test_revenue_calculation(synthetic_raw_data):
    df_rev = create_revenue(synthetic_raw_data)
    assert "Revenue" in df_rev.columns
    # Row 0: 6 * 2.55 = 15.30
    assert df_rev.loc[0, "Revenue"] == 15.30
    # Row 2: 4 * 12.75 = 51.00
    assert df_rev.loc[2, "Revenue"] == 51.00


# --- 13. Customer analytics filtering ---
def test_customer_analytics_filtering(synthetic_raw_data):
    clean_df = clean_transactions(synthetic_raw_data)
    cust_df = get_customer_transactions(clean_df)

    # In synthetic data:
    # Row 0: Valid sale with CustomerID 17850 -> KEPT
    # Row 1: Duplicate -> REMOVED
    # Row 2: Valid sale with CustomerID 13047 (missing desc) -> KEPT
    # Row 3: Missing CustomerID -> EXCLUDED
    # Row 4: Cancellation -> EXCLUDED
    # Row 5: Adjustment -> EXCLUDED
    # Row 6: Warehouse adjustment -> EXCLUDED
    # Row 7: Zero qty -> EXCLUDED
    # Row 8: Zero price -> EXCLUDED
    # Row 9: Negative price -> EXCLUDED
    assert len(cust_df) == 2
    assert set(cust_df["CustomerID"]) == {"17850", "13047"}
    assert (cust_df["TransactionType"] == "Sale").all()
    assert (cust_df["Quantity"] > 0).all()
    assert (cust_df["UnitPrice"] > 0).all()
    assert cust_df["CustomerID"].notna().all()


# --- 14. Output schema ---
def test_output_schema(synthetic_raw_data):
    clean_df = clean_transactions(synthetic_raw_data)
    expected_cols = [
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
    assert list(clean_df.columns) == expected_cols
    assert pd.api.types.is_datetime64_any_dtype(clean_df["InvoiceDate"])
    assert pd.api.types.is_numeric_dtype(clean_df["Quantity"])
    assert pd.api.types.is_numeric_dtype(clean_df["UnitPrice"])
    assert pd.api.types.is_numeric_dtype(clean_df["Revenue"])


# --- 15. Cleaning report generation ---
def test_cleaning_report_generation(synthetic_raw_data):
    clean_df = clean_transactions(synthetic_raw_data)
    cust_df = get_customer_transactions(clean_df)
    report = get_cleaning_report(synthetic_raw_data, clean_df, cust_df)

    assert report["raw_total_rows"] == 10
    assert report["exact_duplicates_removed"] == 1
    assert report["clean_total_rows"] == 9
    assert report["customer_transactions_rows"] == 2
    assert report["excluded_from_customer_analytics"] == 8
    assert report["customer_unique_customers"] == 2


# --- 16. Empty DataFrame edge case ---
def test_empty_dataframe_edge_case():
    empty_df = pd.DataFrame(columns=[
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country"
    ])
    clean_empty = clean_transactions(empty_df)
    assert len(clean_empty) == 0
    cust_empty = get_customer_transactions(clean_empty)
    assert len(cust_empty) == 0


# --- 17. Already-clean DataFrame ---
def test_already_clean_dataframe():
    clean_initial = pd.DataFrame({
        "InvoiceNo": ["536365"],
        "StockCode": ["85123A"],
        "Description": ["WHITE HANGING HEART T-LIGHT HOLDER"],
        "Quantity": [6],
        "InvoiceDate": ["12/1/2010 8:26"],
        "UnitPrice": [2.55],
        "CustomerID": ["17850"],
        "Country": ["United Kingdom"],
    })
    clean_df = clean_transactions(clean_initial)
    assert len(clean_df) == 1
    assert clean_df["TransactionType"].iloc[0] == "Sale"
    assert clean_df["Revenue"].iloc[0] == 15.30


# --- 18. Idempotent behavior ---
def test_idempotent_behavior(synthetic_raw_data):
    clean_once = clean_transactions(synthetic_raw_data)
    clean_twice = clean_transactions(clean_once)
    assert len(clean_once) == len(clean_twice)
    assert list(clean_once["TransactionType"]) == list(clean_twice["TransactionType"])
    assert list(clean_once["Revenue"]) == list(clean_twice["Revenue"])


# --- 19. Save cleaned data ---
def test_save_cleaned_data(tmp_path, synthetic_raw_data):
    clean_df = clean_transactions(synthetic_raw_data)
    out_file = tmp_path / "subfolder" / "test_clean.csv"
    saved_path = save_cleaned_data(clean_df, out_file)
    assert saved_path.exists()
    reloaded = pd.read_csv(saved_path)
    assert len(reloaded) == len(clean_df)
