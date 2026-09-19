# Streamlit Interactive Analytics Application
## CustomerLens — Customer Segmentation & Targeted Marketing Analytics

---

## 1. Purpose

The **CustomerLens Streamlit Application** is a professional, portfolio-grade web presentation and exploration platform built on top of the completed CustomerLens analytical pipeline. It allows hiring managers, data science interviewers, BI analysts, and marketing executives to interactively explore empirical customer segmentation findings, RFM behavioral dynamics, and strategic commercial opportunities.

### Key Operational Philosophy
The application serves strictly as a **presentation and exploration layer**. It directly consumes validated, precomputed analytical datasets generated in Phases 4 through 10. It does **not** re-execute expensive clustering models, retrain machine learning algorithms on startup, or recompute baseline features on widget interactions.

---

## 2. Architecture & File Structure

The application adopts Streamlit's native multi-page application architecture:

```
app/
├── Home.py                             # Landing page: project overview, methodology, tech stack
├── data_loader.py                      # Central cached data loading with @st.cache_data
├── utils.py                            # Pure formatting, KPI calculation, and filtering helpers
├── components/                         # Modular, reusable presentation components
│   ├── __init__.py
│   ├── charts.py                       # Matplotlib / Seaborn visualization functions
│   ├── filters.py                      # Global sidebar filters and branding controls
│   └── metrics.py                      # KPI card containers and segment scorecards
└── pages/                              # Analytical application pages
    ├── 1_Executive_Overview.py         # Top-line financial KPIs, monthly velocity, Pareto analysis
    ├── 2_Customer_Segmentation.py      # K-Means diagnostics, segment scorecard, cluster explorer
    ├── 3_RFM_Analysis.py               # Feature distributions, log1p scaling, score heatmaps
    ├── 4_Marketing_Insights.py         # Hypothesis matrix, experimentation designs, risk caveats
    └── 5_Customer_Explorer.py          # Searchable data grid and single-customer detail cards
```

---

## 3. Application Pages

### Home (`app/Home.py`)
- **Executive Mission:** Introduces CustomerLens, framing customer segmentation as a balance of quantitative modeling and business actionability.
- **Methodology Flowchart:** Step-by-step visual progression from raw transactions $\rightarrow$ data cleaning $\rightarrow$ PostgreSQL analytics $\rightarrow$ EDA $\rightarrow$ RFM scoring $\rightarrow$ K-Means clustering $\rightarrow$ business segment mapping $\rightarrow$ marketing opportunities.
- **Platform Invariants:** Highlights verified population metrics (4,338 customers, 18,532 orders, £8,887,208.89 revenue).
- **Scientific Integrity Notice:** Explicit disclaimer that the app presents descriptive analytics and testable hypotheses without claiming causal marketing impact.

### Page 1 — Executive Overview (`app/pages/1_Executive_Overview.py`)
- **Top KPI Cards:**
  - *Active Customers:* 4,338
  - *Completed Orders:* 18,532
  - *Gross Revenue:* £8,887,208.89
  - *Average Order Value (AOV):* £479.56
  - *Repeat Buyer Rate:* 65.58% (driving 91.94% of orders and 93.09% of sales)
- **Visual Dashboards:**
  1. *Monthly Revenue Velocity:* 13-month sales trajectory showing Q4 wholesale restocking surge.
  2. *Geographic Distribution:* Top revenue contributing countries (UK domestic vs. European exports).
  3. *Customer vs. Revenue Disparity:* Side-by-side bar charts illustrating top-tier concentration.
  4. *Repeat vs. One-Time Buyers:* Order and revenue leverage comparison.
  5. *Revenue Concentration Index:* Multiplier showing segment revenue density relative to customer volume.
- **Evidence-Based Observations:** Dynamic, data-grounded insights explaining Pareto dynamics.

### Page 2 — Customer Segmentation (`app/pages/2_Customer_Segmentation.py`)
- **Segment Scorecard:** Complete demographic and financial table across the 4 personas (Customer Count, Customer %, Revenue, Revenue %, Median Recency, Median Frequency, Median Spend).
- **Behavioral Comparison:** 3-panel bar charts comparing median Recency, Frequency, and Monetary spend.
- **K-Means Model Selection Diagnostics:**
  - Complete scorecard table evaluating candidate models from $K=2$ through $K=10$ across Inertia, Silhouette Score, Calinski-Harabasz Index, and Davies-Bouldin Index.
  - Elbow curve and Silhouette score plots.
  - Expandable explanation documenting why $K=4$ was selected as a **business-oriented solution** (balancing metrics, cluster balance, and interpretability).
- **Interactive Cluster Explorer:** Dropdown selector allowing users to inspect individual cluster archetypes, spend profiles, and commercial opportunities.

### Page 3 — RFM Analysis (`app/pages/3_RFM_Analysis.py`)
- **Operational Definitions:** Explains mathematical formulation of Recency (days to anchor `2011-12-10`), Frequency (completed invoices), and Monetary spend (gross sales).
- **Distribution Profiles:** Histograms with KDE curves featuring an interactive toggle between Raw Empirical Scale and Variance-Stabilized Log Scale ($\log(x + 1)$).
- **Bivariate Scatters:** Log-scale scatter plots evaluating Frequency vs. Spend and Recency vs. Spend.
- **Quintile Score Breakdown:** Bar charts displaying distribution of discrete quintile scores ($1 \dots 5$) across R, F, and M.
- **Interactive Behavioral Sliders:** Dynamic filtering by minimum spend, minimum frequency, and maximum recency.

