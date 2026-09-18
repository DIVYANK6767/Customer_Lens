# Product Requirements Document (PRD)

## CustomerLens: Customer Segmentation & Targeted Marketing Analytics

---

### 1. Project Title
**CustomerLens — Customer Segmentation & Targeted Marketing Analytics**

---

### 2. Executive Summary
CustomerLens is an end-to-end e-commerce customer analytics project designed to transform raw transactional sales data into actionable behavioral segments and data-driven marketing strategies. In modern retail, blanket marketing approaches produce inefficient spend and fail to address varying customer lifecycles. CustomerLens establishes a structured analytics workflow: ingesting raw transaction records, performing data hygiene, persisting structured data into PostgreSQL, conducting exploratory analysis, calculating Recency, Frequency, and Monetary (RFM) metrics, evaluating and executing unsupervised K-Means clustering, and profiling customer cohorts.

The resulting segments provide marketing and CRM teams with clear behavioral profiles. Strategic marketing recommendations are formulated as testable hypotheses rather than speculative claims of proven impact. The project delivers dual reporting interfaces—an interactive Streamlit application and an executive Power BI dashboard—supported by automated `pytest` suites and GitHub Actions CI, demonstrating a professional, reproducible data analyst workflow.

---

### 3. Business Problem
E-commerce businesses routinely face challenges in optimizing marketing spend, maintaining customer loyalty, and preventing churn when relying on undifferentiated, one-size-fits-all customer engagement. Key pain points include:
- **Inefficient Marketing Spend:** Treating every customer identically results in wasteful promotional discounts sent to loyal shoppers who would purchase anyway, or generic messages sent to dormant customers who require re-engagement incentives.
- **Customer Churn & Inactivity:** Businesses lack visibility into when a previously active customer is drifting into dormancy until after they have lapsed.
- **Unidentified Customer Value:** High-value customers contributing disproportionate revenue are not systematically distinguished from one-time bargain seekers, preventing personalized VIP treatment or account nurturing.
- **Disconnected Data & Decision-Making:** Transaction logs sit in relational tables or log stores without being synthesized into actionable customer-level behavioral profiles accessible to marketing and commercial decision-makers.

---

### 4. Business Context
Online retail operates under low switching costs and transactional anonymity. Unlike subscription businesses with explicit contract renewals, e-commerce stores operate in a non-contractual setting: customers purchase at will and lapse silently. To navigate this landscape, growth and retention teams require an objective, empirical method to evaluate customer engagement over time. By consolidating order logs into customer-level RFM metrics and applying machine learning clustering, CustomerLens equips stakeholders with an empirical foundation for targeted retention, reactivation campaigns, and customer lifetime value optimization.

---

### 5. Target Users
1. **E-Commerce Marketing Managers & Campaign Planners:**
   - Need clear segment profiles to design targeted campaigns, select promotional channels, and allocate marketing budget efficiently.
2. **CRM & Retention Specialists:**
   - Need early identification of declining engagement and at-risk cohorts to deploy automated win-back workflows.
3. **E-Commerce Executives & Commercial Directors:**
   - Require high-level visibility into customer volume, revenue concentration, order velocity, and cohort dynamics via summary dashboards.
4. **Data Analysts & Analytics Engineers:**
   - Require a modular, fully reproducible codebase, documented data transformation rules, automated tests, and clear database schemas.

---

### 6. Business Objectives
- **Understand Customer Purchasing Dynamics:** Provide commercial teams with baseline metrics on customer counts, transaction volumes, revenue distributions, and purchase intervals.
- **Establish Objective Customer Segmentation:** Replace subjective customer categorizations with an unsupervised machine learning model based on verified transaction history.
- **Formulate Segment-Specific Marketing Strategies:** Define tailored, actionable marketing recommendations for each discovered cohort to guide retention, cross-selling, and VIP engagement.
- **Deliver Self-Service Analytical Tools:** Deploy intuitive web and BI dashboard interfaces allowing non-technical stakeholders to explore segments, inspect metrics, and filter cohorts dynamically.

---

