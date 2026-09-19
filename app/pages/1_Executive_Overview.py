"""
CustomerLens — Page 1: Executive Overview (Phase 11).

Presents top-line commercial KPIs, seasonal monthly turnover, country distribution,
repeat purchasing concentration, and evidence-based executive insights.
"""

from pathlib import Path
import streamlit as st  # type: ignore
import pandas as pd

from app.components.filters import render_sidebar_header, render_sidebar_footer, render_customer_filters
from app.components.metrics import render_executive_kpis
from app.components.charts import (
    plot_revenue_by_month,
    plot_customer_vs_revenue_share,
    plot_revenue_by_country,
    plot_repeat_vs_onetime,
    plot_revenue_concentration,
)
from app.data_loader import (
    load_customer_transactions,
    load_business_segments,
    load_segment_summary,
)
from app.utils import calculate_executive_kpis, filter_customers, format_currency, format_number, format_percentage

st.set_page_config(page_title="Executive Overview — CustomerLens", page_icon="📊", layout="wide")

render_sidebar_header()

# Load source datasets
transactions_df = load_customer_transactions()
customers_df = load_business_segments()
summary_df = load_segment_summary()

# Render sidebar filters
filter_settings = render_customer_filters(customers_df, show_country=True, show_segments=True, show_action=False, show_sliders=False)
render_sidebar_footer()

# Apply active filters if any
filtered_customers = filter_customers(
    customers_df,
    countries=filter_settings.get("countries"),
    segments=filter_settings.get("segments"),
)

# Filter transactions accordingly
if filter_settings.get("countries") or filter_settings.get("segments"):
    active_cids = set(filtered_customers["customerid"].unique())
    filtered_transactions = transactions_df[transactions_df["customerid"].isin(active_cids)]
else:
    filtered_transactions = transactions_df

# Page Header
st.title("📊 Executive Overview")
st.markdown("### Strategic Performance Dashboard & Revenue Composition")

if filtered_customers.empty or filtered_transactions.empty:
    st.warning("No data matches the selected filters. Please adjust your criteria in the sidebar.")
    st.stop()

# 1. Top KPI Metrics
kpi_data = calculate_executive_kpis(filtered_transactions, filtered_customers)
render_executive_kpis(kpi_data)

st.markdown("---")

# 2. Executive Visuals - Row 1
col_month, col_country = st.columns(2)

with col_month:
    st.subheader("Monthly Revenue Velocity")
    st.caption("Aggregated monthly sales volume illustrating Q4 surge (November peak).")
    fig_month = plot_revenue_by_month(filtered_transactions)
    st.pyplot(fig_month, use_container_width=True)

with col_country:
    st.subheader("Geographic Revenue Distribution")
    st.caption("Top gross revenue contributing markets (UK domestic vs. European exports).")
    fig_country = plot_revenue_by_country(filtered_transactions, top_n=8)
    st.pyplot(fig_country, use_container_width=True)

st.markdown("---")

# 3. Executive Visuals - Row 2
col_share, col_repeat = st.columns(2)

with col_share:
    st.subheader("Segment Contribution Disparity")
    st.caption("Customer volume (% of Base) vs. Gross Revenue contribution (% of Turnover).")
    fig_share = plot_customer_vs_revenue_share(summary_df)
    st.pyplot(fig_share, use_container_width=True)

with col_repeat:
    st.subheader("Repeat Purchasing Concentration")
    st.caption("Comparison between one-time shoppers (1 order) and repeat accounts (2+ orders).")
    fig_repeat = plot_repeat_vs_onetime(filtered_customers)
    st.pyplot(fig_repeat, use_container_width=True)

st.markdown("---")

# 4. Revenue Concentration Ratio
st.subheader("Revenue Concentration Index by Segment")
st.caption("Ratio of % Revenue Share to % Customer Share. Ratios > 1.0x denote high-yield commercial segments.")
fig_conc = plot_revenue_concentration(summary_df)
st.pyplot(fig_conc, use_container_width=True)

st.markdown("---")

# 5. Evidence-Based Executive Insights
st.subheader("💡 Evidence-Based Executive Observations")

# Compute dynamic insight values
r3_row = summary_df[summary_df["cluster_id"] == 3].iloc[0]
r1_row = summary_df[summary_df["cluster_id"] == 1].iloc[0]
total_rev = kpi_data["total_revenue"]

st.markdown(
    f"""
    - **Top-Tier Revenue Concentration:** The **{r3_row['business_segment']}** segment represents **{r3_row['customer_percentage']:.1f}% of customer accounts** ({r3_row['customer_count']:,} accounts) but generates **{r3_row['revenue_percentage']:.1f}% of observed revenue** ({format_currency(r3_row['total_revenue'])}). This cohort forms the primary commercial foundation of the business.
    - **Repeat Customer Leverage:** Repeat buyers represent **{kpi_data['repeat_customer_rate']:.1f}% of customers** ({kpi_data['repeat_customers']:,} accounts) but drive **{kpi_data['repeat_revenue_rate']:.1f}% of gross turnover** ({format_currency(kpi_data['repeat_revenue'])}). Sustainable growth relies on second-order conversion rather than one-time acquisition.
    - **Largest Headcount Cohort:** The **{r1_row['business_segment']}** cohort represents the largest individual group by customer count (**{r1_row['customer_percentage']:.1f}% of base**, {r1_row['customer_count']:,} accounts), yet yields only **{r1_row['revenue_percentage']:.1f}% of revenue** ({format_currency(r1_row['total_revenue'])}).
    - **Seasonal Demand Surge:** Monthly transaction volume peaks sharply in Q4 (October–November), reflecting wholesale inventory restocking cycles prior to the retail holiday season.
    """
)
