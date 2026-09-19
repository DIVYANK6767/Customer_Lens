"""Unit tests for the exploratory data analysis (EDA) support module."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.eda import (
    validate_eda_input,
    get_dataset_summary,
    add_time_features,
    get_time_summary,
    get_customer_summary,
    calculate_revenue_concentration,
    calculate_aov,
    calculate_repeat_customer_rate,
    get_order_summary,
    get_country_summary,
    get_product_summary,
)


@pytest.fixture
def sample_eda_df():
    """Return a small, deterministic customer transactions DataFrame for unit testing."""
    return pd.DataFrame({
        "InvoiceNo": ["1001", "1001", "1002", "1003", "1004"],
        "StockCode": ["A01", "A02", "A01", "B01", "C01"],
        "Description": ["Product A1", "Product A2", "Product A1", "Product B1", "Product C1"],
        "Quantity": [2, 1, 4, 10, 5],
        "InvoiceDate": [
            "2011-01-10 10:00:00",
            "2011-01-10 10:00:00",
            "2011-01-15 11:30:00",
            "2011-02-05 14:15:00",
            "2011-02-20 16:45:00",
        ],
        "UnitPrice": [10.0, 20.0, 10.0, 5.0, 8.0],
        "CustomerID": ["CUST_1", "CUST_1", "CUST_1", "CUST_2", "CUST_3"],
        "Country": ["United Kingdom", "United Kingdom", "United Kingdom", "Germany", "France"],
        "Revenue": [20.0, 20.0, 40.0, 50.0, 40.0],  # Total = 170.0
    })


# --- 1. Dataset summary ---
def test_get_dataset_summary(sample_eda_df):
    summary = get_dataset_summary(sample_eda_df)
    assert summary["total_rows"] == 5
    assert summary["unique_customers"] == 3
    assert summary["unique_orders"] == 4
    assert summary["unique_products"] == 4
    assert summary["unique_countries"] == 3
    assert summary["total_quantity"] == 22
    assert summary["total_revenue"] == 170.0
    assert summary["aov"] == round(170.0 / 4, 2)  # 42.50


# --- 2. Unique customer calculation & 3. Unique order calculation ---
def test_unique_counts(sample_eda_df):
    assert sample_eda_df["CustomerID"].nunique() == 3
    assert sample_eda_df["InvoiceNo"].nunique() == 4


# --- 4. Total revenue & 5. AOV ---
def test_calculate_aov(sample_eda_df):
    aov = calculate_aov(sample_eda_df)
    # Total revenue = 170.0, unique invoices = 4 => 170 / 4 = 42.50
    assert aov == 42.50


# --- 6. Customer revenue aggregation ---
def test_get_customer_summary(sample_eda_df):
    cust_summary = get_customer_summary(sample_eda_df)
    assert len(cust_summary) == 3
    # CUST_1: Invoices 1001 (40) + 1002 (40) = 80.0, Orders = 2, Qty = 7
    cust_1 = cust_summary[cust_summary["CustomerID"] == "CUST_1"].iloc[0]
    assert cust_1["total_revenue"] == 80.0
    assert cust_1["order_count"] == 2
    assert cust_1["total_quantity"] == 7
    assert cust_1["aov"] == 40.0

    # CUST_2: Invoice 1003 (50.0), Orders = 1
    cust_2 = cust_summary[cust_summary["CustomerID"] == "CUST_2"].iloc[0]
    assert cust_2["total_revenue"] == 50.0
    assert cust_2["order_count"] == 1


# --- 7. Orders per customer, 8. Repeat customer identification, 9. Repeat rate ---
def test_repeat_customer_rate(sample_eda_df):
    repeat_stats = calculate_repeat_customer_rate(sample_eda_df)
    # CUST_1 has 2 orders (repeat), CUST_2 has 1 order, CUST_3 has 1 order (one-time)
    assert repeat_stats["total_customers"] == 3
    assert repeat_stats["one_time_customers"] == 2
    assert repeat_stats["repeat_customers"] == 1
    assert repeat_stats["repeat_customer_rate"] == round((1 / 3) * 100, 2)
    assert repeat_stats["one_time_customer_rate"] == round((2 / 3) * 100, 2)


def test_get_order_summary(sample_eda_df):
    order_summary = get_order_summary(sample_eda_df)
    assert order_summary["total_orders"] == 4
    assert order_summary["aov"] == 42.50
    assert order_summary["one_time_customers"] == 2
    assert order_summary["repeat_customers"] == 1
    assert order_summary["orders_per_customer_max"] == 2


# --- 10. Monthly aggregation ---
def test_get_time_summary(sample_eda_df):
    time_summary = get_time_summary(sample_eda_df)
    monthly = time_summary["monthly"]
    assert len(monthly) == 2  # 2011-01 and 2011-02
    jan = monthly[monthly["YearMonth"] == "2011-01"].iloc[0]
    assert jan["Revenue"] == 80.0
    assert jan["Orders"] == 2
    assert jan["Customers"] == 1

    feb = monthly[monthly["YearMonth"] == "2011-02"].iloc[0]
    assert feb["Revenue"] == 90.0
    assert feb["Orders"] == 2
    assert feb["Customers"] == 2


# --- 11. Country aggregation ---
def test_get_country_summary(sample_eda_df):
    country_summary = get_country_summary(sample_eda_df)
    assert len(country_summary) == 3
    uk = country_summary[country_summary["Country"] == "United Kingdom"].iloc[0]
    assert uk["Revenue"] == 80.0
    assert uk["Orders"] == 2
    assert uk["Customers"] == 1
    assert uk["PctRevenue"] == round((80.0 / 170.0) * 100, 2)


# --- 12. Revenue concentration ---
def test_calculate_revenue_concentration(sample_eda_df):
    conc = calculate_revenue_concentration(sample_eda_df)
    assert conc["total_customers"] == 3
    assert conc["total_revenue"] == 170.0
    # Top customer is CUST_1 with 80.0
    assert conc["top_10_revenue"] == 170.0  # since only 3 customers
    assert conc["top_10_pct"] == 100.0


# --- 13. Revenue calculation consistency ---
def test_revenue_consistency(sample_eda_df):
    expected_rev = (sample_eda_df["Quantity"] * sample_eda_df["UnitPrice"]).round(2)
    assert (sample_eda_df["Revenue"] == expected_rev).all()


# --- 14. Invalid input detection ---
def test_validate_eda_input_missing_column(sample_eda_df):
    bad_df = sample_eda_df.drop(columns=["Revenue"])
    with pytest.raises(ValueError) as exc:
        validate_eda_input(bad_df)
    assert "Missing required column(s)" in str(exc.value)


def test_validate_eda_input_null_customer(sample_eda_df):
    bad_df = sample_eda_df.copy()
    bad_df.loc[0, "CustomerID"] = None
    with pytest.raises(ValueError) as exc:
        validate_eda_input(bad_df)
    assert "missing CustomerID" in str(exc.value)


def test_validate_eda_input_negative_quantity(sample_eda_df):
    bad_df = sample_eda_df.copy()
    bad_df.loc[0, "Quantity"] = -5
    with pytest.raises(ValueError) as exc:
        validate_eda_input(bad_df)
    assert "Quantity <= 0" in str(exc.value)


def test_validate_eda_input_zero_price(sample_eda_df):
    bad_df = sample_eda_df.copy()
    bad_df.loc[0, "UnitPrice"] = 0.0
    with pytest.raises(ValueError) as exc:
        validate_eda_input(bad_df)
    assert "UnitPrice <= 0" in str(exc.value)


# --- 15. Empty dataset handling ---
def test_empty_dataset_handling():
    empty_df = pd.DataFrame(columns=[
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country", "Revenue"
    ])
    assert validate_eda_input(empty_df) is True
    summary = get_dataset_summary(empty_df)
    assert summary["total_rows"] == 0
    assert summary["total_revenue"] == 0.0
    assert calculate_aov(empty_df) == 0.0
    cust_summary = get_customer_summary(empty_df)
    assert len(cust_summary) == 0
    conc = calculate_revenue_concentration(empty_df)
    assert conc["total_revenue"] == 0.0


# --- Product summary ---
def test_get_product_summary(sample_eda_df):
    prod_summary = get_product_summary(sample_eda_df, top_n=2)
    assert prod_summary["total_unique_products"] == 4
    top_qty = prod_summary["top_by_quantity"]
    assert len(top_qty) <= 2
    assert top_qty.iloc[0]["Quantity"] == 10  # Product B1