### 7. Analytical Objectives
- **Data Ingestion & Hygiene:** Extract raw transaction logs, diagnose data quality issues (missing identifiers, cancellations, negative quantities, zero/negative unit prices), and construct an auditable data cleaning pipeline.
- **Database Modeling:** Structure and load raw and cleaned data into a PostgreSQL relational schema, writing optimized SQL queries for business aggregations.
- **Baseline Transactional Analysis:** Calculate summary statistics for revenue, total unique customers, total distinct orders, and Average Order Value (AOV).
- **RFM Metric Engineering:** Consolidate transactional records by unique customer ID to compute:
  - **Recency ($R$):** Days elapsed from customer's latest purchase to a defined reference snapshot date.
  - **Frequency ($F$):** Total count of distinct completed purchase invoices per customer.
  - **Monetary ($M$):** Total cumulative spend across all valid transactions per customer.
- **Distributional Assessment & Transformation:** Evaluate skewness and variance across R, F, and M distributions, applying appropriate mathematical transformations (e.g., logarithmic or power transforms) and feature scaling.
- **Empirical Cluster Determination:** Evaluate cluster candidates objectively across $k \in [2, 10]$ using the Elbow Method (Inertia/WCSS) and Silhouette Analysis without pre-assuming cluster count.
- **Cluster Profiling & Validation:** Compute summary statistics (mean, median, min, max, standard deviation) for each segment across RFM dimensions to validate mathematical separability and business interpretability.

---

### 8. Key Business Questions
The analytical pipeline and dashboard deliverables must specifically answer:
1. How many customers exist?
2. How many orders exist?
3. What is total revenue?
4. What is average order value?
5. Which customers generate the most revenue?
6. How frequently do customers purchase?
7. Which customers are highly valuable?
8. Which customers appear at risk of becoming inactive?
9. What are the distributions of Recency, Frequency and Monetary value?
10. How many meaningful customer segments exist?
11. What are the characteristics of each segment?
12. Which segments contribute the most revenue?
13. Which segments contain the most customers?
14. Which customers/segments represent retention opportunities?
15. Which segments represent cross-selling opportunities?
16. What marketing strategy could be appropriate for each segment?

*(Note: All metrics, counts, segment totals, and percentages will be calculated directly from the verified dataset during subsequent analytical phases; no values are hard-coded or fabricated in this document.)*

---

### 9. Functional Requirements
- **FR-1: Data Loading & Inspection:** Ingest transactional dataset from `data/raw/`, inspect schema, data types, null rates, and duplicate entries.
- **FR-2: Data Cleaning Module:**
  - Detect and remove records lacking valid customer identification where customer attribution is impossible.
  - Separate cancelled/returned orders from completed purchases based on invoice identifiers and negative quantities.
  - Filter out administrative anomalies (e.g., test entries, manual ledger adjustments, non-merchandise fees).
  - Persist cleaned data to `data/processed/` without altering raw source data.
- **FR-3: Relational SQL Pipeline:**
  - Create table schemas in PostgreSQL for raw transactions, cleaned transactions, and RFM customer aggregates.
  - Implement SQL scripts answering exploratory and analytical transaction questions.
- **FR-4: RFM Feature Engineering Engine:**
  - Calculate reference snapshot date dynamically as `max(InvoiceDate) + 1 day`.
  - Aggregate transactions at the customer level to compute raw R, F, and M values.
- **FR-5: Clustering Pipeline:**
  - Provide feature transformation and standard scaling to handle skewness and varying units.
  - Implement K-Means clustering with configurable `random_state` for deterministic execution.
  - Generate diagnostics: Inertia curve (Elbow) and Silhouette coefficient scores across evaluated $k$ values.
  - Assign final cluster labels to each customer record.
- **FR-6: Segment Profiling Module:**
  - Compute segment-level summary statistics and assign descriptive behavioral tags based strictly on observed data.
- **FR-7: Interactive Streamlit Application:**
  - Multi-page UI providing KPI overviews, RFM distribution plots, cluster visualizers, and strategy cards.
- **FR-8: Power BI Dashboard:**
  - `.pbix` data model with explicit DAX measures, dynamic slicers, and executive overview visuals.
- **FR-9: Automated Testing:**
  - Test suite built with `pytest` covering data cleaning logic, RFM calculations, and scaling transformations.

