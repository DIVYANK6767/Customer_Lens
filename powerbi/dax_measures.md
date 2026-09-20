# DAX Measure Catalogue — CustomerLens Power BI Layer

This document contains the complete, production-ready DAX measure catalogue for the CustomerLens Power BI semantic model. All measures are designed to be organized into a dedicated measure group (`_Measures`) to maintain clean separation between data tables and reporting logic.

---

## 1. Architectural Principles & Best Practices

1. **Explicit Measures Over Implicit Columns:** Visuals should never bind raw numeric columns directly (e.g. dragging `Revenue` into a card). Explicit DAX measures enforce consistent calculation logic, proper context transition, and uniform number formatting.
2. **Dynamic Context vs. Precomputed Analytical Metrics:**
   - **Dynamic Measures:** Metrics that must recalculate dynamically when slicers change (e.g. filtering by country or date) must be implemented via DAX over `customer_transactions` or `business_segments`.
   - **Static Analytical Benchmarks:** Validated cluster-level metrics (e.g. *Median Recency = 8.0 days*, *Median Frequency = 10.0*, *Median Monetary = £3,730.61*) are non-linear, non-additive medians derived from the complete 4,338-customer population in Phase 9/10. For high-level segment scorecards, displaying the precomputed columns from `segment_summary` preserves verified statistical baselines. Dynamic measures (e.g. `MEDIAN(business_segments[recency])`) can be used when sliced by external dimensions such as country.
3. **Safe Division:** All ratios utilize `DIVIDE(Numerator, Denominator, 0)` to prevent division-by-zero errors.

---

## 2. Core Financial & Transactional Measures

### 2.1. Total Revenue
```dax
Total Revenue =
SUM(customer_transactions[Revenue])
```
- **Format:** Currency (`£#,##0.00`)
- **Business Definition:** Total gross monetary turnover generated across all completed transactions.
- **Expected Grain:** Filter context sensitive; evaluates across line items, orders, customers, dates, and segments.
- **Assumptions:** Validated on `customer_transactions` where `Revenue = Quantity * UnitPrice` and strictly positive (`> 0`). Overall benchmark reconciles exactly to **£8,887,208.89**.

---

### 2.2. Total Customers
```dax
Total Customers =
DISTINCTCOUNT(customer_transactions[CustomerID])
```
- **Format:** Whole Number (`#,##0`)
- **Business Definition:** Total distinct active customer accounts with at least one completed transaction in the current filter context.
- **Expected Grain:** Evaluated across the transaction fact table.
- **Assumptions:** Reconciles to **4,338** active customers across the full baseline.

---

### 2.3. Total Orders
```dax
Total Orders =
DISTINCTCOUNT(customer_transactions[InvoiceNo])
```
- **Format:** Whole Number (`#,##0`)
- **Business Definition:** Total distinct completed commercial transactions (invoices).
- **Expected Grain:** Evaluated across the transaction fact table.
- **Assumptions:** Excludes cancellations and zero/negative quantities per Phase 5 cleaning. Reconciles to **18,532** orders across the full baseline.

---

### 2.4. Average Order Value (AOV)
```dax
Average Order Value =
DIVIDE(
    [Total Revenue],
    [Total Orders],
    0
)
```
- **Format:** Currency (`£#,##0.00`)
- **Business Definition:** Average gross turnover generated per completed transaction.
- **Expected Grain:** Derived measure combining `[Total Revenue]` and `[Total Orders]`.
- **Assumptions:** Overall portfolio benchmark reconciles to **£479.56** (£8,887,208.89 / 18,532).

---

### 2.5. Total Units
```dax
Total Units =
SUM(customer_transactions[Quantity])
```
- **Format:** Whole Number (`#,##0`)
- **Business Definition:** Aggregate quantity of physical product units purchased across completed line items.
- **Expected Grain:** Line item level.
- **Assumptions:** Invariant verified in Phase 5: all line items have `Quantity > 0`. Total volume across the dataset reconciles to **5,152,002** units.

---

## 3. Customer Engagement & Repeat Purchase Measures

