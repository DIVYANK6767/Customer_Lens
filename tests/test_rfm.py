"""Comprehensive test suite for Phase 8 RFM Analysis Layer.

Verifies raw metric computation, structural invariants, scoring monotonicity,
segment assignment determinism, error handling, and synthetic edge cases.
"""

from __future__ import annotations

import decimal
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data_loader import get_project_root
from src.rfm import (
    DEFAULT_INPUT_CSV,
    DEFAULT_OUTPUT_CSV,
    EXPECTED_CUSTOMERS,
    EXPECTED_ORDERS,
    EXPECTED_TOTAL_REVENUE,
    _score_single_metric,
    assign_rfm_segments,
    calculate_rfm,
    calculate_rfm_scores,
    load_customer_transactions,
    save_rfm_dataset,
    summarize_rfm,
    validate_rfm,
)


# -----------------------------------------------------------------------------
# Test Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def source_transactions() -> pd.DataFrame:
    """Load the full validated customer transaction dataset."""
    return load_customer_transactions(DEFAULT_INPUT_CSV)


@pytest.fixture(scope="module")
def rfm_dataset(source_transactions: pd.DataFrame) -> pd.DataFrame:
    """Compute customer-level raw RFM metrics."""
    return calculate_rfm(source_transactions)


@pytest.fixture(scope="module")
def scored_rfm_dataset(rfm_dataset: pd.DataFrame) -> pd.DataFrame:
    """Compute scored and segmented RFM metrics."""
    scored = calculate_rfm_scores(rfm_dataset)
    return assign_rfm_segments(scored)


@pytest.fixture
def small_synthetic_transactions() -> pd.DataFrame:
    """Create a minimal synthetic transaction DataFrame for isolated testing."""
    data = {
        "InvoiceNo": ["1001", "1002", "1003", "1004", "1005"],
        "InvoiceDate": [
            "2021-01-01 10:00:00",
            "2021-01-02 11:00:00",
            "2021-01-05 12:00:00",
            "2021-01-08 14:00:00",
            "2021-01-10 15:00:00",
        ],
        "CustomerID": ["C1", "C1", "C2", "C3", "C3"],
        "Revenue": [100.0, 150.0, 50.0, 300.0, 200.0],
        "Quantity": [10, 15, 5, 30, 20],
        "UnitPrice": [10.0, 10.0, 10.0, 10.0, 10.0],
        "Country": ["United Kingdom", "United Kingdom", "France", "Germany", "Germany"],
    }
    return pd.DataFrame(data)


# -----------------------------------------------------------------------------
# Required 22 Invariant and Functional Tests
# -----------------------------------------------------------------------------

def test_01_rfm_output_has_one_row_per_customer(rfm_dataset: pd.DataFrame):
    """Test 1: RFM output has exactly one row per customer."""
    assert len(rfm_dataset) == rfm_dataset["customerid"].nunique()


def test_02_customer_count_matches_validated_baseline(rfm_dataset: pd.DataFrame):
    """Test 2: Customer count matches validated value of 4,338."""
    assert len(rfm_dataset) == EXPECTED_CUSTOMERS


def test_03_no_duplicate_customer_ids(rfm_dataset: pd.DataFrame):
    """Test 3: No duplicate Customer IDs exist in RFM dataset."""
    duplicates = rfm_dataset["customerid"].duplicated().sum()
    assert duplicates == 0, f"Found {duplicates} duplicate customer IDs."


def test_04_no_null_customer_ids(rfm_dataset: pd.DataFrame):
    """Test 4: CustomerID contains zero null values."""
    nulls = rfm_dataset["customerid"].isna().sum()
    assert nulls == 0, f"Found {nulls} null customer IDs."


def test_05_recency_is_non_negative(rfm_dataset: pd.DataFrame):
    """Test 5: Recency is strictly non-negative (>= 0)."""
    assert (rfm_dataset["recency"] >= 0).all()
    assert rfm_dataset["recency"].min() >= 0


def test_06_frequency_is_at_least_one(rfm_dataset: pd.DataFrame):
    """Test 6: Frequency is positive integer (>= 1)."""
    assert (rfm_dataset["frequency"] >= 1).all()
    assert (rfm_dataset["frequency"] % 1 == 0).all()


def test_07_monetary_is_strictly_positive(rfm_dataset: pd.DataFrame):
    """Test 7: Monetary spend is strictly positive (> 0)."""
    assert (rfm_dataset["monetary"] > 0).all()
    assert rfm_dataset["monetary"].min() > 0