---

### 10. Non-Functional Requirements
- **Reproducibility:** All analytical steps, random states in modeling, and data transformations must produce identical outputs when re-run from scratch.
- **Modularity:** Reusable logic must reside in Python packages under `src/` rather than monolithic notebook cells.
- **Maintainability & Code Quality:** Code must adhere to PEP 8 standards, include docstrings, and maintain clear separation of concerns.
- **Data Integrity & Immutability:** Raw data files in `data/raw/` must be treated as strictly read-only.
- **Security & Privacy:** Environment variables, database credentials, and local secrets must be loaded via `.env` and strictly excluded from version control via `.gitignore`.
- **Portability:** The project must run cleanly on standard Python 3.10+ environments with dependencies managed via `requirements.txt`.

---

### 11. Data Requirements
- **Expected Primary Dataset:** UCI Machine Learning Repository — Online Retail Dataset (or verified e-commerce transactional equivalent).
- **Required Verification:** Dataset fields and data types must be programmatically verified against the real data file before pipeline execution.
- **Expected Data Schema (Subject to Initial Verification):**
  - `InvoiceNo` (String/Integer): Unique 6-digit transaction identifier. Invoices prefixed with 'C' indicate cancellations.
  - `StockCode` (String): Unique product item identifier.
  - `Description` (String): Product/item name.
  - `Quantity` (Integer): The quantity of each item per transaction. Negative values denote returns/cancellations.
  - `InvoiceDate` (Datetime): Timestamp when the transaction took place.
  - `UnitPrice` (Float): Price per unit of merchandise in GBP.
  - `CustomerID` (Float/String): Unique identifier assigned to each individual customer.
  - `Country` (String): Name of the country where the customer resides.
- **Data Quality & Filtering Criteria:**
  - Document total rows before and after cleaning.
  - Missing `CustomerID` records must be analyzed for volume and excluded from customer-level RFM modeling (with rationale documented).
  - Transactions where `UnitPrice <= 0` or non-merchandise stock codes (e.g., postage, manual entries) must be evaluated and filtered systematically.

---

### 12. RFM Requirements
- **Customer Grain:** Exactly one record per unique customer in the analytical feature set.
- **Snapshot Date:** Calculated as one day after the maximum date found in the cleaned dataset (`max(InvoiceDate) + timedelta(days=1)`), avoiding arbitrary historical anchor dates.
- **Recency ($R$):**
  $$\text{Recency} = \text{Snapshot Date} - \max(\text{InvoiceDate}_i)$$
  Measured in integer days.
- **Frequency ($F$):**
  $$\text{Frequency} = \text{Count of unique valid InvoiceNo}_i$$
  Distinct completed orders placed by customer $i$.
- **Monetary ($M$):**
  $$\text{Monetary} = \sum (\text{Quantity}_{i,j} \times \text{UnitPrice}_{i,j})$$
  Net expenditure across all valid purchases for customer $i$.
- **Distributional Assessment:**
  - Generate descriptive statistics (mean, median, standard deviation, IQR, min, max, skewness).
  - Visualize histograms and box plots to detect heavy right-skewness and extreme outliers typical of e-commerce spend.

---

### 13. Customer Segmentation Requirements
- **Behavioral Foundation:** Segmentation must be grounded solely on observed transactional RFM features, avoiding unverified synthetic attributes.
- **Empirical Optimization:** The number of clusters ($k$) will not be predetermined or hard-coded. It will be decided using quantitative criteria (Elbow Method and Silhouette Analysis) combined with domain interpretability.
- **Distinct Segment Separation:** Segments must display statistically meaningful differences across recency, order velocity, and total spend.
- **Interpretable Nomenclature:** Segment labels will be derived only after inspecting post-clustering profiles (e.g., distinguishing high-spend recent buyers from low-frequency dormant customers).

---

### 14. Machine Learning Requirements
- **Algorithm:** K-Means Clustering (`sklearn.cluster.KMeans`).
- **Feature Preprocessing:**
  - Logarithmic transformation (e.g., $\log(x + 1)$) or Power Transformation to alleviate extreme right-skewness in RFM distributions.
  - Standardization using `StandardScaler` to ensure zero mean and unit variance across all features, preventing Monetary scale from dominating Euclidean distance calculations.
