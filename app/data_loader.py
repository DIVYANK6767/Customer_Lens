"""
CustomerLens — Central Data Access Layer (Phase 11).

Provides cached loading functions for all precomputed and validated analytical outputs.
All paths are project-relative using pathlib.
"""

from pathlib import Path
from typing import Optional
import logging
import pandas as pd
import streamlit as st  # type: ignore

try:
    from utils import validate_required_columns
except ModuleNotFoundError:
    from app.utils import validate_required_columns

logger = logging.getLogger(__name__)

# Base project path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def _handle_missing_file(file_path: Path, dataset_name: str) -> None:
    """Helper to display clear error message and raise FileNotFoundError."""
    msg = (
        f"Critical file missing: '{file_path.name}' not found at {file_path}. "
        f"Please run the upstream {dataset_name} pipeline first."
    )
    st.error(msg)
    raise FileNotFoundError(msg)


@st.cache_data(show_spinner=False)
def load_customer_transactions(custom_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load cleaned customer transactions dataset.

    Returns:
        pd.DataFrame: Transactions fact table.
    """
    path = custom_path or (DATA_PROCESSED_DIR / "customer_transactions.csv")
    if not path.exists():
        _handle_missing_file(path, "Customer Transactions (Phase 5)")
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower()
    if "invoicedate" in df.columns:
        df["invoicedate"] = pd.to_datetime(df["invoicedate"])
    validate_required_columns(
        df,
        ["invoiceno", "stockcode", "quantity", "unitprice", "customerid", "country", "revenue"],
        "customer_transactions.csv",
    )
    return df



@st.cache_data(show_spinner=False)
def load_rfm_metrics(custom_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load customer RFM behavioral feature store.

    Returns:
        pd.DataFrame: Customer-level RFM metrics.
    """
    path = custom_path or (DATA_PROCESSED_DIR / "rfm_customer_metrics.csv")
    if not path.exists():
        _handle_missing_file(path, "RFM Feature Store (Phase 8)")
    df = pd.read_csv(path)
    validate_required_columns(
        df,
        ["customerid", "recency", "frequency", "monetary", "R_score", "F_score", "M_score", "RFM_score", "segment"],
        "rfm_customer_metrics.csv",
    )
    return df


@st.cache_data(show_spinner=False)
def load_customer_clusters(custom_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load customer cluster assignments with PCA projections.

    Returns:
        pd.DataFrame: Customer clusters.
    """
    path = custom_path or (DATA_PROCESSED_DIR / "customer_clusters.csv")
    if not path.exists():
        _handle_missing_file(path, "K-Means Clustering (Phase 9)")
    df = pd.read_csv(path)
    validate_required_columns(
        df,
        ["customerid", "recency", "frequency", "monetary", "cluster_id", "PCA1", "PCA2"],
        "customer_clusters.csv",
    )
    return df


@st.cache_data(show_spinner=False)
def load_cluster_profiles(custom_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load empirical cluster profile statistics.

    Returns:
        pd.DataFrame: Cluster profiles.
    """
    path = custom_path or (DATA_PROCESSED_DIR / "cluster_profiles.csv")
    if not path.exists():
        _handle_missing_file(path, "Cluster Profiles (Phase 9)")
    df = pd.read_csv(path)
    validate_required_columns(
        df,
        [
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
        ],
        "cluster_profiles.csv",
    )
    return df


@st.cache_data(show_spinner=False)
def load_clustering_metrics(custom_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load K=2..10 clustering evaluation diagnostics.

    Returns:
        pd.DataFrame: Model selection scorecard.
    """
    path = custom_path or (DATA_PROCESSED_DIR / "clustering_metrics.csv")
    if not path.exists():
        _handle_missing_file(path, "Clustering Metrics (Phase 9)")
    df = pd.read_csv(path)
    validate_required_columns(
        df,
        ["k", "inertia", "silhouette_score", "calinski_harabasz", "davies_bouldin"],
        "clustering_metrics.csv",
    )
    return df


@st.cache_data(show_spinner=False)
def load_business_segments(custom_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load customer records with business segment and action category assignments.

    Returns:
        pd.DataFrame: Customer business segments.
    """
    path = custom_path or (DATA_PROCESSED_DIR / "business_segments.csv")
    if not path.exists():
        _handle_missing_file(path, "Business Segments (Phase 10)")
    df = pd.read_csv(path)
    validate_required_columns(
        df,
        [
            "customerid",
            "recency",
            "frequency",
            "monetary",
            "cluster_id",
            "business_segment",
            "action_category",
        ],
        "business_segments.csv",
    )
    return df


@st.cache_data(show_spinner=False)
def load_segment_summary(custom_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load business segment summary table.

    Returns:
        pd.DataFrame: Segment summary.
    """
    path = custom_path or (DATA_PROCESSED_DIR / "segment_summary.csv")
    if not path.exists():
        _handle_missing_file(path, "Segment Summary (Phase 10)")
    df = pd.read_csv(path)
    validate_required_columns(
        df,
        [
            "cluster_id",
            "business_segment",
            "action_category",
            "customer_count",
            "customer_percentage",
            "total_revenue",
            "revenue_percentage",
            "primary_characteristic",
            "business_opportunity",
        ],
        "segment_summary.csv",
    )
    return df


@st.cache_data(show_spinner=False)
def load_marketing_opportunities(custom_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load structured marketing opportunities and experimentation framework.

    Returns:
        pd.DataFrame: Marketing opportunities table.
    """
    path = custom_path or (DATA_PROCESSED_DIR / "marketing_opportunities.csv")
    if not path.exists():
        _handle_missing_file(path, "Marketing Opportunities (Phase 10)")
    df = pd.read_csv(path)
    validate_required_columns(
        df,
        [
            "cluster_id",
            "business_segment",
            "action_category",
            "primary_characteristic",
            "business_opportunity",
            "recommended_action",
            "measurement_metric",
            "caveat",
        ],
        "marketing_opportunities.csv",
    )
    return df
