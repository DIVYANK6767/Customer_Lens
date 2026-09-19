"""
CustomerLens — Page 5: Customer Account Explorer (Phase 11).

Provides interactive search, multi-attribute filtering, customer data grid,
and single-account behavioral detail cards with factual, non-predictive summaries.
"""

from pathlib import Path
import streamlit as st  # type: ignore
import pandas as pd

from app.components.filters import render_sidebar_header, render_sidebar_footer, render_customer_filters
from app.components.metrics import render_customer_kpis
from app.data_loader import load_business_segments
from app.utils import filter_customers, format_currency, format_number, generate_customer_interpretation

st.set_page_config(page_title="Customer Explorer — CustomerLens", page_icon="🔎", layout="wide")

render_sidebar_header()

# Load customer dataset
customers_df = load_business_segments()

# Render sidebar filters
filter_settings = render_customer_filters(
    customers_df,
    show_country=True,
    show_segments=True,
    show_action=True,
    show_sliders=True,
)
render_sidebar_footer()

st.title("🔎 Customer Account Explorer")
st.markdown("### Interactive Single-Account Search & Multi-Attribute Filtering")

# Search bar
search_col, count_col = st.columns([3, 1])
with search_col:
    search_id = st.text_input("Search by Customer ID:", placeholder="e.g. 14646, 18102, 17841...")

# Apply filters
filtered_df = filter_customers(
    customers_df,
    search_query=search_id if search_id else None,
    segments=filter_settings.get("segments"),
    action_categories=filter_settings.get("action_categories"),
    countries=filter_settings.get("countries"),
    min_monetary=filter_settings.get("min_monetary"),
    min_frequency=filter_settings.get("min_frequency"),
    max_recency=filter_settings.get("max_recency"),
)

with count_col:
    st.metric("Matching Accounts", f"{len(filtered_df):,}", f"of {len(customers_df):,}")

if filtered_df.empty:
    st.warning("No customer accounts match the current filter criteria.")
    st.stop()

st.markdown("---")

# 1. Customer Detail Card (Select single account)
st.subheader("👤 Individual Account Behavioral Profile")

default_cids = filtered_df["customerid"].tolist()
selected_cid = st.selectbox(
    "Select Account to Inspect:",
    options=default_cids,
    index=0,
    help="Displays verified empirical metrics and behavioral persona assignment.",
)

cust_row = customers_df[customers_df["customerid"] == selected_cid].iloc[0]

# Render individual KPI cards
render_customer_kpis(cust_row)

st.markdown(f"**Country Location:** `{cust_row.get('country', 'Unknown')}`")
st.markdown(f"**Assigned Behavioral Persona:** `{cust_row['business_segment']}` (Cluster {int(cust_row['cluster_id'])})")
st.markdown(f"**Operational Action Priority:** `{cust_row['action_category']}`")

# Plain-language factual interpretation
st.info(f"**Factual Behavioral Summary:**\n\n{generate_customer_interpretation(cust_row)}")

st.markdown("---")

# 2. Filterable Data Grid
st.subheader("📋 Filtered Accounts Data Grid")
st.caption("Displaying top 100 matching customer records. Click column headers to sort.")

display_table = filtered_df.head(100).copy()
display_table["Monetary Spend (£)"] = display_table["monetary"].apply(lambda v: format_currency(v))
display_table["Recency (Days)"] = display_table["recency"].apply(lambda v: f"{int(v)} d")
display_table["Frequency (Orders)"] = display_table["frequency"].apply(lambda v: f"{int(v)} ord")

cols_to_render = [
    "customerid",
    "country",
    "business_segment",
    "action_category",
    "Recency (Days)",
    "Frequency (Orders)",
    "Monetary Spend (£)",
    "RFM_score",
    "cluster_id",
]

st.dataframe(
    display_table[cols_to_render].rename(columns={
        "customerid": "Customer ID",
        "country": "Country",
        "business_segment": "Business Segment",
        "action_category": "Action Category",
        "RFM_score": "RFM Score",
        "cluster_id": "Cluster ID",
    }),
    use_container_width=True,
    hide_index=True,
)