- **Hyperparameter Evaluation:**
  - Inertia / Within-Cluster Sum of Squares (WCSS) plotted over $k \in [2, 10]$ to identify the "elbow".
  - Average Silhouette Coefficient computed for each candidate $k$ to quantify cluster cohesion and separation.
- **Model Stability:** Set deterministic `random_state` and specify `n_init >= 10` for convergence consistency.
- **Validation Criteria:** Clusters must be balanced enough to avoid single-customer outlier groupings while demonstrating distinct operational behaviors.

---

### 15. Dashboard Requirements
- **Visual Hierarchy:** Clean, executive-level interface with a top-level KPI band, interactive middle filters, and detailed diagnostic charts below.
- **Key Performance Indicators (KPIs):**
  - Total Revenue
  - Total Customers
  - Total Orders
  - Average Order Value (AOV)
- **Visualizations Required:**
  - Segment customer distribution (count and percentage share).
  - Segment revenue distribution (monetary contribution and percentage share).
  - RFM 2D/3D scatter plots illustrating cluster boundaries.
  - Average and median RFM metrics comparison by segment.
- **Interactivity:** Cross-filtering by segment, country, or metric thresholds.

---

### 16. Streamlit Requirements
- **Multi-Page Architecture:**
  - `app/Home.py`: Executive Overview and high-level project KPIs.
  - `app/pages/1_Data_Overview.py`: Summary statistics, data health metrics, and sample transaction views.
  - `app/pages/2_RFM_Distributions.py`: Interactive distribution plots (Plotly histograms, box plots, skewness indicators).
  - `app/pages/3_Customer_Segments.py`: Interactive 2D/3D cluster visualizations, segment comparison tables, and filterable customer explorer.
  - `app/pages/4_Marketing_Strategy.py`: Cohort-specific behavioral summaries and strategic recommendation cards.
- **Component Design:** Modular widgets stored under `app/components/` for KPI cards, chart themes, and data download utilities.

---

### 17. Power BI Requirements
- **Data Model:** Clean, tabular schema loaded from processed analytical outputs.
- **Explicit DAX Measures:**
  - `Total Sales = SUM(FactTransactions[LineTotal])`
  - `Total Orders = DISTINCTCOUNT(FactTransactions[InvoiceNo])`
  - `Total Customers = DISTINCTCOUNT(DimCustomer[CustomerID])`
  - `Average Order Value = DIVIDE([Total Sales], [Total Orders], 0)`
  - `Avg Recency`, `Avg Frequency`, `Avg Monetary` per segment.
- **Visual Layout:**
  - Executive Overview page with KPI cards, revenue breakdown by segment, and geographic summary.
  - Segment Deep-Dive page with customer scatter distribution, segment matrix comparison, and customer lookup tables.

---

### 18. Business Insight Requirements: The Four-Tier Analytical Framework
To maintain professional credibility and avoid overstating claims in a fresher portfolio, all project outputs must explicitly differentiate between the following four levels:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. Analytical Findings (Empirical, mathematical facts from data)        │
├─────────────────────────────────────────────────────────────────────────┤
│ 2. Business Interpretation (Contextual meaning in retail operations)    │
├─────────────────────────────────────────────────────────────────────────┤
│ 3. Recommendations / Action Plans (Strategic hypotheses to test)        │
├─────────────────────────────────────────────────────────────────────────┤
│ 4. Measured Business Impact (Verified outcomes from post-campaign test) │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Analytical Findings (Facts):** Purely objective statistical observations calculated from the dataset.
   - *Example:* "Segment 1 exhibits a median Recency of $X$ days, median Frequency of $Y$ orders, and median spend of $Z$ GBP."
2. **Business Interpretation (Context):** Translating the statistical finding into commercial customer behavior.
   - *Example:* "Customers in Segment 1 are recent, frequent buyers with above-average spend, reflecting our core loyal customer base."
