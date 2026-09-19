"""
Unit and integration tests for Business Segmentation module (src/segmentation.py).
Phase 10 — CustomerLens.
"""

from pathlib import Path
import pytest
import pandas as pd

from src.segmentation import (
    load_cluster_profiles,
    load_customer_clusters,
    validate_cluster_profiles,
    validate_customer_clusters,
    build_segment_mapping,
    assign_business_segments,
    build_segment_summary,
    save_segment_outputs,
    run_segmentation_pipeline,
    EXPECTED_CLUSTER_IDS,
    EXPECTED_TOTAL_CUSTOMERS,
    EXPECTED_TOTAL_REVENUE,
)

PROCESSED_DATA_DIR = Path("data/processed")
CLUSTERS_CSV = PROCESSED_DATA_DIR / "customer_clusters.csv"
PROFILES_CSV = PROCESSED_DATA_DIR / "cluster_profiles.csv"


# ==============================================================================
# Fixtures
# ==============================================================================
@pytest.fixture
def cluster_profiles_df():
    """Load actual cluster profiles for testing."""
    return load_cluster_profiles(PROFILES_CSV)


@pytest.fixture
def customer_clusters_df():
    """Load actual customer clusters for testing."""
    return load_customer_clusters(CLUSTERS_CSV)


@pytest.fixture
def segment_mapping():
    """Return segment mapping dictionary."""
    return build_segment_mapping()


# ==============================================================================
# Ingestion and Validation Tests
# ==============================================================================
def test_load_cluster_profiles_success(cluster_profiles_df):
    """Assert cluster profiles load successfully with 4 rows."""
    assert isinstance(cluster_profiles_df, pd.DataFrame)
    assert len(cluster_profiles_df) == 4
    assert set(cluster_profiles_df["cluster_id"].astype(int)) == EXPECTED_CLUSTER_IDS


def test_load_customer_clusters_success(customer_clusters_df):
    """Assert customer clusters load successfully with exactly 4,338 rows."""
    assert isinstance(customer_clusters_df, pd.DataFrame)
    assert len(customer_clusters_df) == EXPECTED_TOTAL_CUSTOMERS
    assert "cluster_id" in customer_clusters_df.columns


def test_load_missing_files_raises():
    """Assert FileNotFoundError is raised on missing file paths."""
    with pytest.raises(FileNotFoundError):
        load_cluster_profiles(Path("non_existent_profiles.csv"))

    with pytest.raises(FileNotFoundError):
        load_customer_clusters(Path("non_existent_clusters.csv"))


def test_validate_cluster_profiles_missing_column():
    """Assert ValueError when required profile columns are absent."""
    df_invalid = pd.DataFrame({"cluster_id": [0, 1, 2, 3]})
    with pytest.raises(ValueError, match="missing required columns"):
        validate_cluster_profiles(df_invalid)


def test_validate_cluster_profiles_invalid_cluster_ids():
    """Assert ValueError when cluster IDs do not match {0, 1, 2, 3}."""
    df_invalid = pd.DataFrame({
        "cluster_id": [0, 1, 2, 99],
        "customer_count": [1000, 1000, 1000, 1338],
        "customer_percentage": [25, 25, 25, 25],
        "total_revenue": [2e6, 2e6, 2e6, 2887208.89],
        "revenue_percentage": [25, 25, 25, 25],
        "average_recency": [10, 20, 30, 40],
        "median_recency": [10, 20, 30, 40],
        "average_frequency": [2, 3, 4, 5],
        "median_frequency": [2, 3, 4, 5],
        "average_monetary": [100, 200, 300, 400],
        "median_monetary": [100, 200, 300, 400],
    })
    with pytest.raises(ValueError, match="Expected cluster IDs"):
        validate_cluster_profiles(df_invalid)


def test_validate_customer_clusters_missing_column(customer_clusters_df):
    """Assert ValueError when customerid column is missing."""
    df_invalid = customer_clusters_df.drop(columns=["customerid"])
    with pytest.raises(ValueError, match="missing 'customerid' column"):
        validate_customer_clusters(df_invalid)


def test_validate_customer_clusters_null_cluster_id(customer_clusters_df):
    """Assert ValueError if cluster_id contains null values."""
    df_invalid = customer_clusters_df.copy()
    df_invalid.loc[0, "cluster_id"] = None
    with pytest.raises(ValueError, match="contains null cluster_id values"):
        validate_customer_clusters(df_invalid)


# ==============================================================================
# Mapping and Assignment Tests
# ==============================================================================
def test_build_segment_mapping_completeness(segment_mapping):
    """Assert mapping covers all 4 clusters with required attributes."""
    assert set(segment_mapping.keys()) == EXPECTED_CLUSTER_IDS
    for cid in EXPECTED_CLUSTER_IDS:
        mapping_item = segment_mapping[cid]
        assert "business_segment" in mapping_item
        assert "action_category" in mapping_item
        assert "segment_description" in mapping_item
        assert "primary_characteristic" in mapping_item
        assert "business_opportunity" in mapping_item

    # Verify expected names
    assert segment_mapping[3]["business_segment"] == "High-Value Engaged"
    assert segment_mapping[3]["action_category"] == "Protect & Grow"
    assert segment_mapping[2]["business_segment"] == "Established Valuable"
    assert segment_mapping[2]["action_category"] == "Nurture"
    assert segment_mapping[0]["business_segment"] == "Recent Developing"
    assert segment_mapping[0]["action_category"] == "Develop"
    assert segment_mapping[1]["business_segment"] == "Low-Engagement / Reactivation"
    assert segment_mapping[1]["action_category"] == "Reactivate"


