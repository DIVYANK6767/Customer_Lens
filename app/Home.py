"""
CustomerLens — Home / Landing Page (Phase 11).

Introduces the analytical pipeline, methodology flow, architecture, and technology stack.
"""

from pathlib import Path
import streamlit as st  # type: ignore
import pandas as pd

from app.components.filters import render_sidebar_header, render_sidebar_footer
from app.data_loader import load_segment_summary
from app.utils import format_currency, format_number

# Configure page layout
st.set_page_config(
    page_title="CustomerLens — Customer Analytics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Render global sidebar
render_sidebar_header()
render_sidebar_footer()

# Title and Executive Header
st.title("CustomerLens")
st.markdown("### Customer Segmentation & Targeted Marketing Analytics")

st.markdown(
    """
    **CustomerLens** is an end-to-end analytical intelligence system designed to process, model, and translate
    retail e-commerce transaction logs into statistically defensible customer personas and testable commercial strategies.

    The platform bridges quantitative unsupervised machine learning (continuous RFM space with K-Means clustering)
    with commercial decision-making, providing marketing and sales leaders with empirical customer intelligence.
    """
)

st.info(
    "**Methodological Guardrail & Scientific Integrity:**\n\n"
    "This application presents **descriptive analytics and hypothesis-driven business opportunities**. "
    "It does not predict churn, guarantee campaign ROI, or claim causal marketing impact. "
    "All strategic recommendations represent structured hypotheses intended for controlled A/B experimentation."
)

st.markdown("---")

# Analytical Workflow Section
st.markdown("### 🔄 End-to-End Analytical Methodology Flow")

st.markdown(
    """
    ```
    +---------------------------------------------------------------------------------------------------+
    |                                   CUSTOMERLENS ANALYTICAL PIPELINE                                |
    +-------------------+-------------------+-------------------+-------------------+-------------------+
    | 1. Ingestion      | 2. Quality Audit  | 3. SQL Analytics  | 4. EDA            | 5. RFM Feature    |
    | Raw Transaction   | Cleaning, Type    | PostgreSQL 18     | Velocity, Volume, | Continuous R, F, M|
    | Logs (541k rows)  | Separation        | Fact Architecture | Country, Pareto   | Feature Store     |
    +-------------------+-------------------+-------------------+-------------------+-------------------+
                                                          │
                                                          ▼
    +-------------------+-------------------+-------------------+-------------------+-------------------+
    | 6. Unsupervised ML| 7. Business Logic | 8. Insights Engine| 9. Multi-Page App | 10. BI Ready      |
    | log1p + Scaling   | Transparent Rules | Experimentation   | Interactive Streamlit| Power BI & API |
    | K-Means (K=4)     | 4 Action Tiers    | Hypothesis Matrix | Presentation Layer| Data Feeds        |
    +-------------------+-------------------+-------------------+-------------------+-------------------+
    ```
    """
)

# Quick Architecture & Metric Highlights
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown("#### 👥 4,338")
    st.caption("Active Commercial Customer Accounts")

with col_m2:
    st.markdown("#### 📦 18,532")
    st.caption("Completed Checkout Invoices")

with col_m3:
    st.markdown("#### 💷 £8,887,208.89")
    st.caption("Verified Gross Sales Turnover")

with col_m4:
    st.markdown("#### 🎯 4 Segments")
    st.caption("Empirical Behavioral Archetypes")

st.markdown("---")

# Exploration Guide & Tech Stack
col_guide, col_tech = st.columns([3, 2])

with col_guide:
    st.markdown("### 🧭 Interactive Application Navigation")
    st.markdown(
        r"""
        Use the sidebar navigation to explore the analytical dimensions:

        1. **📊 Executive Overview:** Top-line financial KPIs, monthly purchasing velocity, top revenue countries, repeat purchase concentration, and evidence-based executive insights.
        2. **🧩 Customer Segmentation:** Detailed scorecard of the 4 K-Means personas, customer vs. revenue share disparities, $K=2..10$ diagnostics, and interactive cluster explorer.
        3. **📈 RFM Analysis:** Behavioral distributions (raw vs. log-scale), bivariate scatter matrices, quintile score distributions ($1 \dots 5$), and interactive range filters.
        4. **💡 Marketing Insights:** Actionable strategy cards (`Protect & Grow`, `Nurture`, `Develop`, `Reactivate`), controlled experimentation designs, and risk caveats.
        5. **🔎 Customer Explorer:** Multi-criteria customer search grid, account-level RFM metrics, and metric-grounded plain-language behavioral summaries.
        """
    )


with col_tech:
    st.markdown("### 🛠️ Production Technology Stack")
    st.markdown(
        """
        - **Core Analytics:** Python 3, Pandas, NumPy, Scipy
        - **Relational Data Layer:** PostgreSQL 18, psycopg3, Advanced SQL
        - **Machine Learning:** Scikit-learn (K-Means++, StandardScaler, PCA)
        - **Presentation & Web:** Streamlit (Multipage Native Architecture)
        - **Visualization:** Matplotlib, Seaborn
        - **Testing & QA:** Pytest (147+ unit & integration tests), Compileall
        - **Downstream Readiness:** Power BI semantic feeds & CSV exports
        """
    )

st.markdown("---")
st.caption("CustomerLens Analytics Platform © 2026. Designed for institutional portfolio demonstration and technical review.")