def test_08_total_monetary_matches_validated_baseline(rfm_dataset: pd.DataFrame):
    """Test 8: Sum of monetary equals Â£8,887,208.89."""
    total_rev = round(float(rfm_dataset["monetary"].sum()), 2)
    assert total_rev == EXPECTED_TOTAL_REVENUE


def test_09_total_frequency_matches_validated_baseline(rfm_dataset: pd.DataFrame):
    """Test 9: Sum of frequency equals 18,532 completed orders."""
    total_orders = int(rfm_dataset["frequency"].sum())
    assert total_orders == EXPECTED_ORDERS


def test_10_maximum_last_purchase_date_matches_source(
    rfm_dataset: pd.DataFrame, source_transactions: pd.DataFrame
):
    """Test 10: Maximum last purchase date matches source transaction dataset."""
    source_max = pd.to_datetime(source_transactions["InvoiceDate"]).max()
    rfm_max = pd.to_datetime(rfm_dataset["last_purchase_date"]).max()
    assert rfm_max == source_max


def test_11_reference_date_calculation_is_correct(source_transactions: pd.DataFrame):
    """Test 11: Reference date calculation equals max(InvoiceDate) + 1 day."""
    max_date = pd.to_datetime(source_transactions["InvoiceDate"]).max()
    expected_ref = max_date + pd.Timedelta(days=1)

    # Calculate with default reference date
    rfm = calculate_rfm(source_transactions)
    # The customer with purchase at max_date should have recency == 1
    most_recent_cust = source_transactions.loc[
        source_transactions["InvoiceDate"] == max_date, "CustomerID"
    ].iloc[0]
    cust_recency = rfm.loc[rfm["customerid"] == most_recent_cust, "recency"].iloc[0]
    assert cust_recency == 1


def test_12_rfm_scores_in_valid_range(scored_rfm_dataset: pd.DataFrame):
    """Test 12: RFM scores are in valid integer range [1, 5]."""
    for col in ["R_score", "F_score", "M_score"]:
        assert (scored_rfm_dataset[col] >= 1).all(), f"{col} has values < 1"
        assert (scored_rfm_dataset[col] <= 5).all(), f"{col} has values > 5"


def test_13_r_score_direction_is_correct(scored_rfm_dataset: pd.DataFrame):
    """Test 13: R_score direction: lower recency (more recent) -> higher score."""
    group_recency = scored_rfm_dataset.groupby("R_score")["recency"].mean()
    # Average recency must decrease strictly as R_score increases
    for s in range(1, 5):
        assert group_recency[s] > group_recency[s + 1], (
            f"Expected R_score {s} to have higher mean recency than {s + 1}."
        )


def test_14_f_score_direction_is_correct(scored_rfm_dataset: pd.DataFrame):
    """Test 14: F_score direction: higher frequency -> higher score."""
    group_freq = scored_rfm_dataset.groupby("F_score")["frequency"].mean()
    scores = sorted(group_freq.index)
    for i in range(len(scores) - 1):
        s_curr = scores[i]
        s_next = scores[i + 1]
        assert group_freq[s_curr] < group_freq[s_next], (
            f"Expected F_score {s_next} to have higher mean frequency than {s_curr}."
        )


def test_15_m_score_direction_is_correct(scored_rfm_dataset: pd.DataFrame):
    """Test 15: M_score direction: higher monetary spend -> higher score."""
    group_monetary = scored_rfm_dataset.groupby("M_score")["monetary"].mean()
    for s in range(1, 5):
        assert group_monetary[s] < group_monetary[s + 1], (
            f"Expected M_score {s + 1} to have higher mean monetary than {s}."
        )


def test_16_rfm_score_string_construction(scored_rfm_dataset: pd.DataFrame):
    """Test 16: RFM score string is constructed correctly as R+F+M string."""
    expected_str = (
        scored_rfm_dataset["R_score"].astype(str)
        + scored_rfm_dataset["F_score"].astype(str)
        + scored_rfm_dataset["M_score"].astype(str)
    )
    assert (scored_rfm_dataset["RFM_score"] == expected_str).all()


def test_17_segment_assignment_is_deterministic(scored_rfm_dataset: pd.DataFrame):
    """Test 17: Segment assignment is deterministic and covers 100% of customers."""
    assert "segment" in scored_rfm_dataset.columns
    assert scored_rfm_dataset["segment"].isna().sum() == 0
    assert (scored_rfm_dataset["segment"] == "Other").sum() == 0

    # Repeat assignment on identical input produces identical output
    run2 = assign_rfm_segments(scored_rfm_dataset)
    assert (scored_rfm_dataset["segment"] == run2["segment"]).all()