3. **Recommendations (Hypotheses):** Proposed marketing or operational interventions formulated to address the observed behavior.
   - *Example Formulation:* "Hypothesis: Enrolling Segment 1 in an exclusive VIP loyalty rewards program with early product access will maintain engagement and increase annual retention."
4. **Measured Business Impact (Post-Intervention Verification):** Empirically measured uplift observed after executing a campaign against a randomized control group.
   - *Portfolio Rule:* Because this portfolio project analyzes historical transactional data and does not run live marketing campaigns, **no measured business impact (e.g., "+15% revenue lift", "10% churn reduction") will be claimed or fabricated**. All recommendations will be explicitly framed as strategic hypotheses.

---

### 19. Success Criteria
- **Technical Rigor:**
  - Automated tests passing via `pytest` for all transformation and RFM logic.
  - Clean, reproducible pipeline execution end-to-end.
  - Continuous integration enabled via GitHub Actions.
- **Analytical Credibility:**
  - Data cleaning decisions documented transparently with counts of filtered records.
  - Cluster selection justified mathematically via Elbow Method and Silhouette Analysis.
  - No pre-determined cluster counts, hard-coded percentages, or fabricated metrics.
- **Portfolio Quality:**
  - Clear, modular Python architecture in `src/`.
  - Accessible, fully functional Streamlit application.
  - Well-structured Power BI report file with documented DAX measures.

---

### 20. Assumptions
- The transaction dataset represents a continuous historical window of actual e-commerce sales.
- Invoices prefixed with 'C' and negative quantities reliably identify returns or cancelled orders.
- Records with identical `CustomerID` values represent transactions conducted by the same individual or commercial purchasing entity.
- Unit prices are denominated in a single standard currency (GBP for the UCI dataset).

---

### 21. Risks & Mitigations
| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **High Missing CustomerID Rate** | Unidentified guest checkout transactions cannot be mapped to individual customer RFM profiles. | Quantify missing record count in EDA; document rationale for excluding them from RFM while retaining them for store-wide revenue summaries. |
| **Heavy Distribution Skewness** | Extreme outliers (e.g., bulk wholesale orders) distort standard Euclidean distance calculations in K-Means. | Apply logarithmic/power transforms and standard scaling; inspect outlier boundaries during EDA. |
| **Ambiguous Cluster Boundaries** | Unsupervised clustering may yield overlapping clusters with low silhouette scores. | Systematically test $k \in [2, 10]$; evaluate both inertia and silhouette scores; favor the most statistically defensible and commercially interpretable $k$. |
| **Environment Incompatibilities** | Dependency mismatches across different operating systems or execution environments. | Maintain pinned version bounds in `requirements.txt` and validate build via GitHub Actions CI. |

---

### 22. Limitations
- **Lack of Demographic & Behavioral Telemetry:** The dataset contains no customer demographic attributes (age, gender, income) and no digital interaction telemetry (web clicks, cart abandonments, page dwell time).
- **Static Historical Window:** Analysis is based on a fixed historical slice; it does not stream live transactions or adapt dynamically without re-running pipelines.
- **K-Means Geometric Assumptions:** K-Means assumes spherical clusters of comparable variance, which may simplify complex, irregular multi-dimensional customer behavioral boundaries.
- **Unverified Post-Campaign Uplift:** Without live marketing intervention and A/B test control groups, campaign recommendations cannot claim verified revenue uplift or retention improvements.

---

### 23. Future Enhancements
- **Predictive Customer Lifetime Value (CLV):** Implement probabilistic models (e.g., BG/NBD and Gamma-Gamma) to forecast future transaction frequency and expected customer monetary value.
- **Supervised Churn Modeling:** Develop binary classification models to predict the probability of churn within a specified forward-looking time window (e.g., next 90 days).
- **Alternative Clustering Algorithms:** Benchmark K-Means against DBSCAN, Hierarchical Agglomerative Clustering, and Gaussian Mixture Models (GMM).
- **Market Basket Analysis:** Implement association rule mining (Apriori / FP-Growth) on transaction line items to identify cross-selling and product bundling opportunities across specific customer segments.
- **Orchestration & Workflow Automation:** Implement pipeline scheduling with tools such as Mage or Apache Airflow to automate recurring ingestion and score updates.
