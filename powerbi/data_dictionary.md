# Power BI Data Dictionary — CustomerLens Analytical Datasets

This data dictionary defines the schema, grain, data types, business definitions, relationship roles, and measure suitability for all validated datasets available to the Power BI analytical layer.

---

## 1. Dataset Architecture & Classification Summary

| File Name | Grain | Layer / Classification | Primary Role in Power BI |
| :--- | :--- | :--- | :--- |
| [`customer_transactions.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/customer_transactions.csv) | Transaction Line Item | Fact Table | Primary Transaction Fact Table (Revenue, Volume, Dates) |
| [`business_segments.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/business_segments.csv) | Customer Account | Dimension / Analytical Output | Primary Customer Dimension Table (RFM, Clusters, Segments) |
| [`rfm_customer_metrics.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/rfm_customer_metrics.csv) | Customer Account | Dimension Subset | Intermediate RFM Dimension (Superseded by `business_segments.csv`) |
| [`customer_clusters.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/customer_clusters.csv) | Customer Account | Dimension Subset | Intermediate Cluster Dimension (Superseded by `business_segments.csv`) |
| [`segment_summary.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/segment_summary.csv) | Cluster Archetype (4 rows) | Dimension / Summary Reference | Segment Performance Scorecard & Reference Profile |
| [`cluster_profiles.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/cluster_profiles.csv) | Cluster Archetype (4 rows) | Summary Reference | Precomputed Cluster Profiles (Superseded by `segment_summary.csv`) |
| [`clustering_metrics.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/clustering_metrics.csv) | $K$ Evaluation Value (9 rows) | Reference / Diagnostics | Disconnected Diagnostic Fact Table for Model Evaluation ($K=2..10$) |
| [`marketing_opportunities.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/marketing_opportunities.csv) | Cluster Archetype (4 rows) | Reference / Strategy | Marketing Strategy Matrix & A/B Experimentation Reference |

> [!IMPORTANT]
> **Recommended Ingestion Practice:** In Power BI, import `customer_transactions.csv` as the Fact table, `business_segments.csv` as the Customer Dimension table, `segment_summary.csv` and `marketing_opportunities.csv` as Segment Reference tables, and `clustering_metrics.csv` as a disconnected diagnostic table. `rfm_customer_metrics.csv`, `customer_clusters.csv`, and `cluster_profiles.csv` are intermediate pipeline artifacts whose attributes are fully consolidated in `business_segments.csv` and `segment_summary.csv`.

---

## 2. Dataset Dictionaries

### 2.1. `customer_transactions.csv`
- **File Path:** `data/processed/customer_transactions.csv`
- **Total Records:** 392,692 rows
- **Grain:** One row per validated invoice line item for identified, active customers.
- **Role:** Fact Table (Core Sales Activity).

| Column Name | Power BI Data Type | Business Meaning & Description | Relationship Key | Measure / Visual Suitability |
| :--- | :--- | :--- | :--- | :--- |
| `InvoiceNo` | Whole Number (`Int64`) | 6-digit unique identifier for a completed sales transaction. | No (Degenerate Fact) | Base for `DISTINCTCOUNT(InvoiceNo)` (Total Orders). |
| `StockCode` | Text (`String`) | 5- or 6-character unique product/item identifier. | No | Categorical breakdown, line item counting. |
| `Description` | Text (`String`) | Cleaned English product description. | No | Visual display in tables/tooltips. |
| `Quantity` | Whole Number (`Int64`) | Number of units purchased per line item (Strictly $>0$). | No | Base for `SUM(Quantity)` (Total Units Sold). |
| `InvoiceDate` | Date/Time (`DateTime`) | Timestamp of transaction creation (`YYYY-MM-DD HH:MM:SS`). | Date Dim (`Date`) | Base for time intelligence, monthly trends, and date slicers. |
| `UnitPrice` | Decimal Number (`Currency`) | Unit selling price in GBP (£) (Strictly $>0$). | No | Item pricing context, average unit price. |
| `CustomerID` | Whole Number (`Int64`) | 5-digit unique customer account identifier. | Foreign Key $\rightarrow$ `business_segments[customerid]` | Slicing, customer joins, `DISTINCTCOUNT(CustomerID)`. |
| `Country` | Text (`String`) | Country of customer billing / order origination (37 countries). | No (or Geo Dim) | Geographic slicer, map visual, country-level revenue. |
| `TransactionType` | Text (`String`) | Invariant transaction category (`Sale` for all 392,692 rows). | No | Filter / audit consistency check. |
| `DescriptionMissing`| True/False (`Boolean`) | Flag indicating whether original description was imputed (`False`). | No | Data quality audit filter. |
| `Revenue` | Decimal Number (`Currency`) | Computed line revenue (`Quantity * UnitPrice`) in GBP (£). | No | Base for `SUM(Revenue)` (Total Revenue). |

