# Power BI Data Architecture & Implementation Guide — CustomerLens

This directory provides the architectural foundation, schema definitions, DAX measures, and dashboard specifications for implementing the **CustomerLens** reporting layer in Microsoft Power BI Desktop.

---

## 1. Overview of the Power BI Layer

Power BI operates strictly as an **interactive presentation, exploration, and analytical reporting layer** over the validated outputs produced by the CustomerLens pipeline (Phases 4–10).

Power BI does **not**:
- Re-run unsupervised clustering algorithms (K-Means).
- Re-calculate feature scaling or log1p transformations.
- Alter raw transaction records.
- Fabricate demographic, churn-probability, or causal attribution metrics.

---

## 2. Dataset Classification & Import Strategy

When importing data via Power BI Desktop (**Home** $\rightarrow$ **Get Data** $\rightarrow$ **Text/CSV**), classify and load the files according to their analytical grain:

### A. Recommended Core Datasets to Import (Primary Model)

| File Name | Grain | Table Role | Description |
| :--- | :--- | :--- | :--- |
| [`customer_transactions.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/customer_transactions.csv) | Line Item (392,692 rows) | **Fact Table** (`FactTransactions`) | Completed, validated sales transactions with positive quantity, price, and identified customer ID. |
| [`business_segments.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/business_segments.csv) | Customer Account (4,338 rows) | **Customer Dimension** (`DimCustomer`) | Comprehensive customer profile: RFM scores, cluster ID, business segment, action category, tenure dates, and PCA coordinates. |
| [`segment_summary.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/segment_summary.csv) | Cluster Archetype (4 rows) | **Segment Dimension** (`DimSegment`) | Validated 4-cluster scorecard containing median/mean RFM metrics, revenue contributions, and persona descriptions. |
| [`marketing_opportunities.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/marketing_opportunities.csv) | Cluster Archetype (4 rows) | **Strategy Reference** (`RefMarketing`) | Strategic action matrix with recommended tactics, proposed success KPIs, and explicit risk caveats. |
| [`clustering_metrics.csv`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/data/processed/clustering_metrics.csv) | Evaluation $K$ (9 rows) | **Diagnostic Fact** (`FactKDiagnostics`) | Evaluation metrics ($K=2..10$: Inertia, Silhouette, Davies-Bouldin) for the model selection visual. |

### B. Intermediate Datasets (Do NOT Import Simultaneously)

To avoid circular relationships, ambiguous paths, and duplicate data in Power BI:

- **Do NOT import `rfm_customer_metrics.csv`:** All 12 columns are fully included in `business_segments.csv`.
- **Do NOT import `customer_clusters.csv`:** All 15 columns are fully included in `business_segments.csv`.
- **Do NOT import `cluster_profiles.csv`:** Its 13 profile columns are fully subsumed and enriched within `segment_summary.csv`.
- **Do NOT import `clean_transactions.csv` directly into the customer model:** That dataset includes 133,949 guest/unidentified rows (`CustomerID = NaN`) retained for top-line financial auditing, whereas customer-level segmentation operates on `customer_transactions.csv`.

---

## 3. Recommended Semantic Model Relationships

The recommended schema is a clean **Star / Constellation Schema** with single-direction cross-filtering (`1` to `*`):

```
                        +----------------------+
                        | segment_summary (4)  |
                        | (DimSegment)         |
                        +----------------------+
                                   | 1
                                   |
                                   | [cluster_id]
                                   | Single Direction (1 -> *)
                                   v *
                        +----------------------+         +---------------------------+
                        | business_segments    | <-----> | marketing_opportunities   |
                        | (DimCustomer, 4,338) |    1:1  | (RefMarketing, 4)         |
                        +----------------------+         +---------------------------+
                                   | 1
                                   |
                                   | [customerid] = [CustomerID]
                                   | Single Direction (1 -> *)
                                   v *
                        +----------------------+
                        | customer_transactions|
                        | (FactTransactions)   |
                        | (392,692 rows)       |
                        +----------------------+

                        +----------------------+
                        | clustering_metrics   |
                        | (Disconnected, 9)    |
                        +----------------------+
```