### Page 4 — Marketing Insights (`app/pages/4_Marketing_Insights.py`)
- **Strategy & Opportunity Cards:** Detailed operational guidance for each persona:
  - *High-Value Engaged (`Protect & Grow`):* Dedicated account management, automated restocking SLAs, and margin preservation.
  - *Established Valuable (`Nurture`):* Basket expansion incentives (£500+ order threshold discounts) and category cross-selling.
  - *Recent Developing (`Develop`):* Automated 21-day onboarding sequences to convert first-time buyers into repeat spenders.
  - *Low-Engagement / Reactivation (`Reactivate`):* Zero-marginal-cost digital win-back sequences and email cadence optimization.
- **Controlled Experimentation Framework:** Detailed A/B testing matrix defining target populations, proposed treatment mechanisms, uncontacted control baselines, primary KPIs, and downside risk guardrails.
- **Interactive Deep-Dive:** Selector displaying individual segment profiles and operational workflows.

### Page 5 — Customer Explorer (`app/pages/5_Customer_Explorer.py`)
- **Account Search & Multi-Attribute Filters:** Instant search by `customerid` with combined filtering across business segments, action categories, countries, spend, frequency, and recency.
- **Filterable Data Grid:** Paginated, sortable table displaying verified customer records with formatted currency and days.
- **Individual Customer Detail Panel:** Metric cards displaying single-customer Recency, Frequency, Spend, and RFM Score, accompanied by a factual, plain-language behavioral interpretation.

---

## 4. Data Sources

The application reads strictly from precomputed, verified files in `data/processed/`:

| Dataset File | Analytical Phase | Record Count | Primary Purpose |
| :--- | :---: | :---: | :--- |
| `customer_transactions.csv` | Phase 5 | 392,692 rows | Underlying line-item transaction fact table for monthly and country velocity. |
| `rfm_customer_metrics.csv` | Phase 8 | 4,338 rows | Continuous RFM features and discrete quintile scores. |
| `customer_clusters.csv` | Phase 9 | 4,338 rows | Customer cluster assignments with 2D PCA projections. |
| `cluster_profiles.csv` | Phase 9 | 4 rows | Aggregated demographic and financial statistics across clusters. |
| `clustering_metrics.csv` | Phase 9 | 9 rows | K-Means model evaluation scorecard across $K=2 \dots 10$. |
| `business_segments.csv` | Phase 10 | 4,338 rows | Customer accounts mapped to business personas and action categories. |
| `segment_summary.csv` | Phase 10 | 4 rows | Executive segment summary combining profiles and strategic descriptions. |
| `marketing_opportunities.csv` | Phase 10 | 4 rows | Structured experimentation matrix and proposed measurement KPIs. |

---

## 5. Performance & Caching Strategy

To ensure sub-second response times and prevent resource exhaustion:
1. **Central Data Loader (`app/data_loader.py`):** Every data-loading function is decorated with `@st.cache_data(show_spinner=False)`. DataFrames are parsed from disk once on initial page access and stored in memory.
2. **Zero Model Retraining:** K-Means clustering, feature scaling, and PCA projections are never computed on user interaction; the precomputed outputs are consumed directly.
3. **Optimized Plotting:** Matplotlib figures are generated using pure, stateless functions in `app/components/charts.py` and closed cleanly to prevent memory leaks.
4. **Column Normalization:** Transaction datasets normalize column headers to lowercase on load, ensuring consistency across modules.

---

## 6. Global Filtering & State Management

- **Page-Level Scoping:** Filters rendered in the sidebar apply dynamically to the active page view.
- **Graceful Empty State Handling:** If a combination of filters yields zero matching records, charts display an informative message (*"No data matches the current filters"*) and detail panels show `st.warning()` without throwing unhandled runtime exceptions.
- **Non-Destructive Slicing:** Filtering operates on in-memory DataFrame copies, preserving cached source datasets intact.

---

## 7. Analytical Limitations & Guardrails

To preserve scientific rigor and avoid deceptive portfolio claims:
1. **Descriptive, Not Predictive:** Inactivity is framed as "lower recent engagement" or "higher recency". The app does not display churn probabilities or claim that customers "will churn".
2. **Hypotheses, Not Guaranteed ROI:** Marketing opportunities are explicitly designated as testable business hypotheses that require empirical A/B validation.
3. **No Demographic Invention:** The source dataset lacks customer age, gender, income, or household data; no demographic attributes are inferred or displayed.
4. **No Artificial Product Categories:** Transactions contain `StockCode` and `Description`, but no formal taxonomies; no fabricated product categories are presented.
5. **Right-Censored Data:** December 2011 contains only 9 days of activity, truncating the retail holiday peak.

---

## 8. Running the Application Locally

Ensure project dependencies are installed from `requirements.txt`:

```bash
# Install dependencies
pip install -r requirements.txt

# Launch Streamlit application
streamlit run app/Home.py
```

The application will launch on `http://localhost:8501`.