---

### 2.2. `business_segments.csv`
- **File Path:** `data/processed/business_segments.csv`
- **Total Records:** 4,338 rows
- **Grain:** One row per unique active customer account.
- **Role:** Primary Customer Dimension Table (Consolidated Behavioral Profile).

| Column Name | Power BI Data Type | Business Meaning & Description | Relationship Key | Measure / Visual Suitability |
| :--- | :--- | :--- | :--- | :--- |
| `customerid` | Whole Number (`Int64`) | Unique customer identifier (4,338 unique values). | Primary Key $\leftarrow$ `customer_transactions[CustomerID]` | Primary join key to transaction fact table. |
| `recency` | Whole Number (`Int64`) | Days elapsed between customer's last purchase and anchor date (2011-12-10). | No | Base for `AVERAGE(recency)`, distribution histograms, scatter X-axis. |
| `frequency` | Whole Number (`Int64`) | Total distinct completed orders (`InvoiceNo` count) across observation window. | No | Base for `AVERAGE(frequency)`, scatter plots, distribution plots. |
| `monetary` | Decimal Number (`Currency`) | Total gross monetary spend in GBP (£) across observation window. | No | Base for `AVERAGE(monetary)`, spend filtering, scatter Y-axis. |
| `R_score` | Whole Number (`Int64`) | Recency quintile rank (1 = least recent, 5 = most recent). | No | Quintile distribution charts, slicers. |
| `F_score` | Whole Number (`Int64`) | Frequency quintile rank (1 = least frequent, 5 = most frequent). | No | Quintile distribution charts, slicers. |
| `M_score` | Whole Number (`Int64`) | Monetary quintile rank (1 = lowest spend, 5 = highest spend). | No | Quintile distribution charts, slicers. |
| `RFM_score` | Whole Number (`Int64`) | Concatenated 3-digit RFM score (e.g. `555`, `111`). | No | Discrete customer grouping, detail card display. |
| `segment` | Text (`String`) | Rule-based RFM segment name (e.g. `Champions`, `At Risk`, `Hibernating`). | No | Rule-based vs cluster comparison, table display. |
| `cluster_id` | Whole Number (`Int64`) | Unsupervised K-Means cluster assignment ($\{0, 1, 2, 3\}$). | Foreign Key $\rightarrow$ `segment_summary[cluster_id]` | Slicing by cluster, cluster-level grouping. |
| `country` | Text (`String`) | Primary country of account registration. | No | Customer geographic distribution, slicer. |
| `first_purchase_date`| Date/Time (`DateTime`) | Timestamp of customer's first observed purchase. | No | Customer tenure calculation, cohort analysis. |
| `last_purchase_date` | Date/Time (`DateTime`) | Timestamp of customer's most recent observed purchase. | No | Customer lifecycle analysis, customer detail cards. |
| `PCA1` | Decimal Number (`Float64`) | First principal component score from RFM feature space. | No | 2D cluster visualization scatter plot. |
| `PCA2` | Decimal Number (`Float64`) | Second principal component score from RFM feature space. | No | 2D cluster visualization scatter plot. |
| `business_segment` | Text (`String`) | Professional business persona name (*High-Value Engaged*, etc.). | No | Primary segmentation slicer, legend, chart categories. |
| `action_category` | Text (`String`) | Commercial operational strategy (*Protect & Grow*, *Nurture*, *Develop*, *Reactivate*). | No | Strategy card categorization, visual grouping. |
| `segment_description`| Text (`String`) | Plain-language description of customer's behavioral archetype. | No | Tooltip display, customer dossier card. |

---

### 2.3. `segment_summary.csv`
- **File Path:** `data/processed/segment_summary.csv`
- **Total Records:** 4 rows
- **Grain:** One row per validated business segment archetype ($K=4$).
- **Role:** Segment Dimension / Performance Scorecard Reference Table.

