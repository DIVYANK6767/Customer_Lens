"""
CustomerLens — Business Segmentation Layer (Phase 10).

This module bridges quantitative unsupervised learning with strategic marketing
analytics, mapping K-Means cluster IDs (0, 1, 2, 3) to descriptive business personas
and operational action categories without making unsupported predictive claims.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Base project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLUSTERS_PATH = PROJECT_ROOT / "data" / "processed" / "customer_clusters.csv"
DEFAULT_PROFILES_PATH = PROJECT_ROOT / "data" / "processed" / "cluster_profiles.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# Expected invariants
EXPECTED_CLUSTER_IDS = {0, 1, 2, 3}
EXPECTED_TOTAL_CUSTOMERS = 4338
EXPECTED_TOTAL_REVENUE = 8887208.89

REQUIRED_PROFILE_COLUMNS = [
    "cluster_id",
    "customer_count",
    "customer_percentage",
    "total_revenue",
    "revenue_percentage",
    "average_recency",
    "median_recency",
    "average_frequency",
    "median_frequency",
    "average_monetary",
    "median_monetary",
]

REQUIRED_CLUSTER_COLUMNS = [
    "customerid",
    "recency",
    "frequency",
    "monetary",
    "cluster_id",
]


def build_segment_mapping() -> Dict[int, Dict[str, str]]:
    """
    Build transparent, deterministic mapping dictionary from cluster_id to business metadata.

    Mapping Rationale:
      - Cluster 3: High-Value Engaged (Protect & Grow)
        Very recent purchases, highest frequency, highest monetary contribution (65.05% of turnover).
      - Cluster 2: Established Valuable (Nurture)
        Established repeat purchasing, moderate recency, substantial monetary contribution (23.54% of turnover).
      - Cluster 0: Recent Developing (Develop)
        Recent activity, early-stage purchase cadence, lower monetary contribution (5.24% of turnover).
      - Cluster 1: Low-Engagement / Reactivation (Reactivate)
        Prolonged inactivity, single-purchase concentration, minimal spend (6.16% of turnover).

    Returns:
        Dict[int, Dict[str, str]]: Structured dictionary keyed by cluster_id.
    """
    return {
        3: {
            "business_segment": "High-Value Engaged",
            "action_category": "Protect & Grow",
            "segment_priority": "Protect & Grow",
            "segment_description": (
                "Customers with very recent purchasing activity, high purchase frequency, "
                "and the highest monetary contribution."
            ),
            "primary_characteristic": (
                "Very recent purchases, highest order frequency, and highest monetary "
                "contribution (65.05% of total revenue)."
            ),
            "business_opportunity": (
                "VIP retention, dedicated B2B account support, proactive restock scheduling, "
                "and cross-category expansion."
            ),
        },
        2: {
            "business_segment": "Established Valuable",
            "action_category": "Nurture",
            "segment_priority": "Nurture",
            "segment_description": (
                "Customers with established repeat purchasing behavior and materially higher "
                "monetary contribution than the lower-value groups."
            ),
            "primary_characteristic": (
                "Established repeat purchasing with moderate recency and strong monetary "
                "contribution (23.54% of total revenue)."
            ),
            "business_opportunity": (
                "Order frequency acceleration, tiered loyalty incentives, and basket threshold promotions."
            ),
        },
        0: {
            "business_segment": "Recent Developing",
            "action_category": "Develop",
            "segment_priority": "Develop",
            "segment_description": (
                "Customers with recent purchasing activity but comparatively lower purchase "
                "frequency and monetary contribution."
            ),
            "primary_characteristic": (
                "Recent initial engagement with lower order frequency and modest monetary "
                "contribution (5.24% of total revenue)."
            ),
            "business_opportunity": (
                "Second-purchase conversion, targeted post-onboarding nurture sequences, and category discovery."
            ),
        },
        1: {
            "business_segment": "Low-Engagement / Reactivation",
            "action_category": "Reactivate",
            "segment_priority": "Reactivate",
            "segment_description": (
                "Customers with relatively high recency and low frequency and monetary contribution, "
                "indicating lower recent engagement relative to the other segments."
            ),
            "primary_characteristic": (
                "Prolonged inactivity with low single-purchase frequency and minimal monetary spend "
                "(6.16% of total revenue)."
            ),
            "business_opportunity": (
                "Low-cost digital reactivation testing, clearance promotions, and email cadence optimization."
            ),
        },
    }


def load_cluster_profiles(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load cluster profiles CSV file.

    Args:
        file_path: Path to cluster profiles CSV.

    Returns:
        pd.DataFrame: Loaded cluster profiles.
    """
    path = file_path or DEFAULT_PROFILES_PATH
    if not path.exists():
        raise FileNotFoundError(f"Cluster profiles file not found at: {path}")
    df = pd.read_csv(path)
    validate_cluster_profiles(df)
    return df


