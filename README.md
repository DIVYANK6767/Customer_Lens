# CustomerLens — E-Commerce Customer Segmentation & Marketing Analytics

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-336791.svg)](https://www.postgresql.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-PBIR_Validated-F2C811.svg)](https://powerbi.microsoft.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/pytest-170_tests--169_passed-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end portfolio project combining **deterministic data cleaning**, **relational SQL analytics**, **unsupervised machine learning (K-Means)**, an **interactive multi-page Streamlit web application**, and an **enterprise-style 4-page Power BI report** (PBIR validated).

CustomerLens transforms **541,909 raw e-commerce transaction records** into validated customer behavioral personas and transparent, hypothesis-driven marketing opportunities.

🚀 Live Demo: https://customerlens-app.streamlit.app/

### Project Links
- **Live Streamlit App:** https://customerlens-app.streamlit.app/
- **GitHub Repository:** https://github.com/DIVYANK6767/Customer_Lens

---

## Table of Contents

- [1. Executive Summary & Verified Headline Baselines](#1-executive-summary--verified-headline-baselines)
- [2. Business Problem & Analytical Inquiries](#2-business-problem--analytical-inquiries)
- [3. End-to-End System Architecture](#3-end-to-end-system-architecture)
- [4. Dataset Provenance & Deterministic Cleaning](#4-dataset-provenance--deterministic-cleaning)
- [5. Relational SQL & PostgreSQL Analytics Layer](#5-relational-sql--postgresql-analytics-layer)
- [6. Exploratory Data Analysis & Macro Trends](#6-exploratory-data-analysis--macro-trends)
- [7. RFM Feature Engineering & Quintile Scoring](#7-rfm-feature-engineering--quintile-scoring)
- [8. Unsupervised Machine Learning (K-Means Clustering)](#8-unsupervised-machine-learning-k-means-clustering)
- [9. Validated Business Segments & Behavioral Scorecard](#9-validated-business-segments--behavioral-scorecard)
- [10. Data-Informed Marketing Opportunity Hypotheses](#10-data-informed-marketing-opportunity-hypotheses)
- [11. Power BI Portfolio Report (4 Pages, PBIR Validated)](#11-power-bi-portfolio-report-4-pages-pbir-validated)
- [12. Streamlit Multi-Page Web Application](#12-streamlit-multi-page-web-application)
- [13. Quality Assurance & Automated Test Suite (170 Tests)](#13-quality-assurance--automated-test-suite-170-tests)
- [14. Repository Directory Structure](#14-repository-directory-structure)
- [15. Installation & Local Reproduction Guide](#15-installation--local-reproduction-guide)
- [16. Methodological Boundaries & Limitations](#16-methodological-boundaries--limitations)
- [17. Technologies Used](#17-technologies-used)

---

## 1. Executive Summary & Verified Headline Baselines

CustomerLens analyzes verified e-commerce customer purchasing patterns between **December 1, 2010 and December 9, 2011**. All metrics reconcile across Python dataframes, PostgreSQL analytical queries, the Streamlit app, and the Power BI semantic model.

### Key Verified Commercial Invariants

| Dimension / Metric | Ground Truth Value | Business Interpretation |
| :--- | :--- | :--- |
| **Raw Source Records** | **541,909 rows** | Total transactions logged in the raw transactional dump. |
| **Completed Customer Purchases** | **392,692 rows** | Verified merchandise sales associated with identified customer accounts. |
| **Active Customer Accounts** | **4,338 customers** | Distinct commercial accounts with at least one completed purchase. |
| **Completed Customer Orders** | **18,532 orders** | Unique customer-invoice purchasing checkout events. |
| **Total Reconciled Revenue** | **£8,887,208.89** | Net completed retail merchandise sales across identified customers. |
| **Average Order Value (AOV)** | **£479.56** | Mean completed revenue per order invoice (£8,887,208.89 / 18,532). |
| **Revenue per Customer** | **£2,048.69** | Mean customer annual spend (heavily right-skewed by top-spending accounts). |
| **Median Customer Spend** | **£668.57** | 50% of customers spent under £668.57 (demonstrating positive skew). |
| **Repeat Customer Count** | **2,845 customers** | Accounts with 2 or more completed orders (65.58% repeat customer rate). |
| **One-Time Customer Count** | **1,493 customers** | Accounts with exactly 1 completed purchase (34.42%). |
| **Geographic Core (UK)** | **£7,308,391.55 (88.80%)** | United Kingdom represents 3,921 active customers (EDA baseline: 88.80% share; fact table: £7,285,024.64 / 81.97%). |
| **Revenue Concentration** | **Top 16.51% $\rightarrow$ 65.05%** | 716 high-value accounts generate £5.78M of total revenue (3.94x density). |

---

## 2. Business Problem & Analytical Inquiries

### The Business Challenge
In multi-category retail e-commerce, generic "one-size-fits-all" marketing generates significant inefficiencies:
1. **Capital Misallocation:** Over-discounting loyal repeat buyers who would purchase organically at full price.
2. **Under-Servicing Key Accounts:** Failing to provide dedicated SLA support and replenishment schedules to accounts generating the majority of revenue.
3. **Budget Waste on Low-Intent Churn:** Allocating expensive paid acquisition or outbound resources toward single-order buyers with a low historical conversion baseline.

### Core Analytical Inquiries Addressed
- **Revenue Concentration:** What share of enterprise turnover is concentrated within top customer tiers?
- **Retention & Repurchase Velocity:** How rapidly do introductory buyers convert into habitual multi-order customers?
- **Behavioral Cohort Discovery:** Can unsupervised machine learning uncover distinct customer archetypes beyond arbitrary manual score cuts?
- **Hypothesis-Driven Marketing:** What concrete, non-demographic marketing tactics align with the observed recency, order cadence, and basket spend of each customer segment?

---

## 3. End-to-End System Architecture

```text
                               CUSTOMERLENS ARCHITECTURE

   [Raw CSV Data]            UCI Online Retail (541,909 raw records)
          │
          ▼
  [Python Ingestion]         src/data_loader.py (Schema validation, encoding, typing)
          │
          ▼
 [Deterministic Cleaning]    src/cleaning.py (Classification & validation pipeline:
                             drops duplicates, segregates non-sales -> 392,692 rows)
          │
          ├───────────────────────────────┬───────────────────────────────┐
          ▼                               ▼                               ▼
 [PostgreSQL Analytical DB]      [RFM Feature Store]          [Machine Learning]
  analytics schema                src/rfm.py                   src/clustering.py
  sql/schema.sql                  Anchor: 2011-12-10           log1p transformation
  sql/customer_metrics.sql        R, F, M calculation          StandardScaler
  sql/business_questions.sql      Quintile/Tier scoring        K-Means (K=4 validated)
          │                               │                               │
          └───────────────────────────────┼───────────────────────────────┘
                                          ▼
                             [Business Segmentation]
                              src/segmentation.py & src/insights.py
                              4 Commercial Personas + Strategy Matrix
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     [Interactive Web App]                            [Power BI Portfolio Report]
      app/Home.py (6 Pages)                            powerbi/CustomerLens.pbip
      Streamlit Multi-Page                             4 Pages (PBIR Validated)
      Cached Exploration & Diagnostics                 Star Schema & 22 DAX Measures
```

---

## 4. Dataset Provenance & Deterministic Cleaning

### Data Source
- **Origin:** UCI Machine Learning Repository — *Online Retail Data Set*.
- **Temporal Window:** 2010-12-01 08:26:00 to 2011-12-09 12:50:00.
- **Attributes:** `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country`.

### Deterministic Cleaning Pipeline & Data Reconciliation

The cleaning pipeline (`src/cleaning.py`) executes deterministic business rules to normalize transactional records, classify operational activity, and extract valid customer purchase transactions:

| Metric / Dimension | Raw Dataset (Before) | Clean Transactions (`clean_transactions.csv`) | Customer Analytics (`customer_transactions.csv`) | Notes & Business Rationale |
| :--- | :---: | :---: | :---: | :--- |
| **Total Rows** | **541,909** | **536,641** | **392,692** | 5,268 exact duplicates removed; 143,949 non-customer/non-sale rows segregated. |
| **Percentage Retained** | 100.00% | **99.03%** | **72.46%** | 72.46% of raw lines represent identified customer retail purchases. |
| **Exact Duplicate Rows** | 5,268 | **0** | **0** | Dropped identical line items across all 8 attributes. |
| **Missing CustomerID Rows** | 135,080 (24.93%) | **135,037** (25.16%) | **0** (0.00%) | Anonymous transactions preserved in clean set; excluded from customer RFM. |
| **Missing Description Rows** | 1,454 (0.27%) | **1,454** (0.27%) | **0** (0.00%) | All belonged to adjustments/anonymous rows; 0 in customer purchases. |
| **Cancellation Rows (`'C'` prefix)** | 9,288 | **9,251** | **0** | Excluded from completed sales; preserved in clean set for return analysis. |
| **Adjustment Rows** | 1,338 | **1,339** | **0** | 3 bad-debt entries ('A') + 1,336 warehouse write-offs; excluded from sales. |
| **Zero UnitPrice Rows (`0.0`)** | 2,515 | **2,510** | **0** | Classified as Invalid (1,174) or Adjustments (1,336); excluded from sales. |
| **Negative UnitPrice Rows (`< 0`)** | 2 | **2** | **0** | Bad-debt adjustments (-£11,062.06); excluded from sales. |
| **Negative Quantity Rows (`< 0`)** | 10,624 | **10,587** | **0** | 9,251 cancellations + 1,336 adjustments; excluded from sales. |
| **Zero Quantity Rows (`= 0`)** | 0 | **0** | **0** | None present in raw or cleaned data. |
| **Completed Sale Rows** | — | **524,877** | **392,692** | 524,877 sales store-wide; 392,692 have verified CustomerID. |
| **Non-Sale / Excluded Rows** | — | **11,764** | **143,949** | Cancellations (9,251) + Adjustments (1,339) + Invalid (1,174). |
| **Unique Identified Customers** | 4,372 | 4,372 | **4,338** | 34 customers had only cancellations or zero-price entries. |
| **Unique Invoices / Orders** | 25,900 | 25,900 | **18,532** | Distinct completed purchase orders placed by identified customers. |
| **Total Monetary Revenue** | — | — | **£8,887,208.89** | Net completed purchase expenditure across identified customers. |

#### Operational Classification Reconciliation (Clean Set: 536,641 Rows)
$$\text{Clean Total (536,641)} = \text{Completed Sales (524,877)} + \text{Cancellations (9,251)} + \text{Adjustments (1,339)} + \text{Invalid Records (1,174)}$$

---

## 5. Relational SQL & PostgreSQL Analytics Layer

A dedicated **PostgreSQL** schema (`analytics`) acts as the relational analytical store:

- **Schema Definition (`sql/schema.sql`):** Defines `analytics.customer_transactions` with strict check constraints guarding positive quantities, positive unit prices, and non-null customer keys.
- **Integrity Validation (`sql/validation.sql`):** Automatically verifies row count, distinct customer count, distinct order count, and revenue totals post-ingestion.
- **Customer Feature Suite (`sql/customer_metrics.sql`):**
  - Lifetime spend, order volume, and average order values.
  - Windowed customer revenue rankings (`RANK()`, `DENSE_RANK()`).
  - Cumulative Lorenz curve distribution via `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
  - Repeat customer breakdown: **2,845 repeat buyers (65.58%)** vs. **1,493 one-time buyers (34.42%)**.
- **Revenue Velocity Suite (`sql/revenue_analysis.sql`):**
  - Month-over-Month growth metrics using `LAG()` window functions.
  - Diurnal weekday and hourly sales distribution.
  - Basket spend percentiles using `PERCENTILE_CONT(0.25, 0.50, 0.75, 0.90, 0.95, 0.99)`.
- **Commercial Business Questions (`sql/business_questions.sql`):** 20 production SQL queries answering executive questions on customer concentration, product affinity, and churn latency.

---

## 6. Exploratory Data Analysis & Macro Trends

Key findings from `notebooks/03_eda.ipynb` and `src/eda.py`:

1. **Monthly Turnover Velocity:** Revenue peaked in **November 2011** (approximately **£1.16M across completed orders**). The dataset does not contain marketing, inventory, or campaign-attribution data sufficient to establish the underlying cause of this increase.
2. **Geographic Concentration:**
   - **United Kingdom:** £7,308,391.55 (88.80% of total revenue in EDA baseline; 3,921 active customers. The transaction fact table reflects £7,285,024.64 / 81.97% across 3,920 accounts).
   - **Top International Markets:** Netherlands (£285.4k), EIRE (£265.5k), Germany (£228.9k), France (£209.7k), Australia (£138.5k). International accounts exhibit significantly higher Average Order Values, consistent with bulk or cross-border purchasing patterns.
3. **Basket Spend Skewness:**
   - Median transaction unit price: **£2.08**.
   - Median line-item quantity: **6 units**.
   - Extreme right skew across order values justifies logarithmic transformation before machine learning.

---

## 7. RFM Feature Engineering & Quintile Scoring

Features were calculated at the customer grain with reference anchor **`2011-12-10 12:50:00`** (`MAX(InvoiceDate) + 1 day`):

- **Recency ($R$):** Days elapsed since customer's most recent completed order.
- **Frequency ($F$):** Total count of unique completed orders (`InvoiceNo`).
- **Monetary ($M$):** Total net purchase value (£) across all completed orders.

### Score Distributions

To accommodate discrete clustering at $F \le 2$, scoring employs quintiles for $R$ and $M$ and explicit boundary tiers for $F$:

- **Recency Score ($R\_score \in [1, 5]$):** Quintile-based (1 = Least Recent / Inactive, 5 = Most Recent / Highly Active).
- **Frequency Score ($F\_score \in [1, 4]$):**
  - Tier 1: $F \in [1, 2]$ orders (2,328 customers; captures 1,493 one-time buyers and 835 two-order buyers due to merged quantile boundaries).
  - Tier 2: $F = 3$ orders (508 customers).
  - Tier 3: $F \in [4, 6]$ orders (802 customers).
  - Tier 4: $F \ge 7$ orders (700 customers).
- **Monetary Score ($M\_score \in [1, 5]$):** Quintile-based (1 = Lowest Lifetime Spend, 5 = Highest Lifetime Spend).

### Heuristic RFM Segments (8 Classic Personas)
Mapped via validated boundary rules into: `Champions` (578), `Loyal Customers` (721), `Potential Loyalists` (210), `Recent Customers` (527), `Need Attention` (594), `At Risk` (203), `Hibernating` (676), and `Lost` (829) $\rightarrow$ Sum = **4,338 customers**.

---

## 8. Unsupervised Machine Learning (K-Means Clustering)

While manual RFM cuts provide operational heuristics, they introduce arbitrary thresholds. CustomerLens deploys unsupervised **K-Means clustering** over continuous feature space to discover organic data density groupings.

### Mathematical Preprocessing Pipeline
1. **Logarithmic Scaling:** Given severe positive skewness, features are transformed via natural logarithm:
   $$X_{\text{trans}} = \ln(X + 1)$$
2. **Standardization:** Transformed features are centered to zero mean and unit variance:
   $$Z = \frac{X_{\text{trans}} - \mu}{\sigma}$$
3. **Clustering Specification:** Scikit-learn `KMeans(n_clusters=4, init='k-means++', n_init=10, max_iter=300, random_state=42)`.

### Multi-Criteria Cluster Validation ($K = 2 \dots 10$)

Clustering diagnostics were executed on standardized $\ln(X + 1)$ RFM features across candidate values $K \in [2, 10]$, producing the verified metrics recorded in `data/processed/clustering_metrics.csv`:

| Clusters ($K$) | Inertia (WCSS) | Silhouette Score | Calinski-Harabasz | Davies-Bouldin | Min Cluster Size | Max Cluster Size | Size Ratio |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$K=2$** | 6,483.60 | **0.4328** | **4,367.32** | **0.8925** | 1,667 | 2,671 | 1.60 |
| **$K=3$** | 4,869.58 | 0.3369 | 3,625.25 | 1.0471 | 763 | 1,877 | 2.46 |
| **$K=4$** | **3,939.26** | **0.3374** | **3,328.14** | **1.0086** | **716** | **1,618** | **2.26** |
| **$K=5$** | 3,297.20 | 0.3161 | 3,192.43 | 0.9880 | 330 | 1,185 | 3.59 |
| **$K=6$** | 2,855.27 | 0.3142 | 3,082.59 | 1.0134 | 305 | 987 | 3.24 |
| **$K=7$** | 2,548.86 | 0.3092 | 2,963.76 | 0.9826 | 229 | 891 | 3.89 |
| **$K=8$** | 2,336.45 | 0.3012 | 2,826.87 | 0.9923 | 217 | 847 | 3.90 |
| **$K=9$** | 2,166.75 | 0.2934 | 2,709.07 | 1.0316 | 182 | 790 | 4.34 |
| **$K=10$**| 2,000.54 | 0.2783 | 2,647.45 | 1.0214 | 93 | 641 | 6.89 |

### Selection Justification & Analytical Trade-Offs

Selecting $K$ in customer segmentation requires distinguishing mathematical extrema from practical commercial actionability:

1. **Why not $K=2$?** While $K=2$ achieves the highest Silhouette score (0.4328) and lowest Davies-Bouldin index (0.8925), it merely bifurcates the population into a coarse "High Engagement" vs. "Low Engagement" split. This lumps recent low-spend trial buyers with lapsed high-value customers, making targeted marketing impossible.
2. **Why $K=4$ over $K=3$?** Moving from $K=3$ to $K=4$ yields a distinct local peak in the Silhouette coefficient (increasing from 0.3369 to 0.3374), improves the Davies-Bouldin index from 1.0471 down to 1.0086, and reduces Inertia by 930.32 points (a 19.1% drop). Operationally, $K=4$ separates introductory trial buyers (Recent Developing) from established repeat buyers (Established Valuable), which $K=3$ fails to distinguish.
3. **Why not $K \ge 5$?** Moving to $K=5$ degrades the Silhouette score down to 0.3161 and fragments the high-value cohort into an unstable micro-cluster of only 330 accounts (7.6% of the base). At $K \ge 6$, minimum cluster size drops below 300 accounts, and silhouette scores degrade monotonically toward 0.2783 without revealing distinct actionable behavioral personas.

**$K=4$ was selected as a business-oriented balance** between cluster separation, diminishing returns in inertia, cluster size stability, and interpretability.

---

## 9. Validated Business Segments & Behavioral Scorecard

The 4 machine learning clusters map directly to validated, explainable commercial personas:

```text
                               BUSINESS SEGMENT SUMMARY
┌──────────────────────────────┬────────────┬──────────┬────────────────┬──────────┬──────────────┐
│ Business Segment             │ Customers  │ Cust %   │ Revenue (£)    │ Rev %    │ Density Mult │
├──────────────────────────────┼────────────┼──────────┼────────────────┼──────────┼──────────────┤
│ 1. High-Value Engaged        │ 716        │ 16.51%   │ £5,781,509.02  │ 65.05%   │ 3.94x        │
│ 2. Established Valuable      │ 1,170      │ 26.97%   │ £2,092,321.70  │ 23.54%   │ 0.87x        │
│ 3. Recent Developing         │ 834        │ 19.23%   │ £465,608.17    │ 5.24%    │ 0.27x        │
│ 4. Low-Engagement / Reactiv. │ 1,618      │ 37.30%   │ £547,770.00    │ 6.16%    │ 0.17x        │
├──────────────────────────────┼────────────┼──────────┼────────────────┼──────────┼──────────────┤
│ TOTAL RECONCILED             │ 4,338      │ 100.00%  │ £8,887,208.89  │ 100.00%  │ 1.00x        │
└──────────────────────────────┴────────────┴──────────┴────────────────┴──────────┴──────────────┘
```

### Behavioral Medians & Cohort Characteristics

1. **High-Value Engaged (Cluster 3 — "Protect & Grow"):**
   - *Observed Profile:* **Median Recency: 8.0 days**, **Median Orders: 10.0**, **Median Spend: £3,730.61** (Mean: £8,074.73).
   - *Significance:* 16.51% of customers account for 65.05% of sales. Primary commercial revenue contributor.
2. **Established Valuable (Cluster 2 — "Nurture"):**
   - *Observed Profile:* **Median Recency: 57.0 days**, **Median Orders: 4.0**, **Median Spend: £1,340.08** (Mean: £1,788.31).
   - *Significance:* Stable repeat purchasers with consistent basket sizes and moderate latency.
3. **Recent Developing (Cluster 0 — "Develop"):**
   - *Observed Profile:* **Median Recency: 17.0 days**, **Median Orders: 2.0**, **Median Spend: £481.03** (Mean: £558.28).
   - *Significance:* Recently acquired or activated buyers showing early purchase habituation.
4. **Low-Engagement / Reactivation (Cluster 1 — "Reactivate"):**
   - *Observed Profile:* **Median Recency: 174.5 days**, **Median Orders: 1.0**, **Median Spend: £293.78** (Mean: £338.55).
   - *Significance:* Largest group by customer volume (37.30%), but generates only 6.16% of revenue. 78%+ completed only one purchase.

---

## 10. Data-Informed Marketing Opportunity Hypotheses

> **Analytical Governance Reminder:** Marketing recommendations are formulated as *data-informed hypotheses* derived from observed transaction patterns. They do NOT represent measured campaign lift, conversion uplift, ROI, CLV, CAC, or churn predictions (as campaign exposure data was not tracked in the source transactional log).

### Strategic Marketing Matrix

| Business Segment | Action Category | Recommended Operational Tactic | Candidate Evaluation Metric | Implementation Caveat & Risk |
| :--- | :--- | :--- | :--- | :--- |
| **High-Value Engaged** | **Protect & Grow** | Dedicated account management, priority delivery SLAs, quarterly replenishment scheduling. | 90-day account retention rate, order frequency consistency, gross margin per account. | Severe concentration risk (65.05% in 716 accounts); avoid margin-eroding price discounting. |
| **Established Valuable**| **Nurture** | Tiered spend threshold incentives (£500+ order thresholds) and category cross-selling. | Quarterly re-order velocity, Average Order Value (AOV), repurchase frequency. | Incentives must maintain high basket minimums to avoid subsidizing organic orders. |
| **Recent Developing** | **Develop** | Automated post-purchase onboarding emails (Day 7 check-in, Day 14 discovery, Day 21 restock).| 60-day repeat conversion rate, time-to-second-order, early customer revenue growth. | Risk of email fatigue; messages must emphasize product utility rather than generic markdowns. |
| **Low-Engagement** | **Reactivate** | Automated low-cost seasonal win-back emails, clearance catalog alerts, preference opt-outs. | Reactivation response rate, incremental margin per reactivated account, unsubscribe rate.| Over 78% made only 1 order; paid acquisition or high-cost outbound tactics should be evaluated carefully because this segment has relatively low observed historical spend and limited repeat purchasing in the available transaction data. |

---

## 11. Power BI Portfolio Report (4 Pages, PBIR Validated)

A production-oriented Power BI portfolio report resides in `powerbi/CustomerLens.pbip` (and compiled standalone `CustomerLens.pbix`), utilizing Power BI Enhanced Report Format (**PBIR**).

### Architectural Properties
- **Validation Status:** Validated via `@microsoft/powerbi-report-authoring-cli validate` with **0 errors, 0 warnings**.
- **Model Architecture:** Clean Star Schema with 3 active 1-to-many / 1-to-1 relationships and zero circular dependencies.
- **DAX Measures:** 22 validated, non-volatile measures (all formatted with explicit currency `£#,##0.00`, percentages `0.0%`, or integers `#,##0`).
- **Canvas Specifications:** 16:9 widescreen ($1920 \times 1080$ px) with uniform header ribbons and aligned filter slicers.

```text
                            POWER BI REPORT STRUCTURE

   Page 1: Executive Overview      Page 2: Customer Segmentation
   ┌────────────────────────────┐  ┌────────────────────────────┐
   │ [Header]  [Date/Ctry/Seg]  │  │ [Header]  [Date/Ctry/Seg]  │
   │ [5 KPI Cards: Rev,Cust,AOV]│  │ [4 KPI Cards: Cust,Rev,AOV]│
   │ [MoM Trend] [Country Bars] │  │ [Volume vs Rev Share Bars] │
   │ [Retention] [Segment Donut]│  │ [Segment Scorecard Matrix] │
   └────────────────────────────┘  └────────────────────────────┘

   Page 3: RFM Analysis           Page 4: Marketing Opportunities
   ┌────────────────────────────┐  ┌────────────────────────────┐
   │ [Header]  [Date/Ctry/Seg]  │  │ [Header]  [Date/Ctry/Seg]  │
   │ [5 Median/Mean KPI Cards]  │  │ [4 KPI Cards: Cust,Rev,AOV]│
   │ [R vs M Scatter] [Log M]   │  │ [Sizing Table] [Action Bar]│
   │ [R-Score] [F-Score] [Table]│  │ [Strategy Matrix] [Tactics]│
   └────────────────────────────┘  └────────────────────────────┘
```

### Report Page Overview

1. **Page 1 — Executive Overview (14 Visual Containers):**
   - High-level KPIs (`Total Revenue`, `Total Customers`, `Total Orders`, `AOV`, `Repeat Customer Rate`).
   - Monthly turnover velocity combo chart and geographic distribution bar chart (UK: £7,308,391.55 / 88.80% in EDA baseline; £7,285,024.64 / 81.97% in transaction fact table).
   - Customer retention split (2,845 repeat vs 1,493 one-time buyers) and revenue concentration indices.
2. **Page 2 — Customer Segmentation (13 Visual Containers):**
   - Side-by-side customer count share vs. revenue contribution disparity charts.
   - Comprehensive 10-column segment scorecard matrix.
   - Median spend comparison across the 4 validated business segments.
3. **Page 3 — RFM Analysis (16 Visual Containers):**
   - 5 behavioral benchmark cards (`Median Recency: 51d`, `Median Frequency: 2`, `Median Monetary: £668.57`, `Average Recency: 92.5d`, `Average Monetary: £2,048.69`).
   - Customer Recency vs. Monetary spend scatter plot (bubble size = order volume).
   - Dedicated unbinned customer monetary distribution using logarithmic horizontal scaling (`logAxisScale: true`).
   - Score distribution column charts correctly titled *"Recency Score Distribution"* and *"Frequency Score Distribution"*.
   - Granular customer-level transactional detail table.
4. **Page 4 — Marketing Opportunities (13 Visual Containers):**
   - Segment opportunity sizing overview table with revenue concentration multipliers.
   - Segment revenue contribution partitioned by strategic action category (`Protect & Grow`, `Nurture`, `Develop`, `Reactivate`).
   - Direct integration of `Ref_MarketingOpportunities` strategy matrix and operational tactics table with proposed KPIs and risk caveats.

---

## 12. Streamlit Multi-Page Web Application

The interactive web application provides self-service behavioral exploration:

- **Live Deployment:** https://customerlens-app.streamlit.app/

```bash
# Launch the Streamlit application locally
streamlit run app/Home.py
```

### Application Page Directory

1. **Home (`app/Home.py`):** Executive introduction, methodology roadmap, headline commercial invariants, and data lineage.
2. **Executive Overview (`app/pages/1_Executive_Overview.py`):** Interactive KPI cards, monthly revenue velocity, top geographic markets, and Pareto analysis.
3. **Customer Segmentation (`app/pages/2_Customer_Segmentation.py`):** Behavioral scorecard, RFM profile box plots, $K=2..10$ clustering diagnostics, and interactive cluster explorer.
4. **RFM Analysis (`app/pages/3_RFM_Analysis.py`):** Continuous distribution profiles (raw vs. log1p scale), bivariate scatters, quintile score distributions, and interactive behavioral threshold sliders.
5. **Marketing Insights (`app/pages/4_Marketing_Insights.py`):** Segment opportunity cards, hypothesis evaluation frameworks, candidate metrics, and risk caveats.
6. **Customer Explorer (`app/pages/5_Customer_Explorer.py`):** Multi-criteria customer search, filterable accounts grid, and single-account factual behavioral detail cards.

---

## 13. Quality Assurance & Automated Test Suite (170 Tests)

CustomerLens includes an automated test suite executed via `pytest`:

```bash
# Run the complete test suite
pytest
```

```text
============================= test session starts =============================
collected 170 items

tests/test_cleaning.py ...................                               [ 11%]
tests/test_clustering.py .....................                           [ 23%]
tests/test_data_loader.py ..........                                     [ 29%]
tests/test_database.py ...............s                                  [ 38%]
tests/test_eda.py ................                                       [ 48%]
tests/test_insights.py ...........                                       [ 54%]
tests/test_rfm.py ........................                               [ 68%]
tests/test_segmentation.py .................                             [ 78%]
tests/test_sql_analytics.py ..............                               [ 87%]
tests/test_streamlit_data.py ......................                      [100%]

======================= 169 passed, 1 skipped in 27.90s =======================
```

### Invariant Test Enforcements
- **Row Invariance:** Asserts exactly 392,692 completed customer transaction records.
- **Population Invariance:** Asserts exactly 4,338 unique active customer accounts.
- **Order Invariance:** Asserts exactly 18,532 completed unique orders.
- **Revenue Invariance:** Asserts net customer revenue sums to £8,887,208.89 ($\pm 0.01$).
- **Segment Sum Invariance:** Asserts cluster counts ($716 + 1,170 + 834 + 1,618 = 4,338$) and cluster revenues sum to 100%.

---

## 14. Repository Directory Structure

```text
Customer_Lens/
├── .github/
│   └── workflows/
│       └── README.md              # CI/CD workflow architecture
├── app/                           # Streamlit multi-page application
│   ├── Home.py                    # Application landing page
│   ├── components/                # Modular UI widgets, cards, and charts
│   ├── data_loader.py             # Streamlit caching and data ingestion
│   ├── utils.py                   # Formatting utilities and styling helpers
│   └── pages/                     # Application subpages
│       ├── 1_Executive_Overview.py
│       ├── 2_Customer_Segmentation.py
│       ├── 3_RFM_Analysis.py
│       ├── 4_Marketing_Insights.py
│       └── 5_Customer_Explorer.py
├── data/
│   ├── raw/                       # Raw source dataset (Online_Retail.csv)
│   └── processed/                 # Deterministic analytical outputs
│       ├── clean_transactions.csv
│       ├── customer_transactions.csv
│       ├── cleaning_report.csv
│       ├── rfm_customer_metrics.csv
│       ├── customer_clusters.csv
│       ├── cluster_profiles.csv
│       ├── clustering_metrics.csv
│       ├── business_segments.csv
│       ├── segment_summary.csv
│       └── marketing_opportunities.csv
├── docs/                          # Comprehensive technical documentation
│   ├── PRD.md
│   ├── architecture.md
│   ├── data_cleaning.md
│   ├── data_cleaning_report.md
│   ├── data_dictionary.md
│   ├── eda.md
│   ├── postgresql.md
│   ├── rfm_analysis.md
│   ├── customer_segmentation.md
│   ├── business_insights.md
│   ├── powerbi_dashboard.md
│   ├── sql_analytics.md
│   └── streamlit_app.md
├── notebooks/                     # Interactive Jupyter analytical notebooks
│   ├── 03_eda.ipynb
│   ├── 04_rfm_analysis.ipynb
│   ├── 05_customer_segmentation.ipynb
│   └── 06_business_insights.ipynb
├── powerbi/                       # Enterprise-style Power BI analytical deliverables
│   ├── CustomerLens.pbip          # Power BI project file (PBIR format)
│   ├── CustomerLens.pbix          # Power BI compiled report package
│   ├── CustomerLens.Report/       # Visual container definitions & layouts
│   ├── CustomerLens.SemanticModel/# Star schema TMDL models & relationships
│   ├── dashboard_specification.md # Visual container coordinate registry
│   ├── data_dictionary.md         # Semantic model field documentation
│   └── dax_measures.md            # Verified DAX measure formulas
├── sql/                           # Relational PostgreSQL analytics layer
│   ├── schema.sql                 # DDL definitions & check constraints
│   ├── validation.sql             # Post-load invariant audit queries
│   ├── exploration.sql            # Foundational exploration queries
│   ├── customer_metrics.sql       # Windowed customer KPIs & concentration
│   ├── revenue_analysis.sql       # Time series, MoM growth, & percentiles
│   ├── rfm.sql                    # SQL-based RFM scoring logic
│   └── business_questions.sql     # 20 commercial business query solutions
├── src/                           # Reusable Python analytical modules
│   ├── data_loader.py             # CSV loading & typing
│   ├── cleaning.py                # Deterministic cleaning pipeline
│   ├── database.py                # PostgreSQL connection management
│   ├── load_to_postgres.py        # COPY ingestion loader
│   ├── eda.py                     # Statistical summaries & EDA charts
│   ├── rfm.py                     # RFM calculations & quintile scoring
│   ├── clustering.py              # Log transform, scaling, K-Means & metrics
│   ├── segmentation.py            # Business segment mapping
│   └── insights.py                # Marketing strategy matrix generation
├── tests/                         # Automated pytest test suite (170 tests)
│   ├── test_cleaning.py
│   ├── test_clustering.py
│   ├── test_data_loader.py
│   ├── test_database.py
│   ├── test_eda.py
│   ├── test_insights.py
│   ├── test_rfm.py
│   ├── test_segmentation.py
│   ├── test_sql_analytics.py
│   └── test_streamlit_data.py
├── pytest.ini                     # Test configuration
├── requirements.txt               # Pinned Python package dependencies
├── LICENSE                        # MIT License
└── README.md                      # Project master documentation
```

---

## 15. Installation & Local Reproduction Guide

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (optional, for running live relational SQL queries)
- Power BI Desktop (optional, for viewing `.pbip` or `.pbix` reports)

### 1. Clone Repository & Setup Virtual Environment
```bash
# Clone repository
git clone https://github.com/DIVYANK6767/Customer_Lens.git
cd Customer_Lens

# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Execute Automated Tests
```bash
# Run pytest to assert all mathematical and data invariants
pytest
```

### 3. Launch Streamlit Application
```bash
# Start the local Streamlit dashboard
streamlit run app/Home.py
```
*Navigate to `http://localhost:8501` in your browser.*

### 4. Inspect Power BI Deliverable
- Open `powerbi/CustomerLens.pbip` in **Power BI Desktop** (PBIR developer format).
- Alternatively, open the standalone compiled package `powerbi/CustomerLens.pbix`.

---

## 16. Methodological Boundaries & Limitations

To maintain institutional-grade analytical integrity, the following boundaries are explicitly stated:

1. **No Demographic Attributes:** The source dataset does not contain customer age, gender, income, or occupation. All segmentations reflect strictly observed transactional behavior.
2. **Absence of Cost of Goods Sold (COGS):** Turnover figures represent gross merchandise sales. Product gross margins and net profitability were not available in the public transactional log.
3. **Hypothesis vs. Causal Lift:** Marketing tactics are proposed as *data-informed hypotheses* grounded in behavioral profiles. They do not claim measured historical campaign uplift, ROI, CLV, CAC, or churn probabilities.
4. **Static Anchor Reference:** RFM calculations reference `2011-12-10` as the fixed historical cutoff date. Production deployments would utilize dynamic rolling windows.

---

## 17. Technologies Used

| Category | Technology | Purpose in CustomerLens |
| :--- | :--- | :--- |
| **Language** | **Python 3.10+** | Core programming language for ingestion, cleaning, and ML. |
| **Data Processing** | **Pandas, NumPy** | Vectorized cleaning, RFM aggregation, and matrix transformations. |
| **Machine Learning**| **Scikit-Learn** | K-Means clustering, `StandardScaler`, and validation metrics. |
| **Database & SQL** | **PostgreSQL, Psycopg3** | Relational data warehouse, DDL constraints, and windowed analytics. |
| **Visualization** | **Matplotlib, Seaborn** | Statistical distribution plots, heatmaps, and diagnostic charts. |
| **Web Application** | **Streamlit** | Multi-page interactive exploratory analytical dashboard. |
| **Business Intelligence** | **Power BI Desktop (PBIR)**| 4-page enterprise-style reporting suite with Star Schema & DAX. |
| **Testing** | **pytest** | Automated test suite enforcing mathematical invariants (170 tests: 169 passed, 1 skipped). |
| **Version Control** | **Git, GitHub** | Source code management and project documentation. |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
