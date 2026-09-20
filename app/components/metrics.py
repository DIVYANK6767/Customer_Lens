"""
CustomerLens — Metric Cards & Scorecard Components (Phase 11).

Provides standardized metric card containers and summary tables.
"""

from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st  # type: ignore

try:
    from utils import format_currency, format_number, format_percentage
except ModuleNotFoundError:
    from app.utils import format_currency, format_number, format_percentage


def render_executive_kpis(kpi_data: Dict[str, Any]) -> None:
    """
    Render 5 top-level KPI metric cards horizontally.

    Args:
        kpi_data: Dictionary of calculated KPI metrics from calculate_executive_kpis.
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Active Customers",
            value=format_number(kpi_data.get("total_customers", 0)),
            help="Unique identified customer accounts with completed sales.",
        )
    with col2:
        st.metric(
            label="Completed Orders",
            value=format_number(kpi_data.get("total_orders", 0)),
            help="Total unique invoice checkouts.",
        )
    with col3:
        st.metric(
            label="Total Gross Revenue",
            value=format_currency(kpi_data.get("total_revenue", 0.0)),
            help="Cumulative sales volume across observation period.",
        )
    with col4:
        st.metric(
            label="Average Order Value",
            value=format_currency(kpi_data.get("average_order_value", 0.0)),
            help="Total Revenue / Total Completed Invoices.",
        )
    with col5:
        st.metric(
            label="Repeat Customer Rate",
            value=format_percentage(kpi_data.get("repeat_customer_rate", 0.0)),
            help="Percentage of customer accounts with frequency > 1.",
        )


def render_segment_scorecard(summary_df: pd.DataFrame) -> None:
    """
    Render a styled, readable scorecard table for business segments.

    Args:
        summary_df: Segment summary DataFrame.
    """
    display_df = summary_df.copy()

    # Format columns for display
    display_df["Customer Share"] = display_df["customer_percentage"].apply(lambda v: format_percentage(v))
    display_df["Revenue Share"] = display_df["revenue_percentage"].apply(lambda v: format_percentage(v))
    display_df["Total Revenue (£)"] = display_df["total_revenue"].apply(lambda v: format_currency(v))
    display_df["Customer Count"] = display_df["customer_count"].apply(lambda v: format_number(v))
    display_df["Median Recency"] = display_df["median_recency"].apply(lambda v: f"{v:.0f} d")
    display_df["Median Frequency"] = display_df["median_frequency"].apply(lambda v: f"{v:.0f} ord")
    display_df["Median Spend"] = display_df["median_monetary"].apply(lambda v: format_currency(v))

    cols_to_show = [
        "cluster_id",
        "business_segment",
        "action_category",
        "Customer Count",
        "Customer Share",
        "Total Revenue (£)",
        "Revenue Share",
        "Median Recency",
        "Median Frequency",
        "Median Spend",
    ]

    st.dataframe(
        display_df[cols_to_show].rename(columns={
            "cluster_id": "Cluster ID",
            "business_segment": "Business Segment",
            "action_category": "Action Category",
        }),
        use_container_width=True,
        hide_index=True,
    )


def render_customer_kpis(customer_row: pd.Series) -> None:
    """
    Render 4 behavioral metric cards for an individual customer.

    Args:
        customer_row: Series representing a single customer.
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Recency",
            value=f"{int(customer_row.get('recency', 0))} days",
            help="Days elapsed between last purchase and 2011-12-10 anchor.",
        )
    with col2:
        st.metric(
            label="Order Frequency",
            value=f"{int(customer_row.get('frequency', 0))} orders",
            help="Number of distinct completed invoices.",
        )
    with col3:
        st.metric(
            label="Monetary Spend",
            value=format_currency(customer_row.get("monetary", 0.0)),
            help="Cumulative lifetime sales revenue.",
        )
    with col4:
        st.metric(
            label="RFM Score",
            value=str(customer_row.get("RFM_score", "N/A")),
            help="Concatenated R-F-M quintile ratings (1-5 each).",
        )
