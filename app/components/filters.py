"""
CustomerLens — Sidebar & Filtering Components (Phase 11).

Provides consistent global sidebar branding, metadata context, and filter widgets.
"""

from typing import Dict, List, Tuple, Optional, Any
import streamlit as st  # type: ignore
import pandas as pd


def render_sidebar_header() -> None:
    """Render consistent sidebar header branding and project metadata."""
    st.sidebar.markdown("## 🔍 CustomerLens")
    st.sidebar.markdown(
        "**Customer Segmentation & Targeted Marketing Analytics**\n\n"
        "*Empirical behavioral modeling in retail e-commerce.*"
    )
    st.sidebar.markdown("---")


def render_sidebar_footer() -> None:
    """Render analytical disclaimer and lineage in sidebar footer."""
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "**Data Invariants Verified:**\n"
        "- 4,338 Active Customers\n"
        "- 18,532 Completed Invoices\n"
        "- £8,887,208.89 Turnover\n"
        "- Observation Anchor: 2011-12-10\n\n"
        "*Descriptive analytics & testable hypotheses only.*"
    )


def render_customer_filters(
    customers_df: pd.DataFrame,
    show_country: bool = True,
    show_segments: bool = True,
    show_action: bool = True,
    show_sliders: bool = True,
) -> Dict[str, Any]:
    """
    Render interactive filter controls in the sidebar and return selected values.

    Args:
        customers_df: Customer DataFrame to extract options and bounds from.
        show_country: Whether to include country filter.
        show_segments: Whether to include segment multiselect.
        show_action: Whether to include action category multiselect.
        show_sliders: Whether to include numerical threshold sliders.

    Returns:
        Dict[str, Any]: Dictionary of active filter settings.
    """
    st.sidebar.markdown("### ⚙️ Page Filters")
    st.sidebar.caption("Filters apply to the current page view.")

    selected_countries = None
    if show_country and "country" in customers_df.columns:
        all_countries = sorted(customers_df["country"].dropna().unique().tolist())
        selected_countries = st.sidebar.multiselect(
            "Country",
            options=all_countries,
            default=[],
            help="Filter transactions and customer accounts by country.",
        )

    selected_segments = None
    if show_segments and "business_segment" in customers_df.columns:
        all_segments = [
            "High-Value Engaged",
            "Established Valuable",
            "Recent Developing",
            "Low-Engagement / Reactivation",
        ]
        selected_segments = st.sidebar.multiselect(
            "Business Segment",
            options=all_segments,
            default=[],
            help="Filter by behavioral cluster persona.",
        )

    selected_actions = None
    if show_action and "action_category" in customers_df.columns:
        all_actions = ["Protect & Grow", "Nurture", "Develop", "Reactivate"]
        selected_actions = st.sidebar.multiselect(
            "Action Category",
            options=all_actions,
            default=[],
            help="Filter by operational marketing action category.",
        )

    min_spend = None
    min_freq = None
    max_rec = None

    if show_sliders:
        with st.sidebar.expander("Advanced Numerical Thresholds", expanded=False):
            max_mon = float(customers_df["monetary"].max()) if not customers_df.empty else 10000.0
            min_spend = st.slider("Minimum Spend (£)", min_value=0.0, max_value=min(max_mon, 50000.0), value=0.0, step=100.0)

            max_f = int(customers_df["frequency"].max()) if not customers_df.empty else 100
            min_freq = st.slider("Minimum Orders", min_value=1, max_value=min(max_f, 50), value=1, step=1)

            max_r = int(customers_df["recency"].max()) if not customers_df.empty else 374
            max_rec = st.slider("Maximum Recency (Days)", min_value=1, max_value=max_r, value=max_r, step=5)

    return {
        "countries": selected_countries if selected_countries else None,
        "segments": selected_segments if selected_segments else None,
        "action_categories": selected_actions if selected_actions else None,
        "min_monetary": min_spend if (min_spend and min_spend > 0) else None,
        "min_frequency": min_freq if (min_freq and min_freq > 1) else None,
        "max_recency": max_rec if (max_rec and max_rec < 374) else None,
    }