### 3.1. Repeat Customers
```dax
Repeat Customers =
COUNTROWS(
    FILTER(
        VALUES(customer_transactions[CustomerID]),
        CALCULATE(DISTINCTCOUNT(customer_transactions[InvoiceNo])) > 1
    )
)
```
- **Alternative (via Dimension Table):**
```dax
Repeat Customers (Dim) =
CALCULATE(
    COUNTROWS(business_segments),
    business_segments[frequency] > 1
)
```
- **Format:** Whole Number (`#,##0`)
- **Business Definition:** Number of distinct customers who have completed 2 or more distinct orders within the evaluation window.
- **Expected Grain:** Evaluated per customer account.
- **Assumptions:** Baseline benchmark reconciles to **2,845** customers (65.58% of the customer base).

---

### 3.2. One-Time Customers
```dax
One-Time Customers =
[Total Customers] - [Repeat Customers]
```
- **Format:** Whole Number (`#,##0`)
- **Business Definition:** Number of distinct customers who have completed exactly 1 transaction.
- **Expected Grain:** Evaluated per customer account.
- **Assumptions:** Baseline benchmark reconciles to **1,493** customers (34.42% of the customer base).

---

### 3.3. Repeat Customer Rate
```dax
Repeat Customer Rate =
DIVIDE(
    [Repeat Customers],
    [Total Customers],
    0
)
```
- **Format:** Percentage (`0.0%`)
- **Business Definition:** Proportion of active customers who completed more than one transaction.
- **Expected Grain:** Summary portfolio ratio.
- **Assumptions:** Portfolio baseline reconciles to **65.6%** (2,845 / 4,338).

---

### 3.4. Revenue per Customer
```dax
Revenue per Customer =
DIVIDE(
    [Total Revenue],
    [Total Customers],
    0
)
```
- **Format:** Currency (`£#,##0.00`)
- **Business Definition:** Mean gross turnover generated per active customer account.
- **Expected Grain:** Portfolio ratio.
- **Assumptions:** Baseline benchmark reconciles to **£2,048.69** (£8,887,208.89 / 4,338). Highly sensitive to heavy-tailed spenders (median spend is £668.57).

---

### 3.5. Average Orders per Customer
```dax
Average Orders per Customer =
DIVIDE(
    [Total Orders],
    [Total Customers],
    0
)
```
- **Format:** Decimal Number (`0.00`)
- **Business Definition:** Mean order velocity per customer across the observation window.
- **Expected Grain:** Portfolio ratio.
- **Assumptions:** Baseline benchmark reconciles to **4.27** orders per customer (18,532 / 4,338).

---

## 4. Segmentation & Concentration Measures

### 4.1. Segment Customer Count
```dax
Segment Customer Count =
COUNTROWS(business_segments)
```
- **Format:** Whole Number (`#,##0`)
- **Business Definition:** Count of customer accounts allocated to the current segment filter context.
- **Expected Grain:** Customer dimension level (`business_segments`).
- **Assumptions:** Requires single-direction relationship from `business_segments` to `customer_transactions`.

---

### 4.2. Customer Share %
```dax
Customer Share % =
DIVIDE(
    [Segment Customer Count],
    CALCULATE([Segment Customer Count], ALL(business_segments)),
    0
)
```
- **Format:** Percentage (`0.00%`)
- **Business Definition:** Proportion of the total customer base represented by the selected segment or cohort.
- **Expected Grain:** Segment level.
- **Assumptions:** Evaluates against the unfiltered customer dimension (`ALL(business_segments)`).
  - *High-Value Engaged:* 16.51% (716 / 4,338)
  - *Established Valuable:* 26.97% (1,170 / 4,338)
  - *Recent Developing:* 19.23% (834 / 4,338)
  - *Low-Engagement / Reactivation:* 37.30% (1,618 / 4,338)

---

### 4.3. Segment Revenue
```dax
Segment Revenue =
CALCULATE(
    [Total Revenue],
    KEEPFILTERS(business_segments)
)
```
- **Format:** Currency (`£#,##0.00`)
- **Business Definition:** Total gross turnover generated by customers belonging to the active segment context.
- **Expected Grain:** Evaluated over `customer_transactions` filtered through `business_segments`.

---

### 4.4. Segment Revenue %
```dax
Segment Revenue % =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], ALL(business_segments)),
    0
)
```
- **Format:** Percentage (`0.00%`)
- **Business Definition:** Percentage of total company turnover generated by the selected segment.
- **Expected Grain:** Segment level.
- **Assumptions:** Removes filters on `business_segments` while preserving external filters (e.g. date ranges) if applicable.
  - *High-Value Engaged:* 65.05% (£5,781,509.02)
  - *Established Valuable:* 23.54% (£2,092,321.70)
  - *Recent Developing:* 5.24% (£465,608.17)
  - *Low-Engagement / Reactivation:* 6.16% (£547,770.00)