| Column Name | Power BI Data Type | Business Meaning & Description | Relationship Key | Measure / Visual Suitability |
| :--- | :--- | :--- | :--- | :--- |
| `cluster_id` | Whole Number (`Int64`) | Cluster ID ($\{0, 1, 2, 3\}$). | Primary Key $\leftarrow$ `business_segments[cluster_id]` | Join key to customer dimension. |
| `business_segment` | Text (`String`) | Standardized persona name (*High-Value Engaged*, etc.). | No | Dimension display, scorecard row header. |
| `action_category` | Text (`String`) | Operational strategy (*Protect & Grow*, *Nurture*, etc.). | No | Badge / card display, category grouping. |
| `customer_count` | Whole Number (`Int64`) | Total customer accounts in segment (e.g. 716, 1170, 834, 1618). | No | Direct scorecard display, bar charts. |
| `customer_percentage`| Decimal Number (`Percentage`)| Share of total customer base (e.g. 16.51%, 26.97%, 19.23%, 37.30%). | No | Precomputed share display, doughnut charts. |
| `total_revenue` | Decimal Number (`Currency`) | Aggregate gross turnover generated by segment (£). | No | Revenue scorecard display, bar charts. |
| `revenue_percentage` | Decimal Number (`Percentage`)| Share of total gross turnover (e.g. 65.05%, 23.54%, 5.24%, 6.16%). | No | Precomputed revenue share display, Pareto visual. |
| `average_recency` | Decimal Number (`Float64`) | Arithmetic mean recency (days) for segment. | No | Comparison bar chart, tooltip context. |
| `median_recency` | Decimal Number (`Float64`) | Median recency (days) (e.g. 8.0, 57.0, 17.0, 174.5). | No | Robust behavioral benchmark visual. |
| `average_frequency` | Decimal Number (`Float64`) | Arithmetic mean order frequency for segment. | No | Comparison bar chart, tooltip context. |
| `median_frequency` | Decimal Number (`Float64`) | Median order frequency (e.g. 10.0, 4.0, 2.0, 1.0). | No | Robust behavioral benchmark visual. |
| `average_monetary` | Decimal Number (`Currency`) | Arithmetic mean monetary spend per customer (£). | No | Comparison bar chart, tooltip context. |
| `median_monetary` | Decimal Number (`Currency`) | Median monetary spend (£) (e.g. £3,730.61, £1,340.08, £481.03, £293.78). | No | Robust behavioral benchmark visual. |
| `average_orders` | Decimal Number (`Float64`) | Mean completed order count per customer. | No | Behavioral metric display. |
| `average_revenue_per_customer`| Decimal Number (`Currency`)| Mean total gross revenue per customer account (£). | No | High-level customer value benchmarking. |
| `primary_characteristic`| Text (`String`) | Key empirical behavioral traits of the segment. | No | Scorecard expandable text, card tooltip. |
| `business_opportunity` | Text (`String`) | High-level commercial opportunity hypothesis. | No | Scorecard expandable text, card tooltip. |

---

### 2.4. `marketing_opportunities.csv`
- **File Path:** `data/processed/marketing_opportunities.csv`
- **Total Records:** 4 rows
- **Grain:** One row per business segment marketing strategy.
- **Role:** Strategy Matrix / Opportunity Detail Reference Table.

| Column Name | Power BI Data Type | Business Meaning & Description | Relationship Key | Measure / Visual Suitability |
| :--- | :--- | :--- | :--- | :--- |
| `cluster_id` | Whole Number (`Int64`) | Cluster ID ($\{0, 1, 2, 3\}$). | Optional Foreign Key $\rightarrow$ `segment_summary[cluster_id]` | Linkage to segment summary table. |
| `business_segment` | Text (`String`) | Standardized persona name (*High-Value Engaged*, etc.). | No | Visual grouping, strategy card header. |
| `action_category` | Text (`String`) | Strategic action category (*Protect & Grow*, etc.). | No | Badge display. |
| `customer_count` | Whole Number (`Int64`) | Customer account volume in segment. | No | Cohort size callout. |
| `customer_percentage`| Decimal Number (`Percentage`)| Share of customer base. | No | Cohort percentage callout. |
| `revenue` | Decimal Number (`Currency`) | Segment turnover in GBP (£). | No | Revenue impact callout. |
| `revenue_percentage` | Decimal Number (`Percentage`)| Segment turnover share. | No | Revenue percentage callout. |
| `primary_characteristic`| Text (`String`) | Empirical profile summary. | No | Narrative card block. |
| `business_opportunity` | Text (`String`) | Proposed commercial leverage point. | No | Opportunity description block. |
| `recommended_action` | Text (`String`) | Concrete marketing/commercial intervention. | No | Primary action visual display. |
| `measurement_metric` | Text (`String`) | Proposed primary success evaluation KPI. | No | Metric guidance tag / KPI badge. |
| `caveat` | Text (`String`) | Explicit risk warning and guardrail consideration. | No | Risk alert box (callout with warning icon). |

