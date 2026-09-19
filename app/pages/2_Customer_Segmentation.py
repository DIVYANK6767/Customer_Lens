"""
CustomerLens — Page 2: Customer Segmentation (Phase 11).

Presents the K-Means customer segmentation scorecard, behavioral profile comparisons,
clustering evaluation diagnostics (K=2..10), and an interactive cluster explorer.
"""

from pathlib import Path
import streamlit as st  # type: ignore
import pandas as pd

from app.components.filters import render_sidebar_header, render_sidebar_footer
from app.components.metrics import render_segment_scorecard
from app.components.charts import (
    plot_customer_vs_revenue_share,
    plot_rfm_metric_comparison,
    plot_revenue_concentration,
    plot_clustering_diagnostics,
)
from app.data_loader import (
    load_cluster_profiles,
    load_clustering_metrics,
    load_segment_summary,
)
from app.utils import format_currency, format_number, format_percentage

st.set_page_config(page_title="Customer Segmentation — CustomerLens", page_icon="🧩", layout="wide")

render_sidebar_header()
render_sidebar_footer()

summary_df = load_segment_summary()
metrics_df = load_clustering_metrics()
profiles_df = load_cluster_profiles()

st.title("🧩 Customer Segmentation")
st.markdown("### RFM-Based K-Means Behavioral Customer Personas")

st.markdown(
    """
    In **Phase 9**, CustomerLens deployed unsupervised machine learning (**K-Means Clustering**) over
    log-transformed and standardized Recency, Frequency, and Monetary features. In **Phase 10**, clusters
    were mapped to transparent, actionable commercial archetypes.
    """
)

st.markdown("---")

# 1. Segment Scorecard Table
st.subheader("📋 Segment Performance Scorecard")
st.caption("Empirical summary of customer volume, gross turnover, and median behavioral metrics.")
render_segment_scorecard(summary_df)

st.markdown("---")

# 2. Behavioral & Financial Comparisons
st.subheader("📊 Behavioral Separation Across Personas")
st.caption("Comparison of median Recency (days), Frequency (orders), and Monetary spend (£) across segments.")
fig_rfm = plot_rfm_metric_comparison(summary_df)
st.pyplot(fig_rfm, use_container_width=True)

col_share, col_conc = st.columns(2)
with col_share:
    st.subheader("Customer Share vs. Revenue Share")
    st.caption("Comparison highlighting extreme top-tier revenue contribution.")
    fig_share = plot_customer_vs_revenue_share(summary_df)
    st.pyplot(fig_share, use_container_width=True)

with col_conc:
    st.subheader("Revenue Concentration Multiplier")
    st.caption("Relative revenue density (% Revenue / % Customer share).")
    fig_conc = plot_revenue_concentration(summary_df)
    st.pyplot(fig_conc, use_container_width=True)

st.markdown("---")

# 3. K-Means Clustering Diagnostics (K=2..10)
st.subheader("🔬 K-Means Model Selection & Diagnostic Scorecard")
st.caption("Evaluation of candidate cluster counts from K=2 through K=10.")

col_diag_table, col_diag_chart = st.columns([1, 1])

with col_diag_table:
    st.markdown("**Clustering Validation Scorecard (K=2..10):**")
    disp_metrics = metrics_df[[
        "k", "inertia", "silhouette_score", "calinski_harabasz", "davies_bouldin", "min_cluster_size", "max_cluster_size"
    ]].rename(columns={
        "k": "K",
        "inertia": "Inertia (WCSS)",
        "silhouette_score": "Silhouette Score",
        "calinski_harabasz": "Calinski-Harabasz",
        "davies_bouldin": "Davies-Bouldin",
        "min_cluster_size": "Min Cluster Size",
        "max_cluster_size": "Max Cluster Size",
    })
    st.dataframe(disp_metrics, use_container_width=True, hide_index=True)

with col_diag_chart:
    fig_diag = plot_clustering_diagnostics(metrics_df)
    st.pyplot(fig_diag, use_container_width=True)

with st.expander("ℹ️ Model Selection Methodology & Disclaimer (Why K=4?)", expanded=True):
    st.markdown(
        r"""
        **Model Selection Rationale:**

        K was evaluated across multiple candidate values ($K \in [2, 10]$). **$K=4$ was selected as a business-oriented
        segmentation solution** because it provided four interpretable customer groups while maintaining reasonable cluster sizes
        (ranging from 716 to 1,618 accounts) and acceptable clustering diagnostics.

        - **$K=2$** yielded a higher mathematical silhouette score (0.4328), but split the customer base into a simplistic
          binary dichotomy ('high activity' vs. 'low activity'), merging dormant wholesale accounts with single-purchase retail shoppers.
        - **$K=4$** achieved an inertia elbow inflection and a local silhouette peak (**0.3374**), cleanly partitioning customers into distinct
          lifecycle stages.
        - **$K \ge 5$** fragmented the high-value cohort into micro-clusters (e.g. 330 accounts at $K=5$) without improving interpretability.

        *Note: This selection represents a practical business choice balancing statistics and actionability. It is not claimed that K=4 is mathematically optimal across all criteria.*
        """
    )


st.markdown("---")

# 4. Interactive Cluster Explorer
st.subheader("🔍 Interactive Cluster Persona Explorer")
st.caption("Select a cluster to review its operational profile, behavioral fingerprint, and growth opportunities.")

cluster_options = {
    3: "Cluster 3 — High-Value Engaged (Protect & Grow)",
    2: "Cluster 2 — Established Valuable (Nurture)",
    0: "Cluster 0 — Recent Developing (Develop)",
    1: "Cluster 1 — Low-Engagement / Reactivation (Reactivate)",
}

selected_cluster_id = st.selectbox(
    "Choose Cluster to Inspect:",
    options=list(cluster_options.keys()),
    format_func=lambda cid: cluster_options[cid],
    index=0,
)

seg_data = summary_df[summary_df["cluster_id"] == selected_cluster_id].iloc[0]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Customer Volume", f"{seg_data['customer_count']:,}", f"{seg_data['customer_percentage']:.1f}% of base")
with c2:
    st.metric("Total Revenue (£)", format_currency(seg_data['total_revenue']), f"{seg_data['revenue_percentage']:.1f}% of turnover")
with c3:
    st.metric("Median Cadence", f"{seg_data['median_frequency']:.0f} orders", f"{seg_data['average_frequency']:.1f} avg orders")
with c4:
    st.metric("Median Basket / Spend", format_currency(seg_data['median_monetary']), f"{format_currency(seg_data['average_monetary'])} avg spend")

st.markdown(f"**Operational Action Priority:** `{seg_data['action_category']}`")
st.markdown(f"**Primary Empirical Characteristic:** {seg_data['primary_characteristic']}")
st.markdown(f"**Commercial Opportunity:** {seg_data['business_opportunity']}")
