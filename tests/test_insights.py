"""
Unit and integration tests for Business Insights module (src/insights.py).
Phase 10 — CustomerLens.
"""

from pathlib import Path
import pytest
import pandas as pd

from src.segmentation import load_cluster_profiles, build_segment_summary
from src.insights import (
    calculate_segment_contribution,
    identify_segment_characteristics,
    build_opportunity_table,
    generate_segment_insights,
    validate_business_insights,
    save_insights_outputs,
    run_insights_pipeline,
    FORBIDDEN_PREDICTIVE_TERMS,
    REQUIRED_OPPORTUNITY_COLUMNS,
)

PROCESSED_DATA_DIR = Path("data/processed")
PROFILES_CSV = PROCESSED_DATA_DIR / "cluster_profiles.csv"


# ==============================================================================
# Fixtures
# ==============================================================================
@pytest.fixture
def segment_summary_df():
    """Load segment summary for testing."""
    profiles_df = load_cluster_profiles(PROFILES_CSV)
    return build_segment_summary(profiles_df)


@pytest.fixture
def opportunities_df(segment_summary_df):
    """Generate opportunities DataFrame for testing."""
    return build_opportunity_table(segment_summary_df)


# ==============================================================================
# Contribution & Characteristic Tests
# ==============================================================================
def test_calculate_segment_contribution(segment_summary_df):
    """Assert revenue concentration ratios are correctly computed."""
    contrib_df = calculate_segment_contribution(segment_summary_df)
    assert "revenue_concentration_ratio" in contrib_df.columns

    # Cluster 3: 65.05% revenue / 16.51% customers ~ 3.94x
    r3 = contrib_df.loc[contrib_df["cluster_id"] == 3, "revenue_concentration_ratio"].iloc[0]
    assert abs(r3 - 3.94) <= 0.05

    # Cluster 1: 6.16% revenue / 37.30% customers ~ 0.17x
    r1 = contrib_df.loc[contrib_df["cluster_id"] == 1, "revenue_concentration_ratio"].iloc[0]
    assert abs(r1 - 0.17) <= 0.05


def test_identify_segment_characteristics(segment_summary_df):
    """Assert descriptive characteristics are generated for all 4 clusters."""
    chars = identify_segment_characteristics(segment_summary_df)
    assert len(chars) == 4
    for cid in [0, 1, 2, 3]:
        assert cid in chars
        assert len(chars[cid]) > 20
        assert "Cluster" in chars[cid]


# ==============================================================================
# Marketing Opportunities & Hypotheses Tests
# ==============================================================================
def test_build_opportunity_table_columns(opportunities_df):
    """Assert all required columns are present in opportunities table."""
    for col in REQUIRED_OPPORTUNITY_COLUMNS:
        assert col in opportunities_df.columns


def test_every_cluster_has_opportunity_and_action(opportunities_df):
    """Assert every cluster has non-empty opportunities, actions, metrics, and caveats."""
    assert len(opportunities_df) == 4
    assert set(opportunities_df["cluster_id"]) == {0, 1, 2, 3}

    for _, row in opportunities_df.iterrows():
        assert len(str(row["business_opportunity"]).strip()) > 15
        assert len(str(row["recommended_action"]).strip()) > 15
        assert len(str(row["measurement_metric"]).strip()) > 15
        assert len(str(row["caveat"]).strip()) > 15


def test_no_forbidden_predictive_language(opportunities_df):
    """Strictly assert no unsupported predictive claims exist in opportunities text."""
    for col in ["business_opportunity", "recommended_action", "caveat"]:
        for text in opportunities_df[col].astype(str):
            lower_text = text.lower()
            for forbidden in FORBIDDEN_PREDICTIVE_TERMS:
                assert forbidden not in lower_text, (
                    f"Forbidden predictive term '{forbidden}' found in column '{col}'"
                )


def test_validate_business_insights_catches_forbidden_term():
    """Assert validate_business_insights raises ValueError on forbidden predictive terms."""
    invalid_df = pd.DataFrame({
        "cluster_id": [0],
        "business_segment": ["Recent Developing"],
        "action_category": ["Develop"],
        "customer_count": [834],
        "customer_percentage": [19.23],
        "revenue": [465608.17],
        "revenue_percentage": [5.24],
        "primary_characteristic": ["Recent"],
        "business_opportunity": ["Customers will churn without intervention"],
        "recommended_action": ["Action"],
        "measurement_metric": ["Metric"],
        "caveat": ["Caveat"],
    })
    with pytest.raises(ValueError, match="Forbidden predictive term"):
        validate_business_insights(invalid_df)


def test_no_nulls_in_opportunities(opportunities_df):
    """Assert zero null or NaN values across all fields."""
    assert not opportunities_df.isnull().any().any()


def test_generate_segment_insights_structure(segment_summary_df):
    """Assert generate_segment_insights produces a list of 4 structured dictionaries."""
    insights = generate_segment_insights(segment_summary_df)
    assert isinstance(insights, list)
    assert len(insights) == 4
    for item in insights:
        assert isinstance(item, dict)
        assert "cluster_id" in item
        assert "business_segment" in item
        assert "measurement_metric" in item


def test_deterministic_insights_generation(segment_summary_df):
    """Assert multiple executions generate identical opportunity tables."""
    opp1 = build_opportunity_table(segment_summary_df)
    opp2 = build_opportunity_table(segment_summary_df)
    pd.testing.assert_frame_equal(opp1, opp2)


# ==============================================================================
# Pipeline & Persistence Tests
# ==============================================================================
def test_save_insights_outputs(tmp_path, opportunities_df):
    """Assert marketing opportunities CSV is properly written to disk."""
    out_file = save_insights_outputs(opportunities_df, output_dir=tmp_path)
    assert out_file.exists()
    assert out_file.name == "marketing_opportunities.csv"

    loaded = pd.read_csv(out_file)
    assert len(loaded) == 4
    assert set(loaded["cluster_id"]) == {0, 1, 2, 3}


def test_run_insights_pipeline_end_to_end(tmp_path, segment_summary_df):
    """Assert insights pipeline executes end-to-end with temporary summary path."""
    summary_path = tmp_path / "segment_summary.csv"
    segment_summary_df.to_csv(summary_path, index=False)

    opp_df = run_insights_pipeline(summary_path=summary_path, output_dir=tmp_path)
    assert len(opp_df) == 4
    assert (tmp_path / "marketing_opportunities.csv").exists()
