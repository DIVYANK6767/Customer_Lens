"""
CustomerLens — Page 4: Marketing Insights & Strategic Hypotheses (Phase 11).

Translates empirical behavioral clusters into hypothesis-driven marketing opportunities,
controlled experimentation designs, and risk caveats without making unsupported predictive claims.
"""

from pathlib import Path
import streamlit as st  # type: ignore
import pandas as pd

from app.components.filters import render_sidebar_header, render_sidebar_footer
from app.data_loader import load_marketing_opportunities, load_segment_summary
from app.utils import format_currency, format_number, format_percentage

st.set_page_config(page_title="Marketing Insights — CustomerLens", page_icon="💡", layout="wide")

render_sidebar_header()
render_sidebar_footer()

opp_df = load_marketing_opportunities()
summary_df = load_segment_summary()

st.title("💡 Strategic Marketing Opportunities")
st.markdown("### Hypothesis-Driven Experimentation & Growth Levers")

st.warning(
    "**Methodological Guardrail & Scientific Integrity:**\n\n"
    "Because the source dataset contains historical sales transactions without marketing exposure, email engagement, "
    "or promotional redemption logs, **no historical campaign response or causal marketing effect can be measured retrospectively**. "
    "All strategic recommendations below represent **testable business hypotheses** that require validation via controlled A/B experiments."
)

st.markdown("---")

# 1. Segment Strategy Cards
st.subheader("📋 Segment Strategy & Action Framework")

action_colors = {
    "Protect & Grow": "🟢",
    "Nurture": "🔵",
    "Develop": "🟠",
    "Reactivate": "⚪",
}

for _, row in opp_df.iterrows():
    seg_name = row["business_segment"]
    action_cat = row["action_category"]
    icon = action_colors.get(action_cat, "🔹")

    with st.expander(f"{icon} **{seg_name}** — Priority: `{action_cat}`", expanded=True):
        col_char, col_action = st.columns([1, 1])

        with col_char:
            st.markdown(f"**Customer Volume:** {row['customer_count']:,} ({row['customer_percentage']:.1f}% of base)")
            st.markdown(f"**Turnover Generated:** {format_currency(row['revenue'])} ({row['revenue_percentage']:.1f}% of total)")
            st.markdown(f"**Primary Characteristic:**\n{row['primary_characteristic']}")
            st.markdown(f"**Commercial Opportunity:**\n{row['business_opportunity']}")

        with col_action:
            st.markdown(f"**Recommended Strategic Action:**\n{row['recommended_action']}")
            st.markdown(f"**Proposed Success KPI:**\n`{row['measurement_metric']}`")
            st.markdown(f"**Risk Caveat & Guardrail:**\n⚠️ {row['caveat']}")

st.markdown("---")

# 2. Controlled Experimentation Framework
st.subheader("🧪 Proposed A/B Experimentation Framework")
st.markdown(
    """
    To evaluate whether these interventions yield statistically significant incremental value,
    marketing teams must execute **randomized controlled trials (RCT)** with an uncontacted holdout baseline.
    """
)

exp_data = [
    {
        "Business Segment": "High-Value Engaged",
        "Target Cohort": "716 Accounts (65.1% Revenue)",
        "Treatment Strategy": "Dedicated B2B account specialist & automated replenishment triggers",
        "Control Group": "Standard self-serve ordering portal (no outreach)",
        "Primary KPI": "90-Day Account Retention Rate",
        "Guardrail Metric": "Gross Margin % per Account (prevent margin erosion)",
    },
    {
        "Business Segment": "Established Valuable",
        "Target Cohort": "1,170 Accounts (23.5% Revenue)",
        "Treatment Strategy": "Tiered volume threshold promotion (£500+ orders unlock 10% credit)",
        "Control Group": "Standard flat promotional broadcast",
        "Primary KPI": "Quarterly Order Frequency Velocity",
        "Guardrail Metric": "Average Order Value (AOV must remain >= £400)",
    },
    {
        "Business Segment": "Recent Developing",
        "Target Cohort": "834 Accounts (5.2% Revenue)",
        "Treatment Strategy": "Triggered 21-Day personalized onboarding & restock recommendation",
        "Control Group": "No post-purchase sequence (organic behavior)",
        "Primary KPI": "60-Day Repeat Purchase Conversion Rate",
        "Guardrail Metric": "Email Unsubscribe Rate (< 0.5%)",
    },
    {
        "Business Segment": "Low-Engagement / Reactivation",
        "Target Cohort": "1,618 Accounts (6.2% Revenue)",
        "Treatment Strategy": "Single automated digital seasonal clearance promotion",
        "Control Group": "Zero contact (Holdout control to measure organic return)",
        "Primary KPI": "Reactivation Conversion Rate",
        "Guardrail Metric": "Net Marketing Cost per Contact (£0.00 paid media)",
    },
]

st.dataframe(pd.DataFrame(exp_data), use_container_width=True, hide_index=True)

st.markdown("---")

# 3. Interactive Segment Deep Dive
st.subheader("🔍 Deep-Dive Strategic Persona Review")

selected_segment = st.selectbox(
    "Select Segment for Operational Review:",
    options=opp_df["business_segment"].tolist(),
    index=0,
)

seg_row = opp_df[opp_df["business_segment"] == selected_segment].iloc[0]
sum_row = summary_df[summary_df["business_segment"] == selected_segment].iloc[0]

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total Segment Spend", format_currency(seg_row["revenue"]), f"{seg_row['revenue_percentage']:.1f}% of total")
with c2:
    st.metric("Customer Accounts", f"{seg_row['customer_count']:,}", f"{seg_row['customer_percentage']:.1f}% of base")
with c3:
    st.metric("Median Order Cadence", f"{sum_row['median_frequency']:.0f} orders", f"{sum_row['median_recency']:.0f} days median recency")

st.markdown(f"#### Strategic Action Plan: {seg_row['action_category']}")
st.markdown(f"- **Implementation Mechanism:** {seg_row['recommended_action']}")
st.markdown(f"- **Proposed Measurement Metric:** `{seg_row['measurement_metric']}`")
st.markdown(f"- **Downside Risk & Operational Guardrail:** {seg_row['caveat']}")