def test_assign_business_segments_success(customer_clusters_df, segment_mapping):
    """Assert segments are properly assigned to all 4,338 customer records."""
    df_assigned = assign_business_segments(customer_clusters_df, segment_mapping)

    assert len(df_assigned) == EXPECTED_TOTAL_CUSTOMERS
    assert "business_segment" in df_assigned.columns
    assert "action_category" in df_assigned.columns
    assert "segment_description" in df_assigned.columns

    # No unknown or missing business segments
    assert not df_assigned["business_segment"].isnull().any()
    assert (df_assigned["business_segment"] != "Unknown").all()
    assert set(df_assigned["business_segment"].unique()) == {
        "High-Value Engaged",
        "Established Valuable",
        "Recent Developing",
        "Low-Engagement / Reactivation",
    }


def test_assign_business_segments_preserves_analytical_columns(customer_clusters_df):
    """Assert all pre-existing analytical columns are preserved."""
    df_assigned = assign_business_segments(customer_clusters_df)
    original_cols = customer_clusters_df.columns
    for col in original_cols:
        assert col in df_assigned.columns


def test_assign_business_segments_deterministic(customer_clusters_df):
    """Assert multiple assignment runs yield identical results."""
    df1 = assign_business_segments(customer_clusters_df)
    df2 = assign_business_segments(customer_clusters_df)
    pd.testing.assert_frame_equal(df1, df2)


# ==============================================================================
# Segment Summary & Reconciliation Tests
# ==============================================================================
def test_build_segment_summary_schema(cluster_profiles_df):
    """Assert segment summary contains all expected business columns."""
    summary_df = build_segment_summary(cluster_profiles_df)

    assert len(summary_df) == 4
    expected_cols = [
        "cluster_id",
        "business_segment",
        "action_category",
        "customer_count",
        "customer_percentage",
        "total_revenue",
        "revenue_percentage",
        "primary_characteristic",
        "business_opportunity",
    ]
    for col in expected_cols:
        assert col in summary_df.columns


def test_segment_summary_customer_count_reconciliation(cluster_profiles_df):
    """Assert customer counts reconcile across clusters and sum to exactly 4,338."""
    summary_df = build_segment_summary(cluster_profiles_df)
    counts = dict(zip(summary_df["cluster_id"], summary_df["customer_count"]))

    assert counts[0] == 834
    assert counts[1] == 1618
    assert counts[2] == 1170
    assert counts[3] == 716
    assert summary_df["customer_count"].sum() == EXPECTED_TOTAL_CUSTOMERS


def test_segment_summary_revenue_reconciliation(cluster_profiles_df):
    """Assert total revenue reconciles across clusters to £8,887,208.89."""
    summary_df = build_segment_summary(cluster_profiles_df)
    revs = dict(zip(summary_df["cluster_id"], summary_df["total_revenue"]))

    assert abs(revs[0] - 465608.17) < 0.10
    assert abs(revs[1] - 547770.00) < 0.10
    assert abs(revs[2] - 2092321.70) < 0.10
    assert abs(revs[3] - 5781509.02) < 0.10
    assert abs(summary_df["total_revenue"].sum() - EXPECTED_TOTAL_REVENUE) < 1.0


def test_segment_summary_percentages_sum_to_100(cluster_profiles_df):
    """Assert customer and revenue percentage totals sum to ~100%."""
    summary_df = build_segment_summary(cluster_profiles_df)
    assert pytest.approx(summary_df["customer_percentage"].sum(), 0.1) == 100.0
    assert pytest.approx(summary_df["revenue_percentage"].sum(), 0.1) == 100.0


# ==============================================================================
# Pipeline & Persistence Tests
# ==============================================================================
def test_save_segment_outputs(tmp_path, customer_clusters_df, cluster_profiles_df):
    """Assert outputs are saved to disk and readable."""
    business_df = assign_business_segments(customer_clusters_df)
    summary_df = build_segment_summary(cluster_profiles_df)

    p1, p2 = save_segment_outputs(business_df, summary_df, output_dir=tmp_path)

    assert p1.exists()
    assert p2.exists()

    loaded_b = pd.read_csv(p1)
    loaded_s = pd.read_csv(p2)
    assert len(loaded_b) == EXPECTED_TOTAL_CUSTOMERS
    assert len(loaded_s) == 4


def test_run_segmentation_pipeline_end_to_end(tmp_path):
    """Assert full segmentation pipeline runs cleanly with custom output directory."""
    b_df, s_df = run_segmentation_pipeline(output_dir=tmp_path)
    assert len(b_df) == EXPECTED_TOTAL_CUSTOMERS
    assert len(s_df) == 4
    assert (tmp_path / "business_segments.csv").exists()
    assert (tmp_path / "segment_summary.csv").exists()
