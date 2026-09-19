"""
Unit and integration tests for Streamlit data access and utilities (Phase 11).

Validates data loading, schema integrity, executive KPI calculations,
formatting utilities, customer filtering logic, and reconciliation.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from app.utils import (
    format_currency,
    format_number,
    format_percentage,
    safe_percentage,
    calculate_executive_kpis,
    filter_customers,
    validate_required_columns,
    generate_customer_interpretation,
)

PROCESSED_DIR = Path("data/processed")


# ==============================================================================
# Utility & Formatting Tests
# ==============================================================================
def test_format_currency():
    """Assert currency formatting handles normal floats, zero, and None."""
    assert format_currency(8887208.89) == "£8,887,208.89"
    assert format_currency(0.0) == "£0.00"
    assert format_currency(None) == "£0.00"
    assert format_currency(np.nan) == "£0.00"
    assert format_currency(1234.5, precision=1) == "£1,234.5"


def test_format_number():
    """Assert number formatting handles integers and floats with thousands commas."""
    assert format_number(4338) == "4,338"
    assert format_number(18532) == "18,532"
    assert format_number(0) == "0"
    assert format_number(None) == "0"
    assert format_number(1234.56, precision=2) == "1,234.56"


def test_format_percentage():
    """Assert percentage formatting handles valid numbers and None."""
    assert format_percentage(16.51) == "16.5%"
    assert format_percentage(65.06) == "65.1%"
    assert format_percentage(0.0) == "0.0%"
    assert format_percentage(None) == "0.0%"


def test_safe_percentage():
    """Assert safe_percentage handles normal division and zero division safely."""
    assert safe_percentage(50, 100) == 50.0
    assert safe_percentage(10, 0) == 0.0
    assert safe_percentage(0, 100) == 0.0
    assert safe_percentage(np.nan, 100) == 0.0
    assert safe_percentage(50, np.nan) == 0.0


# ==============================================================================
# Processed Files Load & Schema Tests
# ==============================================================================
@pytest.mark.parametrize("filename,required_cols", [
    ("customer_transactions.csv", ["invoiceno", "stockcode", "quantity", "unitprice", "customerid", "country", "revenue"]),
    ("rfm_customer_metrics.csv", ["customerid", "recency", "frequency", "monetary", "R_score", "F_score", "M_score", "RFM_score", "segment"]),
    ("customer_clusters.csv", ["customerid", "recency", "frequency", "monetary", "cluster_id", "PCA1", "PCA2"]),
    ("cluster_profiles.csv", ["cluster_id", "customer_count", "customer_percentage", "total_revenue", "revenue_percentage"]),
    ("clustering_metrics.csv", ["k", "inertia", "silhouette_score", "calinski_harabasz", "davies_bouldin"]),
    ("business_segments.csv", ["customerid", "recency", "frequency", "monetary", "cluster_id", "business_segment", "action_category"]),
    ("segment_summary.csv", ["cluster_id", "business_segment", "action_category", "customer_count", "total_revenue"]),
    ("marketing_opportunities.csv", ["cluster_id", "business_segment", "action_category", "recommended_action", "measurement_metric", "caveat"]),
])
def test_processed_files_exist_and_have_columns(filename, required_cols):
    """Assert all 8 precomputed analytical files exist and have required schema."""
    file_path = PROCESSED_DIR / filename
    assert file_path.exists(), f"Missing required file: {file_path}"

    df = pd.read_csv(file_path)
    assert not df.empty, f"File is empty: {file_path}"
    # Normalizing columns for case-insensitive check
    df_norm = df.copy()
    if filename == "customer_transactions.csv":
        df_norm.columns = df_norm.columns.str.lower()
    validate_required_columns(df_norm, required_cols, filename)



# ==============================================================================
# Executive KPI Calculation & Reconciliation Tests
# ==============================================================================
def test_calculate_executive_kpis():
    """Assert calculated KPIs match project ground truth."""
    tx_df = pd.read_csv(PROCESSED_DIR / "customer_transactions.csv")
    cust_df = pd.read_csv(PROCESSED_DIR / "business_segments.csv")

    kpis = calculate_executive_kpis(tx_df, cust_df)

    assert kpis["total_customers"] == 4338
    assert kpis["total_orders"] == 18532
    assert abs(kpis["total_revenue"] - 8887208.89) < 1.0
    assert abs(kpis["average_order_value"] - 479.56) < 1.0
    assert kpis["repeat_customers"] == 2845
    assert abs(kpis["repeat_customer_rate"] - 65.58) < 0.1
    assert abs(kpis["repeat_revenue_rate"] - 93.09) < 0.1


# ==============================================================================
# Customer Filtering Tests
# ==============================================================================
@pytest.fixture
def business_segments_df():
    """Load business segments DataFrame."""
    return pd.read_csv(PROCESSED_DIR / "business_segments.csv")


def test_filter_customers_by_search(business_segments_df):
    """Assert filtering by customer ID search returns exact match."""
    filtered = filter_customers(business_segments_df, search_query="14646")
    assert len(filtered) == 1
    assert filtered["customerid"].iloc[0] == 14646


def test_filter_customers_by_segment(business_segments_df):
    """Assert filtering by business segment subsets rows accurately."""
    filtered = filter_customers(business_segments_df, segments=["High-Value Engaged"])
    assert len(filtered) == 716
    assert (filtered["business_segment"] == "High-Value Engaged").all()


def test_filter_customers_by_action(business_segments_df):
    """Assert filtering by action category works."""
    filtered = filter_customers(business_segments_df, action_categories=["Protect & Grow"])
    assert len(filtered) == 716
    assert (filtered["action_category"] == "Protect & Grow").all()


def test_filter_customers_by_country(business_segments_df):
    """Assert filtering by country subsets accounts correctly."""
    filtered = filter_customers(business_segments_df, countries=["United Kingdom"])
    assert not filtered.empty
    assert (filtered["country"] == "United Kingdom").all()


def test_filter_customers_by_numeric_thresholds(business_segments_df):
    """Assert spend and frequency threshold sliders correctly filter rows."""
    filtered = filter_customers(
        business_segments_df,
        min_monetary=10000.0,
        min_frequency=10,
        max_recency=30,
    )
    assert not filtered.empty
    assert (filtered["monetary"] >= 10000.0).all()
    assert (filtered["frequency"] >= 10).all()
    assert (filtered["recency"] <= 30).all()


def test_filter_customers_empty_result(business_segments_df):
    """Assert filter returning zero rows produces valid empty DataFrame without crashing."""
    filtered = filter_customers(business_segments_df, min_monetary=999999999.0)
    assert filtered.empty
    assert list(filtered.columns) == list(business_segments_df.columns)


# ==============================================================================
# Customer Interpretation Tests
# ==============================================================================
def test_generate_customer_interpretation(business_segments_df):
    """Assert generated customer summary is factual and non-predictive."""
    row = business_segments_df.iloc[0]
    summary = generate_customer_interpretation(row)

    assert isinstance(summary, str)
    assert str(row["customerid"]) in summary
    assert "High-Value Engaged" in summary
    # Assert no forbidden predictive claims
    forbidden = ["will churn", "churn probability", "guaranteed", "predict"]
    for word in forbidden:
        assert word not in summary.lower()


def test_generate_customer_interpretation_edge_case():
    """Assert interpretation handles Series with missing/unknown values gracefully."""
    empty_row = pd.Series({})
    summary = generate_customer_interpretation(empty_row)
    assert "N/A" in summary
    assert "Unknown" in summary



# ==============================================================================
# Business Segment Reconciliation Tests
# ==============================================================================
def test_segment_summary_consistency():
    """Assert segment summary and marketing opportunities share identical segment names."""
    summary_df = pd.read_csv(PROCESSED_DIR / "segment_summary.csv")
    opp_df = pd.read_csv(PROCESSED_DIR / "marketing_opportunities.csv")

    expected_segments = {
        "High-Value Engaged",
        "Established Valuable",
        "Recent Developing",
        "Low-Engagement / Reactivation",
    }
    assert set(summary_df["business_segment"]) == expected_segments
    assert set(opp_df["business_segment"]) == expected_segments
    assert summary_df["customer_count"].sum() == 4338
    assert abs(summary_df["total_revenue"].sum() - 8887208.89) < 1.0