def test_18_edge_case_tied_quantiles_does_not_crash():
    """Test 18: Metric series with heavily tied quantile boundaries does not crash."""
    # Series with 90% identical values
    tied_series = pd.Series([1] * 90 + [2, 3, 4, 5, 10, 20, 30, 40, 50, 100])
    scores = _score_single_metric(tied_series, num_scores=5, ascending=True)
    assert len(scores) == len(tied_series)
    assert (scores >= 1).all()
    assert (scores <= 5).all()

    # Series with 100% identical values
    identical_series = pd.Series([10] * 50)
    scores_ident = _score_single_metric(identical_series, num_scores=5, ascending=True)
    assert len(scores_ident) == 50
    assert (scores_ident == 1).all()


def test_19_edge_case_small_synthetic_dataset_works(
    small_synthetic_transactions: pd.DataFrame,
):
    """Test 19: RFM pipeline operates correctly on a small synthetic dataset."""
    rfm = calculate_rfm(small_synthetic_transactions)
    assert len(rfm) == 3  # C1, C2, C3
    assert set(rfm["customerid"]) == {"C1", "C2", "C3"}

    # C1 has 2 orders, Â£250
    c1 = rfm.loc[rfm["customerid"] == "C1"].iloc[0]
    assert c1["frequency"] == 2
    assert c1["monetary"] == 250.0

    scored = calculate_rfm_scores(rfm)
    assert len(scored) == 3
    segmented = assign_rfm_segments(scored)
    assert len(segmented) == 3
    assert segmented["segment"].isna().sum() == 0


def test_20_missing_customer_id_is_rejected():
    """Test 20: Missing/Null CustomerID in transaction data raises ValueError."""
    bad_df = pd.DataFrame({
        "InvoiceNo": ["1001", "1002"],
        "InvoiceDate": ["2021-01-01", "2021-01-02"],
        "CustomerID": ["C1", None],
        "Revenue": [10.0, 20.0],
        "Quantity": [1, 2],
        "UnitPrice": [10.0, 10.0],
        "Country": ["United Kingdom", "United Kingdom"],
    })
    with pytest.raises(ValueError, match="NULL CustomerID"):
        calculate_rfm(bad_df)


def test_21_negative_recency_is_rejected():
    """Test 21: Negative recency in RFM DataFrame raises ValueError during validation."""
    bad_rfm = pd.DataFrame({
        "customerid": ["C1", "C2"],
        "recency": [-5, 10],  # Negative recency
        "frequency": [1, 2],
        "monetary": [50.0, 100.0],
    })
    with pytest.raises(ValueError, match="negative recency"):
        validate_rfm(bad_rfm)


def test_22_zero_or_negative_monetary_is_rejected():
    """Test 22: Zero or negative monetary spend raises ValueError during validation."""
    bad_rfm_zero = pd.DataFrame({
        "customerid": ["C1", "C2"],
        "recency": [5, 10],
        "frequency": [1, 2],
        "monetary": [0.0, 100.0],  # Zero monetary
    })
    with pytest.raises(ValueError, match="monetary <= 0"):
        validate_rfm(bad_rfm_zero)

    bad_rfm_neg = pd.DataFrame({
        "customerid": ["C1", "C2"],
        "recency": [5, 10],
        "frequency": [1, 2],
        "monetary": [-25.0, 100.0],  # Negative monetary
    })
    with pytest.raises(ValueError, match="monetary <= 0"):
        validate_rfm(bad_rfm_neg)


# -----------------------------------------------------------------------------
# Additional Helper & Summary Tests
# -----------------------------------------------------------------------------

def test_summarize_rfm_scorecard(scored_rfm_dataset: pd.DataFrame):
    """Verify summarize_rfm computes accurate segment-level metrics."""
    summary = summarize_rfm(scored_rfm_dataset)
    assert len(summary) == 8  # 8 analytical segments
    assert summary["customer_count"].sum() == EXPECTED_CUSTOMERS
    assert round(float(summary["total_revenue"].sum()), 2) == EXPECTED_TOTAL_REVENUE
    assert round(float(summary["pct_customers"].sum()), 1) == 100.0
    assert round(float(summary["pct_revenue"].sum()), 1) == 100.0


def test_save_rfm_dataset_writes_file(scored_rfm_dataset: pd.DataFrame, tmp_path: Path):
    """Verify save_rfm_dataset successfully persists the dataset."""
    dest = tmp_path / "test_rfm_metrics.csv"
    res = save_rfm_dataset(scored_rfm_dataset, dest)
    assert res.is_file()
    loaded = pd.read_csv(res)
    assert len(loaded) == EXPECTED_CUSTOMERS
    assert len(loaded.columns) == 12