---

### 2.5. `clustering_metrics.csv`
- **File Path:** `data/processed/clustering_metrics.csv`
- **Total Records:** 9 rows ($K \in [2, 10]$)
- **Grain:** One row per candidate cluster solution evaluated during model selection.
- **Role:** Disconnected Diagnostic Fact Table (Model Validation Visual).

| Column Name | Power BI Data Type | Business Meaning & Description | Relationship Key | Measure / Visual Suitability |
| :--- | :--- | :--- | :--- | :--- |
| `k` | Whole Number (`Int64`) | Number of candidate clusters evaluated ($K = 2, 3, \dots, 10$). | None (Disconnected) | X-axis for all clustering evaluation charts. |
| `inertia` | Decimal Number (`Float64`) | Within-cluster sum of squared errors (WCSS). | None | Line chart (Elbow Curve visual). |
| `silhouette_score` | Decimal Number (`Float64`) | Mean silhouette coefficient across all points ($-1$ to $+1$). | None | Line chart (Separation quality visual). |
| `calinski_harabasz` | Decimal Number (`Float64`) | Variance ratio criterion score (higher is denser/separated). | None | Diagnostic evaluation table / secondary axis. |
| `davies_bouldin` | Decimal Number (`Float64`) | Similarity measure between clusters (lower is better). | None | Line chart (Cluster compactness visual). |
| `cluster_count` | Whole Number (`Int64`) | Redundant verification of $K$. | None | Validation check. |
| `min_cluster_size` | Whole Number (`Int64`) | Customer count in smallest cluster for given $K$. | None | Table display, cluster balance evaluation. |
| `max_cluster_size` | Whole Number (`Int64`) | Customer count in largest cluster for given $K$. | None | Table display, cluster balance evaluation. |

---

### 2.6. Intermediate Output Dictionaries (For Technical Reference)

These tables are created during Phases 8 and 9 of the analytical pipeline. Their contents are fully subsumed into `business_segments.csv` and `segment_summary.csv`.

#### `rfm_customer_metrics.csv` (4,338 rows)
- `customerid` (`Int64`), `recency` (`Int64`), `frequency` (`Int64`), `monetary` (`Float64`), `first_purchase_date` (`String`), `last_purchase_date` (`String`), `country` (`String`), `R_score` (`Int64`), `F_score` (`Int64`), `M_score` (`Int64`), `RFM_score` (`Int64`), `segment` (`String`).
- *Status in Power BI:* Do not load alongside `business_segments.csv` to avoid schema redundancy.

#### `customer_clusters.csv` (4,338 rows)
- `customerid` (`Int64`), `recency` (`Int64`), `frequency` (`Int64`), `monetary` (`Float64`), `R_score` (`Int64`), `F_score` (`Int64`), `M_score` (`Int64`), `RFM_score` (`Int64`), `segment` (`String`), `cluster_id` (`Int64`), `country` (`String`), `first_purchase_date` (`String`), `last_purchase_date` (`String`), `PCA1` (`Float64`), `PCA2` (`Float64`).
- *Status in Power BI:* Do not load alongside `business_segments.csv` to avoid schema redundancy.

#### `cluster_profiles.csv` (4 rows)
- `cluster_id` (`Int64`), `customer_count` (`Int64`), `customer_percentage` (`Float64`), `total_revenue` (`Float64`), `revenue_percentage` (`Float64`), `average_recency` (`Float64`), `median_recency` (`Float64`), `average_frequency` (`Float64`), `median_frequency` (`Float64`), `average_monetary` (`Float64`), `median_monetary` (`Float64`), `average_orders` (`Float64`), `average_revenue_per_customer` (`Float64`).
- *Status in Power BI:* Fully represented by `segment_summary.csv` which additionally includes persona and opportunity metadata.