---

### 4.5. Customer Revenue % (Pareto Share)
```dax
Customer Revenue % =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], ALL(customer_transactions)),
    0
)
```
- **Format:** Percentage (`0.00%`)
- **Business Definition:** Contribution of an individual customer or group to total enterprise gross turnover.
- **Expected Grain:** Customer row or group level.

---

### 4.6. Revenue Concentration Multiplier
```dax
Revenue Concentration Multiplier =
DIVIDE(
    [Segment Revenue %],
    [Customer Share %],
    0
)
```
- **Format:** Decimal (`0.00x`)
- **Business Definition:** Ratio of financial share to customer volume share ($\% \text{Revenue} / \% \text{Customers}$).
- **Expected Grain:** Segment level.
- **Assumptions:** Values $>1.0\text{x}$ indicate disproportionate revenue generation; values $<1.0\text{x}$ indicate under-indexing.
  - *High-Value Engaged:* **3.94x** (65.05% / 16.51%)
  - *Established Valuable:* **0.87x** (23.54% / 26.97%)
  - *Recent Developing:* **0.27x** (5.24% / 19.23%)
  - *Low-Engagement / Reactivation:* **0.17x** (6.16% / 37.30%)

---

## 5. Behavioral RFM Summary Measures

### 5.1. Average Recency
```dax
Average Recency =
AVERAGE(business_segments[recency])
```
- **Format:** Decimal Number (`0.0`)
- **Business Definition:** Arithmetic mean days elapsed since last purchase.
- **Expected Grain:** Evaluated over `business_segments`.

---

### 5.2. Average Frequency
```dax
Average Frequency =
AVERAGE(business_segments[frequency])
```
- **Format:** Decimal Number (`0.00`)
- **Business Definition:** Arithmetic mean completed orders per customer.
- **Expected Grain:** Evaluated over `business_segments`.

---

### 5.3. Average Monetary
```dax
Average Monetary =
AVERAGE(business_segments[monetary])
```
- **Format:** Currency (`£#,##0.00`)
- **Business Definition:** Arithmetic mean total monetary spend per customer.
- **Expected Grain:** Evaluated over `business_segments`.

---

### 5.4. Dynamic Median Measures vs. Precomputed Analytical Columns

```dax
Median Recency =
MEDIAN(business_segments[recency])

Median Frequency =
MEDIAN(business_segments[frequency])

Median Monetary =
MEDIAN(business_segments[monetary])
```

#### Analytical Implementation Guidance:
1. **When to use precomputed columns from `segment_summary`:**
   - On the **Executive Overview** and **Customer Segmentation Scorecard** pages, use the precomputed columns:
     - `segment_summary[median_recency]`
     - `segment_summary[median_frequency]`
     - `segment_summary[median_monetary]`
   - *Rationale:* These values reflect the exact deterministic medians validated in Phase 9/10 (e.g. Cluster 3 Median Recency = 8.0 d, Frequency = 10.0, Monetary = £3,730.61). They display instantly without scanning 4,338 customer rows.
2. **When to use DAX `MEDIAN()` measures:**
   - In the **RFM Analysis** and **Customer Explorer** pages when interactive cross-filtering by country, date range, or spend thresholds is active.

---

## 6. Measure Directory Structure (`_Measures` Table)

To establish an organized Power BI model, create an empty calculated table:
```dax
_Measures = { BLANK() }
```
Then assign each measure to its respective Display Folder:

| Display Folder | Measures Included |
| :--- | :--- |
| **01 Core Financials** | `[Total Revenue]`, `[Total Units]`, `[Average Order Value]` |
| **02 Volumes & Counts** | `[Total Customers]`, `[Total Orders]`, `[Segment Customer Count]` |
| **03 Engagement & Retention** | `[Repeat Customers]`, `[One-Time Customers]`, `[Repeat Customer Rate]`, `[Revenue per Customer]`, `[Average Orders per Customer]` |
| **04 Segmentation & Pareto** | `[Customer Share %]`, `[Segment Revenue]`, `[Segment Revenue %]`, `[Customer Revenue %]`, `[Revenue Concentration Multiplier]` |
| **05 RFM Averages & Medians** | `[Average Recency]`, `[Average Frequency]`, `[Average Monetary]`, `[Median Recency]`, `[Median Frequency]`, `[Median Monetary]` |
