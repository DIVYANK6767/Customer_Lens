# CustomerLens — Customer Segmentation & Targeted Marketing Analytics

## Project Description

CustomerLens is an end-to-end e-commerce customer analytics project designed to analyze real transaction data, uncover customer purchasing behavior, compute RFM (Recency, Frequency, Monetary) metrics, and perform customer segmentation using K-Means clustering. The insights generated support explainable, data-driven marketing strategies and are presented through interactive dashboards and reports.

## Planned Technology Stack

- **Data Processing & Analytics:** Python, Pandas, NumPy
- **Data Visualization:** Matplotlib, Seaborn, Plotly
- **Machine Learning:** Scikit-learn
- **Database & Querying:** PostgreSQL, SQL
- **Prototyping & EDA:** Jupyter Notebook
- **Business Intelligence:** Power BI
- **Web Application:** Streamlit
- **Testing & Quality Assurance:** pytest
- **Version Control & CI/CD:** Git, GitHub, GitHub Actions

## Project Status

**Phases 0–11 Completed** — Data ingestion, cleaning, PostgreSQL analytical database, SQL layer, RFM analysis, K-Means customer segmentation, business insights, and multi-page Streamlit web application are fully implemented, verified with 165+ automated tests, and documented.

## Streamlit Interactive Web Application

CustomerLens features a portfolio-grade, multi-page Streamlit web application for interactive customer analytics, behavioral distribution analysis, and strategic marketing exploration.

### Application Pages
1. **Home (`Home.py`):** Executive overview, end-to-end analytical workflow roadmap, verified invariants, and technology stack.
2. **Executive Overview (`1_Executive_Overview.py`):** High-level KPI cards, monthly revenue velocity, top geographic markets, repeat purchase leverage, and evidence-based executive insights.
3. **Customer Segmentation (`2_Customer_Segmentation.py`):** Behavioral segment scorecard, RFM profile comparisons, $K=2..10$ clustering diagnostics, and interactive cluster explorer.
4. **RFM Analysis (`3_RFM_Analysis.py`):** Continuous distribution profiles (raw vs. log1p scale), bivariate scatters, quintile score distributions, and interactive behavioral threshold sliders.
5. **Marketing Insights (`4_Marketing_Insights.py`):** Segment opportunity cards (`Protect & Grow`, `Nurture`, `Develop`, `Reactivate`), controlled A/B experimentation designs, and risk caveats.
6. **Customer Explorer (`5_Customer_Explorer.py`):** Multi-criteria customer search, filterable accounts grid, and single-account factual behavioral detail cards.

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit application
streamlit run app/Home.py
```

### Application Screenshots
<!-- Screenshots placeholder for portfolio demonstration -->
*Interactive multi-page dashboard running on `http://localhost:8501`.*