### Relationship Configuration Table:

| From Table (Primary / 1) | From Column | To Table (Foreign / *) | To Column | Cardinality | Cross-Filter Direction | Security / Active |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `segment_summary` | `cluster_id` | `business_segments` | `cluster_id` | 1 to Many (`1:*`) | Single (`segment_summary` filters `business_segments`) | Active |
| `business_segments` | `customerid` | `customer_transactions` | `CustomerID` | 1 to Many (`1:*`) | Single (`business_segments` filters `customer_transactions`) | Active |
| `segment_summary` | `cluster_id` | `marketing_opportunities` | `cluster_id` | 1 to 1 (`1:1`) | Both (or merged into `segment_summary`) | Active |
| `clustering_metrics` | None | None | None | None | **Disconnected** | None |

---

## 4. Tables That Should NOT Be Unnecessarily Related

1. **Do NOT relate `clustering_metrics` to anything:**
   - The $K=2..10$ diagnostic table evaluates theoretical clustering alternatives. It does not map to individual transactions or customers. Keeping it disconnected prevents accidental model corruption.
2. **Do NOT create a direct relationship from `segment_summary` to `customer_transactions`:**
   - Filtering transactions by segment should propagate naturally through `business_segments`. Adding a direct link creates an ambiguous multi-path relationship.
3. **Do NOT enable Bi-Directional Cross-Filtering:**
   - Bi-directional filtering between `customer_transactions` and `business_segments` can cause unexpected context transitions, inflate DAX calculation times, and produce circular evaluation errors.

---

## 5. Step-by-Step Data Ingestion Guide

1. **Launch Power BI Desktop** and create a new report.
2. Select **Get Data** $\rightarrow$ **Text/CSV**.
3. Navigate to `data/processed/` and select:
   - `customer_transactions.csv`
   - `business_segments.csv`
   - `segment_summary.csv`
   - `marketing_opportunities.csv`
   - `clustering_metrics.csv`
4. In the Power Query preview dialog, click **Transform Data**.
5. **Set Proper Data Types:**
   - `customer_transactions`:
     - `InvoiceNo` $\rightarrow$ `Int64` (or Text)
     - `Quantity` $\rightarrow$ `Int64`
     - `InvoiceDate` $\rightarrow$ `DateTime`
     - `UnitPrice` $\rightarrow$ `Fixed Decimal (Currency)`
     - `CustomerID` $\rightarrow$ `Int64`
     - `Revenue` $\rightarrow$ `Fixed Decimal (Currency)`
   - `business_segments`:
     - `customerid` $\rightarrow$ `Int64`
     - `recency`, `frequency`, `R_score`, `F_score`, `M_score`, `cluster_id` $\rightarrow$ `Int64`
     - `monetary` $\rightarrow$ `Fixed Decimal (Currency)`
     - `first_purchase_date`, `last_purchase_date` $\rightarrow$ `DateTime`
   - `segment_summary`:
     - `cluster_id`, `customer_count` $\rightarrow$ `Int64`
     - `total_revenue`, `median_monetary`, `average_monetary` $\rightarrow$ `Fixed Decimal (Currency)`
     - `customer_percentage`, `revenue_percentage` $\rightarrow$ `Percentage` (divide by 100 if stored as integer percentages)
6. Click **Close & Apply**.
7. Navigate to the **Model View** and verify relationships match the architecture in Section 3 above.
8. Create the `_Measures` table and paste the DAX measures documented in [`powerbi/dax_measures.md`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/powerbi/dax_measures.md).

---

## 6. Directory Documentation Index

- [`powerbi/data_dictionary.md`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/powerbi/data_dictionary.md): Field-level schema, grain, and visual role dictionary.
- [`powerbi/dax_measures.md`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/powerbi/dax_measures.md): Complete DAX measure formulas, descriptions, and business logic.
- [`powerbi/dashboard_specification.md`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/powerbi/dashboard_specification.md): Detailed 4-page visual layout, field mappings, and card specifications.
- [`docs/powerbi_dashboard.md`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/docs/powerbi_dashboard.md): Enterprise dashboard overview, refresh strategy, and governance report.
