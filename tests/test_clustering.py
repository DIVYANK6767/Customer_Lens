"""Test suite for Phase 9 Customer Segmentation via K-Means Clustering.

Verifies RFM data loading, transformation stability, feature scaling,
K-evaluation metrics (Inertia, Silhouette), deterministic clustering,
cluster profile conservation, and synthetic edge cases.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans

from src.clustering import (
    CLUSTERING_FEATURE_NAMES,
    DEFAULT_CLUSTERS_OUTPUT,
    DEFAULT_METRICS_OUTPUT,
    DEFAULT_PROFILES_OUTPUT,
    DEFAULT_RFM_INPUT,
    SELECTED_K,
    evaluate_k_values,
    fit_kmeans,
    generate_cluster_assignments,
    load_rfm_data,
    prepare_features,
    profile_clusters,
    save_clustering_outputs,
    scale_features,
    select_k,
    transform_features,
    validate_clustering_data,
)
from src.rfm import EXPECTED_CUSTOMERS, EXPECTED_TOTAL_REVENUE


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rfm_data() -> pd.DataFrame:
    """Load the validated customer RFM dataset."""
    return load_rfm_data(DEFAULT_RFM_INPUT)


@pytest.fixture(scope="module")
def prepared_features(rfm_data: pd.DataFrame) -> pd.DataFrame:
    """Extract raw clustering features."""
    return prepare_features(rfm_data)


@pytest.fixture(scope="module")
def transformed_features(prepared_features: pd.DataFrame) -> pd.DataFrame:
    """Apply log1p transformation."""
    return transform_features(prepared_features)


@pytest.fixture(scope="module")
def scaled_features(transformed_features: pd.DataFrame) -> np.ndarray:
    """Scale features with StandardScaler."""
    X_scaled, _ = scale_features(transformed_features)
    return X_scaled


@pytest.fixture(scope="module")
def fitted_model(scaled_features: np.ndarray) -> KMeans:
    """Fit default K-Means model."""
    return fit_kmeans(scaled_features, k=SELECTED_K, random_state=42)


@pytest.fixture(scope="module")
def clustered_customers(
    rfm_data: pd.DataFrame, fitted_model: KMeans, scaled_features: np.ndarray
) -> pd.DataFrame:
    """Assign cluster IDs to customer records."""
    return generate_cluster_assignments(rfm_data, fitted_model, scaled_features)


@pytest.fixture(scope="module")
def cluster_profiles_df(clustered_customers: pd.DataFrame) -> pd.DataFrame:
    """Generate cluster summary profiles."""
    return profile_clusters(clustered_customers)


@pytest.fixture
def small_synthetic_rfm() -> pd.DataFrame:
    """Minimal synthetic RFM dataset for isolated testing."""
    return pd.DataFrame({
        "customerid": ["1", "2", "3", "4", "5", "6"],
        "recency": [5, 10, 50, 60, 200, 250],
        "frequency": [10, 8, 3, 2, 1, 1],
        "monetary": [2000.0, 1500.0, 400.0, 300.0, 50.0, 40.0],
        "R_score": [5, 5, 3, 3, 1, 1],
        "F_score": [4, 4, 2, 2, 1, 1],
        "M_score": [5, 5, 3, 3, 1, 1],
        "RFM_score": ["545", "545", "323", "323", "111", "111"],
        "segment": ["Champions", "Champions", "Need Attention", "Need Attention", "Lost", "Lost"],
        "country": ["United Kingdom"] * 6,
    })


# -----------------------------------------------------------------------------
# Required 20 Test Cases
# -----------------------------------------------------------------------------

def test_01_rfm_input_loads_correctly(rfm_data: pd.DataFrame):
    """Test 1: RFM input loads correctly with expected row count."""
    assert isinstance(rfm_data, pd.DataFrame)
    assert len(rfm_data) == EXPECTED_CUSTOMERS


def test_02_required_columns_exist(rfm_data: pd.DataFrame):
    """Test 2: Required columns exist in loaded RFM data."""
    required = ["customerid", "recency", "frequency", "monetary"]
    for col in required:
        assert col in rfm_data.columns, f"Missing required column: {col}"


def test_03_no_missing_clustering_features(prepared_features: pd.DataFrame):
    """Test 3: Zero missing values exist in clustering features."""
    assert prepared_features.isna().sum().sum() == 0


def test_04_feature_matrix_row_count(prepared_features: pd.DataFrame):
    """Test 4: Feature matrix has expected row count (4,338)."""
    assert len(prepared_features) == EXPECTED_CUSTOMERS
    assert prepared_features.shape[1] == 3


def test_05_transformation_produces_finite_values(transformed_features: pd.DataFrame):
    """Test 5: Log-transformation produces finite values (no NaN or inf)."""
    assert np.isfinite(transformed_features.values).all()
    assert (transformed_features.values >= 0).all()


def test_06_scaling_produces_finite_values(scaled_features: np.ndarray):
    """Test 6: Feature scaling produces finite values."""
    assert np.isfinite(scaled_features).all()
    assert scaled_features.shape == (EXPECTED_CUSTOMERS, 3)


def test_07_scaled_features_mean_zero_unit_variance(scaled_features: np.ndarray):
    """Test 7: Scaled features have approximately mean = 0 and std = 1."""
    means = np.mean(scaled_features, axis=0)
    stds = np.std(scaled_features, axis=0)
    np.testing.assert_allclose(means, [0.0, 0.0, 0.0], atol=1e-7)
    np.testing.assert_allclose(stds, [1.0, 1.0, 1.0], atol=1e-7)


def test_08_k_evaluation_covers_two_through_ten(scaled_features: np.ndarray):
    """Test 8: K evaluation covers cluster counts 2 through 10."""
    metrics_df = evaluate_k_values(scaled_features, k_range=range(2, 11), random_state=42)
    assert len(metrics_df) == 9
    assert list(metrics_df["k"]) == list(range(2, 11))


def test_09_inertia_is_finite_and_positive(scaled_features: np.ndarray):
    """Test 9: Inertia is strictly positive and finite across evaluated K values."""
    metrics_df = evaluate_k_values(scaled_features, k_range=range(2, 6), random_state=42)
    assert (metrics_df["inertia"] > 0).all()
    assert np.isfinite(metrics_df["inertia"]).all()
    # Inertia must decrease monotonically as K increases
    inertias = list(metrics_df["inertia"])
    for i in range(len(inertias) - 1):
        assert inertias[i] > inertias[i + 1], "Inertia must decrease as K increases"


def test_10_silhouette_score_is_finite(scaled_features: np.ndarray):
    """Test 10: Silhouette score is finite."""
    metrics_df = evaluate_k_values(scaled_features, k_range=range(2, 5), random_state=42)
    assert np.isfinite(metrics_df["silhouette_score"]).all()


def test_11_silhouette_score_in_valid_range(scaled_features: np.ndarray):
    """Test 11: Silhouette score lies strictly between -1 and 1."""
    metrics_df = evaluate_k_values(scaled_features, k_range=range(2, 6), random_state=42)
    assert (metrics_df["silhouette_score"] >= -1.0).all()
    assert (metrics_df["silhouette_score"] <= 1.0).all()


def test_12_final_cluster_count_matches_selected_k(clustered_customers: pd.DataFrame):
    """Test 12: Final cluster count matches selected K (4)."""
    assert clustered_customers["cluster_id"].nunique() == SELECTED_K
    assert set(clustered_customers["cluster_id"].unique()) == set(range(SELECTED_K))


def test_13_every_customer_gets_exactly_one_cluster(clustered_customers: pd.DataFrame):
    """Test 13: Every customer receives exactly one valid cluster ID."""
    assert len(clustered_customers) == EXPECTED_CUSTOMERS
    assert clustered_customers["cluster_id"].isna().sum() == 0


def test_14_customer_ids_remain_unique(clustered_customers: pd.DataFrame):
    """Test 14: Customer IDs remain strictly unique in output."""
    assert clustered_customers["customerid"].nunique() == EXPECTED_CUSTOMERS


def test_15_cluster_profile_counts_sum_to_total(
    cluster_profiles_df: pd.DataFrame, rfm_data: pd.DataFrame
):
    """Test 15: Cluster profile customer counts sum to total customer count."""
    assert cluster_profiles_df["customer_count"].sum() == len(rfm_data)


def test_16_cluster_revenue_sums_to_total_revenue(
    cluster_profiles_df: pd.DataFrame, rfm_data: pd.DataFrame
):
    """Test 16: Cluster revenue sums approximately to total revenue."""
    profile_total = cluster_profiles_df["total_revenue"].sum()
    rfm_total = rfm_data["monetary"].sum()
    assert abs(profile_total - rfm_total) < 0.1
    assert abs(profile_total - EXPECTED_TOTAL_REVENUE) < 0.1


def test_17_cluster_percentages_sum_to_100(cluster_profiles_df: pd.DataFrame):
    """Test 17: Cluster percentages sum approximately to 100%."""
    cust_pct = cluster_profiles_df["customer_percentage"].sum()
    rev_pct = cluster_profiles_df["revenue_percentage"].sum()
    assert abs(cust_pct - 100.0) <= 0.1
    assert abs(rev_pct - 100.0) <= 0.1


def test_18_model_is_deterministic(scaled_features: np.ndarray):
    """Test 18: Model produces identical cluster assignments with random_state=42."""
    model1 = fit_kmeans(scaled_features, k=4, random_state=42)
    model2 = fit_kmeans(scaled_features, k=4, random_state=42)
    labels1 = model1.predict(scaled_features)
    labels2 = model2.predict(scaled_features)
    np.testing.assert_array_equal(labels1, labels2)


def test_19_small_synthetic_dataset_clusters_successfully(
    small_synthetic_rfm: pd.DataFrame,
):
    """Test 19: Small synthetic dataset can be transformed, scaled, and clustered."""
    X_raw = prepare_features(small_synthetic_rfm)
    X_log = transform_features(X_raw)
    X_scaled, _ = scale_features(X_log)
    model = fit_kmeans(X_scaled, k=2, random_state=42)
    assigned = generate_cluster_assignments(small_synthetic_rfm, model, X_scaled)
    assert len(assigned) == 6
    assert assigned["cluster_id"].nunique() == 2
    profile = profile_clusters(assigned)
    assert len(profile) == 2
    assert profile["customer_count"].sum() == 6


def test_20_invalid_features_rejected():
    """Test 20: Missing or invalid features raise ValueError."""
    # Missing required column
    bad_df_col = pd.DataFrame({"customerid": ["1"], "recency": [10]})
    with pytest.raises(ValueError, match="Missing required RFM columns"):
        validate_clustering_data(bad_df_col)

    # Negative recency
    bad_df_neg = pd.DataFrame({
        "customerid": ["1"],
        "recency": [-5],
        "frequency": [2],
        "monetary": [100.0],
        "R_score": [1],
        "F_score": [1],
        "M_score": [1],
        "RFM_score": ["111"],
        "segment": ["Lost"],
        "country": ["UK"],
    })
    with pytest.raises(ValueError, match="negative"):
        validate_clustering_data(bad_df_neg)

    # Null customerid
    bad_df_null = pd.DataFrame({
        "customerid": [None],
        "recency": [5],
        "frequency": [2],
        "monetary": [100.0],
        "R_score": [1],
        "F_score": [1],
        "M_score": [1],
        "RFM_score": ["111"],
        "segment": ["Lost"],
        "country": ["UK"],
    })
    with pytest.raises(ValueError, match="null customer IDs"):
        validate_clustering_data(bad_df_null)


# -----------------------------------------------------------------------------
# Additional Helper Tests
# -----------------------------------------------------------------------------

def test_save_clustering_outputs(
    clustered_customers: pd.DataFrame,
    cluster_profiles_df: pd.DataFrame,
    scaled_features: np.ndarray,
    tmp_path: Path,
):
    """Verify save_clustering_outputs writes all three output CSVs."""
    metrics_df = evaluate_k_values(scaled_features, k_range=range(2, 4), random_state=42)
    p_clusters = tmp_path / "test_clusters.csv"
    p_profiles = tmp_path / "test_profiles.csv"
    p_metrics = tmp_path / "test_metrics.csv"

    saved = save_clustering_outputs(
        clustered_customers,
        cluster_profiles_df,
        metrics_df,
        clusters_path=p_clusters,
        profiles_path=p_profiles,
        metrics_path=p_metrics,
    )
    assert saved["customer_clusters"].is_file()
    assert saved["cluster_profiles"].is_file()
    assert saved["clustering_metrics"].is_file()

    loaded_clusters = pd.read_csv(p_clusters)
    assert len(loaded_clusters) == EXPECTED_CUSTOMERS
    assert "cluster_id" in loaded_clusters.columns