def load_customer_clusters(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load customer clusters CSV file.

    Args:
        file_path: Path to customer clusters CSV.

    Returns:
        pd.DataFrame: Loaded customer clusters.
    """
    path = file_path or DEFAULT_CLUSTERS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Customer clusters file not found at: {path}")
    df = pd.read_csv(path)
    validate_customer_clusters(df)
    return df


def validate_cluster_profiles(profiles_df: pd.DataFrame) -> None:
    """
    Validate schema and mathematical integrity of cluster profiles.

    Args:
        profiles_df: Cluster profile DataFrame.
    """
    if profiles_df.empty:
        raise ValueError("Cluster profiles DataFrame is empty.")

    missing = [c for c in REQUIRED_PROFILE_COLUMNS if c not in profiles_df.columns]
    if missing:
        raise ValueError(f"Cluster profiles missing required columns: {missing}")

    cluster_ids = set(profiles_df["cluster_id"].dropna().astype(int).unique())
    if cluster_ids != EXPECTED_CLUSTER_IDS:
        raise ValueError(f"Expected cluster IDs {EXPECTED_CLUSTER_IDS}, found {cluster_ids}")

    total_customers = int(profiles_df["customer_count"].sum())
    if total_customers != EXPECTED_TOTAL_CUSTOMERS:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL_CUSTOMERS} total customers, found {total_customers}"
        )

    total_rev = float(profiles_df["total_revenue"].sum())
    if abs(total_rev - EXPECTED_TOTAL_REVENUE) > 1.0:
        raise ValueError(
            f"Expected £{EXPECTED_TOTAL_REVENUE:.2f} total revenue, found £{total_rev:.2f}"
        )


def validate_customer_clusters(clusters_df: pd.DataFrame) -> None:
    """
    Validate schema and integrity of customer clusters.

    Args:
        clusters_df: Customer clusters DataFrame.
    """
    if clusters_df.empty:
        raise ValueError("Customer clusters DataFrame is empty.")

    # Normalize check for customerid (case-insensitive check for presence)
    cols_lower = [c.lower() for c in clusters_df.columns]
    if "customerid" not in cols_lower:
        raise ValueError("Customer clusters missing 'customerid' column.")

    missing = [c for c in REQUIRED_CLUSTER_COLUMNS if c.lower() not in cols_lower]
    if missing:
        raise ValueError(f"Customer clusters missing required columns: {missing}")

    if clusters_df["cluster_id"].isnull().any():
        raise ValueError("Customer clusters contains null cluster_id values.")

    cluster_ids = set(clusters_df["cluster_id"].astype(int).unique())
    if cluster_ids != EXPECTED_CLUSTER_IDS:
        raise ValueError(f"Expected cluster IDs {EXPECTED_CLUSTER_IDS}, found {cluster_ids}")

    if len(clusters_df) != EXPECTED_TOTAL_CUSTOMERS:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL_CUSTOMERS} rows, found {len(clusters_df)}"
        )


def assign_business_segments(
    clusters_df: pd.DataFrame,
    mapping: Optional[Dict[int, Dict[str, str]]] = None,
) -> pd.DataFrame:
    """
    Assign business segment names, action categories, and descriptions to customer records.

    Preserves all existing analytical columns.

    Args:
        clusters_df: Customer-level clusters DataFrame.
        mapping: Optional custom segment mapping dictionary.

    Returns:
        pd.DataFrame: Customer DataFrame with business segment metadata added.
    """
    validate_customer_clusters(clusters_df)
    map_dict = mapping or build_segment_mapping()

    df = clusters_df.copy()

    # Map attributes
    df["business_segment"] = df["cluster_id"].map(
        lambda cid: map_dict[cid]["business_segment"] if cid in map_dict else "Unknown"
    )
    df["action_category"] = df["cluster_id"].map(
        lambda cid: map_dict[cid]["action_category"] if cid in map_dict else "Unknown"
    )
    df["segment_description"] = df["cluster_id"].map(
        lambda cid: map_dict[cid]["segment_description"] if cid in map_dict else "Unknown"
    )

    if (df["business_segment"] == "Unknown").any():
        raise ValueError("Failed to map some cluster IDs to business segments.")

    return df


def build_segment_summary(
    profiles_df: pd.DataFrame,
    mapping: Optional[Dict[int, Dict[str, str]]] = None,
) -> pd.DataFrame:
    """
    Combine cluster profiles with business names, action categories, and strategic summaries.

    Args:
        profiles_df: Cluster profile DataFrame.
        mapping: Optional custom segment mapping dictionary.

    Returns:
        pd.DataFrame: Comprehensive segment summary DataFrame.
    """
    validate_cluster_profiles(profiles_df)
    map_dict = mapping or build_segment_mapping()

    df = profiles_df.copy()

    df["business_segment"] = df["cluster_id"].map(
        lambda cid: map_dict[cid]["business_segment"] if cid in map_dict else "Unknown"
    )
    df["action_category"] = df["cluster_id"].map(
        lambda cid: map_dict[cid]["action_category"] if cid in map_dict else "Unknown"
    )
    df["primary_characteristic"] = df["cluster_id"].map(
        lambda cid: map_dict[cid]["primary_characteristic"] if cid in map_dict else "Unknown"
    )
    df["business_opportunity"] = df["cluster_id"].map(
        lambda cid: map_dict[cid]["business_opportunity"] if cid in map_dict else "Unknown"
    )

    # Reorder columns logically
    front_cols = [
        "cluster_id",
        "business_segment",
        "action_category",
        "customer_count",
        "customer_percentage",
        "total_revenue",
        "revenue_percentage",
    ]
    other_cols = [c for c in df.columns if c not in front_cols]
    df = df[front_cols + other_cols]

    return df.sort_values(by="cluster_id").reset_index(drop=True)


def save_segment_outputs(
    business_segments_df: pd.DataFrame,
    segment_summary_df: pd.DataFrame,
    output_dir: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """
    Persist customer-level business segments and segment-level summary CSV files.

    Args:
        business_segments_df: Customer-level DataFrame with segments.
        segment_summary_df: Segment-level summary DataFrame.
        output_dir: Target output directory.

    Returns:
        Tuple[Path, Path]: Paths to saved files.
    """
    target_dir = output_dir or DEFAULT_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    segments_path = target_dir / "business_segments.csv"
    summary_path = target_dir / "segment_summary.csv"

    business_segments_df.to_csv(segments_path, index=False)
    segment_summary_df.to_csv(summary_path, index=False)

    logger.info(f"Saved business segments ({len(business_segments_df):,} rows) to: {segments_path}")
    logger.info(f"Saved segment summary ({len(segment_summary_df):,} rows) to: {summary_path}")

    return segments_path, summary_path


def run_segmentation_pipeline(
    clusters_path: Optional[Path] = None,
    profiles_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute the full business segmentation pipeline.

    Args:
        clusters_path: Path to customer_clusters.csv.
        profiles_path: Path to cluster_profiles.csv.
        output_dir: Directory to save generated CSV files.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (business_segments_df, segment_summary_df).
    """
    logger.info("Executing Business Segmentation Pipeline (Phase 10)...")

    profiles_df = load_cluster_profiles(profiles_path)
    clusters_df = load_customer_clusters(clusters_path)

    mapping = build_segment_mapping()

    business_segments_df = assign_business_segments(clusters_df, mapping)
    segment_summary_df = build_segment_summary(profiles_df, mapping)

    save_segment_outputs(business_segments_df, segment_summary_df, output_dir)

    logger.info("Business Segmentation Pipeline successfully completed.")
    return business_segments_df, segment_summary_df


if __name__ == "__main__":
    run_segmentation_pipeline()
