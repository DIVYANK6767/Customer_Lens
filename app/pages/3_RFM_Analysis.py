"""
CustomerLens — Page 3: RFM Analysis (Phase 11).

Explores customer purchasing behavior through Recency, Frequency, and Monetary analysis,
including continuous distributions, log-scale transformations, quintile scores, and bivariate scatters.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st  # type: ignore

from components.filters import render_sidebar_header, render_sidebar_footer
from components.charts import plot_rfm_distributions
from data_loader import load_rfm_metrics
from utils import format_currency, format_number

st.set_page_config(page_title="RFM Analysis — CustomerLens", page_icon="📈", layout="wide")

render_sidebar_header()
render_sidebar_footer()

rfm_df = load_rfm_metrics()

st.title("📈 RFM Behavioral Analysis")
st.markdown("### Continuous Feature Distributions & Quintile Scorecard")

# 1. Operational Definitions
col_r_def, col_f_def, col_m_def = st.columns(3)

with col_r_def:
    st.info(
        "**Recency (R):**\n\n"
        "Elapsed time in calendar days between customer's most recent checkout and the dataset reference anchor (`2011-12-10 12:50:00`). "
        "Lower values denote more immediate engagement."
    )
with col_f_def:
    st.info(
        "**Frequency (F):**\n\n"
        "Total count of unique completed checkout invoices (`invoiceno`) attributed to the customer account. "
        "Measures repeat ordering habituation."
    )
with col_m_def:
    st.info(
        "**Monetary (M):**\n\n"
        "Cumulative gross sales revenue (£) generated across all completed purchases. "
        "Measures lifetime customer commercial contribution."
    )

st.markdown("---")

# 2. Top-Level RFM Baseline KPIs
col_r_kpi, col_f_kpi, col_m_kpi = st.columns(3)

with col_r_kpi:
    st.metric(
        "Recency (Days)",
        f"{rfm_df['median_recency'].iloc[0] if 'median_recency' in rfm_df else rfm_df['recency'].median():.0f} d (Median)",
        f"{rfm_df['recency'].mean():.1f} d (Mean)",
    )
with col_f_kpi:
    st.metric(
        "Order Frequency",
        f"{rfm_df['frequency'].median():.0f} orders (Median)",
        f"{rfm_df['frequency'].mean():.2f} orders (Mean)",
    )
with col_m_kpi:
    st.metric(
        "Monetary Spend (£)",
        format_currency(rfm_df['monetary'].median()) + " (Median)",
        format_currency(rfm_df['monetary'].mean()) + " (Mean)",
    )

st.markdown("---")

# 3. Interactive Filtering for Behavioral Exploration
st.subheader("⚙️ Interactive Behavioral Range Thresholds")
st.caption("Adjust sliders to examine specific customer sub-cohorts.")

f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    min_spend = st.slider("Minimum Monetary Spend (£)", min_value=0.0, max_value=20000.0, value=0.0, step=250.0)
with f_col2:
    min_orders = st.slider("Minimum Order Frequency", min_value=1, max_value=30, value=1, step=1)
with f_col3:
    max_days = st.slider("Maximum Recency (Days)", min_value=1, max_value=374, value=374, step=5)

filtered_rfm = rfm_df[
    (rfm_df["monetary"] >= min_spend) &
    (rfm_df["frequency"] >= min_orders) &
    (rfm_df["recency"] <= max_days)
]

st.markdown(f"**Showing {len(filtered_rfm):,} of {len(rfm_df):,} customers** ({len(filtered_rfm)/len(rfm_df)*100:.1f}% of base)")

if filtered_rfm.empty:
    st.warning("No customers match the specified thresholds.")
    st.stop()

st.markdown("---")

# 4. Continuous Distributions: Raw vs. Log-Transformed
st.subheader("📊 Feature Distributions: Variance & Tail Compression")
use_log = st.checkbox("Apply Variance Stabilization [log1p(x)]", value=True, help="Mitigates severe power-law right skewness.")

fig_dist = plot_rfm_distributions(filtered_rfm, use_log=use_log)
st.pyplot(fig_dist, use_container_width=True)

st.markdown("---")

# 5. Bivariate Behavioral Scatters
st.subheader("🔍 Bivariate Feature Relationships")
col_sc1, col_sc2 = st.columns(2)

with col_sc1:
    st.markdown("**Order Frequency vs. Monetary Spend (Log-Scale)**")
    fig_sc1, ax_sc1 = plt.subplots(figsize=(6, 4))
    ax_sc1.scatter(filtered_rfm["frequency"], filtered_rfm["monetary"], alpha=0.4, color="#1976d2", edgecolors="none", s=20)
    ax_sc1.set_xscale("log")
    ax_sc1.set_yscale("log")
    ax_sc1.set_xlabel("Order Frequency (Log Scale)")
    ax_sc1.set_ylabel("Monetary Spend £ (Log Scale)")
    ax_sc1.set_title("Frequency vs. Spend", fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig_sc1, use_container_width=True)

with col_sc2:
    st.markdown("**Recency vs. Monetary Spend (Log-Scale)**")
    fig_sc2, ax_sc2 = plt.subplots(figsize=(6, 4))
    ax_sc2.scatter(filtered_rfm["recency"], filtered_rfm["monetary"], alpha=0.4, color="#d32f2f", edgecolors="none", s=20)
    ax_sc2.set_xscale("log")
    ax_sc2.set_yscale("log")
    ax_sc2.set_xlabel("Recency Days (Log Scale)")
    ax_sc2.set_ylabel("Monetary Spend £ (Log Scale)")
    ax_sc2.set_title("Recency vs. Spend", fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig_sc2, use_container_width=True)

st.markdown("---")

# 6. RFM Quintile Scorecard Distribution
st.subheader("🎯 RFM Quintile Score Distribution")
st.caption("Distribution of discrete quintile scores (1 to 5) across Recency, Frequency, and Monetary.")

score_cols = ["R_score", "F_score", "M_score"]
if all(c in filtered_rfm.columns for c in score_cols):
    fig_scores, ax_scores = plt.subplots(1, 3, figsize=(12, 3.2))
    score_names = ["Recency Score (R)", "Frequency Score (F)", "Monetary Score (M)"]
    colors = ["#2e7d32", "#1976d2", "#f57c00"]

    for idx, sc in enumerate(score_cols):
        counts = filtered_rfm[sc].value_counts().sort_index()
        ax_scores[idx].bar(counts.index, counts.values, color=colors[idx], width=0.5)
        ax_scores[idx].set_title(score_names[idx], fontweight="bold")
        ax_scores[idx].set_xlabel("Score (1=Low, 5=High)")
        ax_scores[idx].set_ylabel("Customer Count")
        ax_scores[idx].set_xticks(range(1, 6))

    plt.suptitle("RFM Score Frequency Breakdown", fontsize=11, fontweight="bold", y=1.02)
    plt.tight_layout()
    st.pyplot(fig_scores, use_container_width=True)
