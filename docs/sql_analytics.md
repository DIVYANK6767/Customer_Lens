# SQL Analytics Layer Report
## CustomerLens — Customer Segmentation & Targeted Marketing Analytics

---

## 1. Purpose of the SQL Analytical Layer

The **SQL Analytical Layer** in **CustomerLens** serves as the relational data foundation bridging raw transaction ingestion and downstream customer intelligence. While Phase 6 Exploratory Data Analysis (EDA) in Python provided statistical exploration and distribution visualizations, enterprise production analytics requires a robust, scalable, and queryable relational data warehouse engine.

The primary objectives of this SQL layer are:
1. **Deliver Single-Source-of-Truth KPIs:** Execute standardized business intelligence aggregations directly inside the PostgreSQL 18 relational engine.
2. **Demonstrate Production-Grade SQL Engineering:** Model complex customer behaviors using Common Table Expressions (CTEs), multi-level aggregations, window ranking functions (`RANK()`, `DENSE_RANK()`, `ROW_NUMBER()`), time-series delta tracking (`LAG()`), and continuous percentile calculations (`PERCENTILE_CONT`).
3. **Establish Portfolio-Grade Business Querying:** Answer 20 high-value executive, commercial, and operational questions with auditable, deterministic SQL code.
4. **Prepare Data Structures for Downstream RFM:** Formulate customer-level behavioral summaries (recency, frequency, monetary aggregates) ready for subsequent segmentation and machine learning.

---

## 2. Data Source & Lineage

The data source for the SQL analytical layer is the fully cleaned and validated customer dataset generated in Phase 5:
- **Source File:** `data/processed/customer_transactions.csv`
- **Integrity Baseline:** 392,692 rows, 11 columns, 0 missing customer IDs, 100% completed `Sale` records, strictly positive unit prices and quantities.
- **Ingestion Mechanism:** Ingested via streaming PostgreSQL `COPY` within an atomic transaction in `src/load_to_postgres.py`, guaranteeing idempotent loading.

---

## 3. PostgreSQL Schema Architecture

To prevent collision with system catalogs and support enterprise multi-tier data modeling, the database is partitioned into a dedicated schema:
- **Database:** `customer_lens`
- **Schema:** `analytics`
- **Isolation Principle:** Application code and BI dashboards query the `analytics` schema directly, abstracting storage optimizations and access permissions from raw ingestion tables.

---

## 4. Analytical Table Specification

The core fact table is `analytics.customer_transactions`, structured as follows:

```sql
CREATE TABLE analytics.customer_transactions (
    InvoiceNo           TEXT            NOT NULL,
    StockCode           TEXT            NOT NULL,
    Description         TEXT,
    Quantity            INTEGER         NOT NULL,
    InvoiceDate         TIMESTAMP       NOT NULL,
    UnitPrice           NUMERIC(12, 4)  NOT NULL,
    CustomerID          TEXT            NOT NULL,
    Country             TEXT            NOT NULL,
    TransactionType     TEXT            NOT NULL,
    DescriptionMissing  BOOLEAN         NOT NULL DEFAULT FALSE,
    Revenue             NUMERIC(14, 2)  NOT NULL
);
```

### Table Invariants & Physical Guarantees
- **Row Count Guarantee:** Exactly `392,692` records.
- **Volume & Price Constraints:** `Quantity > 0` and `UnitPrice > 0`.
- **Identity Guarantee:** `CustomerID IS NOT NULL`.
- **Financial Precision:** `Revenue = Quantity * UnitPrice` stored as `NUMERIC(14, 2)` to eliminate floating-point rounding errors.

---

## 5. Standardized Business Definitions

To maintain analytical consistency across all queries, reports, and tests, the following business definitions are strictly enforced:

| Business Entity | Operational Definition | SQL Implementation |
| :--- | :--- | :--- |
| **Active Customer** | A unique, verified account with at least one completed order. | `COUNT(DISTINCT customerid)` |
| **Completed Order** | A discrete checkout transaction represented by a unique invoice. | `COUNT(DISTINCT invoiceno)` |
| **Gross Revenue** | Total top-line financial spend across completed sales. | `SUM(revenue)` |
| **Physical Units** | Aggregate quantity of merchandise transacted. | `SUM(quantity)` |
| **Average Order Value (AOV)** | Average monetary spend per completed invoice. | `SUM(revenue) / COUNT(DISTINCT invoiceno)` |
| **One-Time Customer** | An account with exactly 1 completed invoice. | `COUNT(DISTINCT invoiceno) = 1` |
| **Repeat Customer** | An account with 2 or more completed invoices. | `COUNT(DISTINCT invoiceno) > 1` |
| **Reference Date** | Latest recorded transaction timestamp plus 1 day. | `MAX(invoicedate) + INTERVAL '1 day'` |
| **Customer Inactivity** | Elapsed days between customer's last order and reference date. | `EXTRACT(EPOCH FROM (ref - last_order)) / 86400` |

---

## 6. Customer Metrics Analysis

Customer metrics evaluate individual purchasing patterns, customer lifetime value, and order frequencies across all 4,338 active accounts.

### Key Empirical Findings:
- **Customer Base:** 4,338 active identified customers.
- **Average Spend per Customer:** £2,048.69.
- **Median Spend per Customer:** £668.56 (indicating substantial positive skewness).
- **Highest Spender:** Customer ID `14646` generated **£280,206.02** across 73 completed orders (196,915 physical units).
- **Top 5 Customers by Revenue:**
  1. `14646`: £280,206.02 (Netherlands / Wholesale)
  2. `18102`: £259,657.30 (United Kingdom)
  3. `17450`: £194,390.79 (United Kingdom)
  4. `16446`: £168,472.50 (United Kingdom / Bulk buyer: 2 orders)
  5. `14911`: £143,711.17 (EIRE / Frequent: 201 orders)

### SQL Implementation Example: Customer LTV & AOV
```sql
SELECT 
    customerid,
    COUNT(DISTINCT invoiceno) AS total_orders,
    SUM(quantity) AS total_units_purchased,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value,
    MIN(invoicedate) AS first_purchase_date,
    MAX(invoicedate) AS last_purchase_date
FROM analytics.customer_transactions
GROUP BY customerid
ORDER BY total_revenue DESC;
```
*Why this technique:* Grouping strictly by `customerid` guarantees 1-to-1 customer integrity without duplicating accounts that transacted across borders.

---

## 7. Revenue Metrics & Time-Series Velocity

Financial analytics examine macro sales velocity, month-over-month trajectories, and basket monetary distribution across the 13-month operating window.

### Key Empirical Findings:
- **Total Gross Revenue:** £8,887,208.89.
- **Total Orders:** 18,532 completed checkouts.
- **Portfolio AOV:** £479.56.
- **Basket Percentiles:**
  - 25th Percentile: £153.11
  - Median (50th Percentile): **£290.00**
  - Mean AOV: £479.56
  - 75th Percentile: £492.70
  - 90th Percentile: £914.80
  - 99th Percentile: £3,130.07
  - Maximum Order: £168,469.60

### Monthly Sales Trajectory (Dec 2010 – Dec 2011)

| Month | Active Accounts | Orders | Units Sold | Monthly Revenue (£) | AOV (£) | MoM Growth (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **2010-12** | 885 | 1,400 | 311,048 | £572,713.89 | £409.08 | — |
| **2011-01** | 741 | 987 | 277,886 | £569,445.41 | £576.95 | -0.57% |
| **2011-02** | 758 | 998 | 265,038 | £447,137.43 | £448.03 | -21.48% |
| **2011-03** | 974 | 1,321 | 347,582 | £595,500.76 | £450.80 | +33.18% |
| **2011-04** | 856 | 1,149 | 292,222 | £469,200.36 | £408.36 | -21.21% |
| **2011-05** | 1,056 | 1,555 | 373,611 | £678,594.56 | £436.40 | +44.63% |
| **2011-06** | 991 | 1,393 | 363,699 | £661,213.69 | £474.67 | -2.56% |
| **2011-07** | 949 | 1,331 | 369,432 | £600,091.01 | £450.86 | -9.24% |
| **2011-08** | 935 | 1,281 | 398,121 | £645,343.90 | £503.78 | +7.54% |
| **2011-09** | 1,266 | 1,755 | 544,821 | £952,838.38 | £542.93 | +47.65% |
| **2011-10** | 1,364 | 1,929 | 593,908 | £1,039,318.79 | £538.79 | +9.08% |
| **2011-11** | 1,664 | 2,657 | 669,811 | **£1,161,817.38** | £437.27 | +11.79% |
| **2011-12** (partial) | 617 | 776 | 144,828 | £353,993.33 | £456.18 | -69.53% |

*Note: December 2011 records capture transactions only through December 9, 2011 12:50:00 (partial month).*

### SQL Implementation Example: Month-over-Month Growth with LAG()
```sql
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', invoicedate)::DATE AS sales_month,
        COUNT(DISTINCT invoiceno) AS monthly_orders,
        ROUND(SUM(revenue), 2) AS current_revenue
    FROM analytics.customer_transactions
    GROUP BY DATE_TRUNC('month', invoicedate)
)
SELECT 
    sales_month,
    monthly_orders,
    current_revenue,
    LAG(current_revenue, 1) OVER (ORDER BY sales_month ASC) AS previous_month_revenue,
    ROUND(current_revenue - LAG(current_revenue, 1) OVER (ORDER BY sales_month ASC), 2) AS revenue_delta_gbp,
    ROUND(
        (current_revenue - LAG(current_revenue, 1) OVER (ORDER BY sales_month ASC)) * 100.0 / 
        NULLIF(LAG(current_revenue, 1) OVER (ORDER BY sales_month ASC), 0),
        2
    ) AS mom_growth_pct
FROM monthly_revenue
ORDER BY sales_month ASC;
```
*Why this technique:* `LAG()` cleanly references the prior row in chronological sequence without requiring self-joins, while `NULLIF` guards against division-by-zero on the first record.

---

## 8. Country Metrics & Geographic Breakdown

Transactions span 37 destination nations. Domestic UK sales represent the vast majority of volume, while non-UK accounts exhibit substantially higher Average Order Values and spend per customer.

### Top 10 Geographic Markets by Revenue

| Country | Active Customers | Completed Orders | Units Sold | Total Revenue (£) | Global Share (%) | AOV (£) | Rev / Customer (£) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **United Kingdom** | 3,920 | 16,646 | 4,256,740 | £7,285,024.64 | 81.97% | £437.64 | £1,858.42 |
| **Netherlands** | 9 | 94 | 200,937 | £285,446.34 | 3.21% | £3,036.66 | £31,716.26 |
| **EIRE** | 3 | 260 | 140,275 | £265,262.46 | 2.98% | £1,020.24 | £88,420.82 |
| **Germany** | 94 | 457 | 119,261 | £228,678.40 | 2.57% | £500.39 | £2,432.75 |
| **France** | 87 | 389 | 111,471 | £208,934.31 | 2.35% | £537.11 | £2,401.54 |
| **Australia** | 9 | 57 | 83,901 | £138,453.81 | 1.56% | £2,429.01 | £15,383.76 |
| **Switzerland** | 21 | 51 | 30,082 | £56,448.35 | 0.64% | £1,106.83 | £2,688.02 |
| **Spain** | 30 | 90 | 27,940 | £61,558.88 | 0.69% | £683.99 | £2,051.96 |
| **Belgium** | 25 | 98 | 23,237 | £41,196.34 | 0.46% | £420.37 | £1,647.85 |
| **Sweden** | 8 | 36 | 36,083 | £38,367.83 | 0.43% | £1,065.77 | £4,795.98 |

*Analytical Note:* When filtering for countries with at least 5 accounts to eliminate sample skew, Netherlands (£31,716.26/cust) and Australia (£15,383.76/cust) generate the highest commercial yield per customer account.

---

## 9. Time-Based Analytics: Diurnal & Weekly Rhythms

### Day-of-Week Operational Analysis (`EXTRACT(ISODOW)`)

| Day of Week | ISO Day | Orders | Customers | Total Revenue (£) | Revenue Share (%) | AOV (£) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Thursday** | 4 | 4,033 | 2,160 | £1,973,284.27 | 22.20% | £489.28 |
| **Wednesday** | 3 | 3,446 | 2,058 | £1,582,698.84 | 17.81% | £459.29 |
| **Tuesday** | 2 | 3,185 | 1,940 | £1,564,286.06 | 17.60% | £491.14 |
| **Monday** | 1 | 2,862 | 1,770 | £1,365,038.31 | 15.36% | £476.95 |
| **Friday** | 5 | 2,829 | 1,778 | £1,327,247.93 | 14.93% | £469.16 |
| **Sunday** | 7 | 2,177 | 1,326 | £1,074,653.48 | 12.09% | £493.64 |
| **Saturday** | 6 | 0 | 0 | £0.00 | 0.00% | £0.00 |

*Operational Discovery:* The business was closed on Saturdays (0 transactions). Thursday is the highest volume and revenue day of the week, accounting for 22.20% of annual turnover.

### Hourly Diurnal Rhythm
- **Operating Hours:** 06:00 to 20:00.
- **Peak Order Velocity:** 12:00 PM (3,129 orders, £1,677,938.86 revenue, 18.88% share).
- **Secondary Peak:** 13:00 PM (2,646 orders, £1,496,252.12 revenue, 16.84% share).
- **Core Trading Window:** 10:00 AM to 15:00 PM accounts for over 80% of all daily transactions.

---

## 10. Repeat vs. One-Time Customer Analysis

Understanding customer retention and loyalty dynamics is critical for commercial segmentation:

| Metric | One-Time Customers | Repeat Customers | Total Active Base | Repeat Share |
| :--- | :---: | :---: | :---: | :---: |
| **Customer Accounts** | 1,493 | 2,845 | 4,338 | **65.58%** |
| **Completed Orders** | 1,493 | 17,039 | 18,532 | **91.94%** |
| **Gross Revenue (£)** | £613,989.56 | £8,273,219.33 | £8,887,208.89 | **93.09%** |
| **Average Order Value (£)** | £411.25 | £485.55 | £479.56 | +18.07% higher |

### Strategic Insight:
While repeat customers represent **65.58%** of the active customer directory, they drive **91.94% of all orders** and generate **93.09% of total company revenue**. Customer acquisition without retention would capture only 6.91% of value.

---

## 11. Customer Concentration & Pareto Analysis

To empirically evaluate revenue concentration, customers were ranked in descending order of spend and grouped into deciles (10 equal tiers of 434 accounts).

### Decile Concentration Analysis (`NTILE(10)`)

| Decile | Customers | Min Spend (£) | Max Spend (£) | Decile Revenue (£) | Revenue Share (%) | Cumulative Share (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Decile 1 (Top 10%)** | 434 | £3,641.24 | £280,206.02 | £5,461,374.89 | **61.45%** | **61.45%** |
| **Decile 2** | 434 | £2,055.51 | £3,640.67 | £1,175,925.93 | 13.23% | **74.68%** |
| **Decile 3** | 434 | £1,346.97 | £2,054.36 | £725,127.48 | 8.16% | **82.84%** |
| **Decile 4** | 434 | £933.26 | £1,345.62 | £489,266.69 | 5.51% | 88.35% |
| **Decile 5** | 434 | £668.56 | £932.97 | £342,309.30 | 3.85% | 92.20% |
| **Decile 6** | 434 | £487.02 | £668.43 | £251,250.14 | 2.83% | 95.03% |
| **Decile 7** | 434 | £349.55 | £486.82 | £178,812.85 | 2.01% | 97.04% |
| **Decile 8** | 434 | £248.61 | £349.27 | £131,201.05 | 1.48% | 98.52% |
| **Decile 9** | 433 | £155.17 | £248.10 | £86,192.65 | 0.97% | 99.49% |
| **Decile 10 (Bottom 10%)**| 433 | £3.75 | £155.05 | £45,747.91 | 0.51% | 100.00% |

### Empirical Pareto Threshold (Q11 Verification):
Querying the exact cumulative revenue threshold reveals that **Customer Rank 1,130** (spending £1,591.45) crosses the 80% boundary:
- **Exact Customers Generating ~80% of Spend:** **1,130 accounts**
- **Proportion of Total Base:** **26.05%**
- **Cumulative Revenue Generated:** **£7,110,647.95 (80.01%)**
This confirms that the customer spend distribution closely tracks the classical Pareto principle (~26% of accounts generate ~80% of turnover).

---

## 12. Advanced SQL Window Functions Demonstrated

The analytical implementation incorporates diverse window functions to solve complex analytical problems:

### 1. Ranking Functions: `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()`
- **Usage:** Used in `customer_metrics.sql` (Section C & H) and `revenue_analysis.sql` (Section D).
- **Rationale:** `ROW_NUMBER()` produces strict monotonic numbering required for Pareto cutoffs; `RANK()` identifies tied spenders while preserving spacing; `DENSE_RANK()` ranks monthly sales without skipping positions.

### 2. Time-Series Offset: `LAG()`
- **Usage:** Used in `revenue_analysis.sql` (Section B) for month-over-month growth calculations.
- **Rationale:** Evaluates the immediately preceding sales period in a single scan without computationally expensive self-joins.

### 3. Running Total & Frame Specification: `SUM(...) OVER (...)`
- **Usage:** Used in `customer_metrics.sql` (Section E) and `business_questions.sql` (Q11, Q20).
- **Syntax:** `SUM(customer_revenue) OVER (ORDER BY customer_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`.
- **Rationale:** Generates continuous cumulative totals for Lorenz curve construction.

### 4. Continuous Percentile Calculations: `PERCENTILE_CONT()`
- **Usage:** Used in `revenue_analysis.sql` (Section H) and `business_questions.sql` (Q16, Q17).
- **Rationale:** Calculates true statistical medians (P50) and quartiles (P25, P75, P90, P99) directly in the database engine to benchmark basket sizes and filter outlier cohorts.

### 5. Equal-Frequency Binning: `NTILE()`
- **Usage:** Used in `business_questions.sql` (Q20) for customer decile segmentation.
- **Rationale:** Equitably divides 4,338 ranked accounts into 10 deciles of 433–434 accounts each.

---

## 13. Common Table Expressions (CTEs) & Modular Architecture

Rather than constructing unreadable nested subqueries, queries are structured using modular CTE pipelines:
1. **Separation of Granularities:** Transaction line-item rows (`analytics.customer_transactions`) are aggregated first into order-level or customer-level summaries inside an initial CTE.
2. **Benchmark Calculation:** Portfolio-wide percentiles or totals are computed in a secondary CTE.
3. **Cross-Join & Filtering:** Analytical results join the customer summary to the benchmark CTE, ensuring clean execution plans and highly readable queries.

---

## 14. Important Business Questions Answered

| Question ID | Core Business Inquiry | Empirical Answer | Strategic Implication |
| :--- | :--- | :--- | :--- |
| **Q1** | Active Customer Count | **4,338** | Baseline customer directory for segmentation. |
| **Q2** | Completed Order Count | **18,532** | Transactional checkout volume. |
| **Q3** | Total Gross Revenue | **£8,887,208.89** | Top-line financial scale. |
| **Q4** | Average Order Value (AOV) | **£479.56** | Median basket is £290.00; mean pulled up by bulk buyers. |
| **Q5** | Repeat Customer Rate | **65.58%** (2,845 customers) | Strong customer retention foundation. |
| **Q6** | Repeat Customer Revenue Share | **93.09%** (£8,273,219.33) | Business viability depends on retention. |
| **Q7** | Top Revenue Country | **United Kingdom** (£7.28M, 81.97%) | Domestic home market dominance. |
| **Q8** | Top Revenue Customer | **ID 14646** (£280,206.02, 73 orders) | Key enterprise wholesale account. |
| **Q9** | Top 10 Customer Concentration | **17.30%** (£1,537,659.21) | Moderate commercial concentration risk. |
| **Q10** | Top 20 Customer Concentration | **23.91%** (£2,125,228.46) | Top 20 buyers account for nearly 1/4 of sales. |
| **Q11** | Pareto 80% Spend Threshold | **26.05% of customers** (1,130 accounts) | Exact verification of 80/20 commercial rule. |
| **Q12** | Inactive / Dormant Accounts | **374.1 days max recency** | Critical candidates for win-back campaigns. |
| **Q13** | Macro Monthly Sales Trend | **Expanding Q3/Q4 2011** | Strong fourth-quarter seasonal holiday surge. |
| **Q14** | Peak Revenue Month | **November 2011** (£1.16M, 13.01%) | Peak holiday gift procurement window. |
| **Q15** | Highest Yield per Customer | **Netherlands** (£31.7k/cust), **Australia** (£15.4k/cust) | High-value export wholesale channels. |
| **Q16** | High Frequency, Low AOV Buyers | **ID 12748** (209 orders, AOV £158.15) | Ideal candidates for basket-building cross-sell. |
| **Q17** | High Revenue, Low Frequency Buyers | **ID 16446** (2 orders, £168,472.50) | High-value bulk wholesale accounts. |
| **Q18** | Orders from Repeat Buyers | **91.94%** (17,039 orders) | Massive transactional dominance of repeat buyers. |
| **Q19** | One-Time Customer Volume | **34.42%** (1,493 customers) | Significant single-purchase conversion attrition. |
| **Q20** | Top Decile Spend Share | **61.45%** (Top 434 accounts) | Portfolio spend is heavily top-loaded. |

---

## 15. SQL Engineering & Design Decisions

1. **Strict Identifier Casing:** All SQL tables and column names use lowercase unquoted identifiers (`customerid`, `invoiceno`, `revenue`), matching native PostgreSQL catalog standards.
2. **Safe Division Handling:** All percentage and AOV calculations wrap divisors with `NULLIF(..., 0)` to guarantee resilience against division-by-zero errors.
3. **Dynamic Reference Date Anchoring:** Customer recency calculates inactivity relative to `MAX(invoicedate) + INTERVAL '1 day'` (`2011-12-10 12:50:00`), avoiding fragile hardcoded dates while reflecting real-world snapshot analytics.
4. **Strict Customer-Level Aggregation:** Top customer and frequency queries group strictly by `customerid` (with `MAX(country)` for geographic context) to ensure customers who transacted in multiple countries are not split.
5. **Separation of Invoices from Line Items:** Line-item rows are never mistaken for orders; all order counts explicitly use `COUNT(DISTINCT invoiceno)`.

---

## 16. Analytical Limitations

1. **Completed Sales Scope:** This analytical layer operates strictly on `analytics.customer_transactions` (completed sales by identified customers). It intentionally excludes cancellations, guest checkouts, and fee adjustments.
2. **Causality vs. Description:** SQL analytical queries describe *what* occurred (e.g. export accounts exhibit higher AOV) without inferring unobserved operational causes (e.g. shipping contracts or buyer motives).
3. **Single Year Horizon:** With 13 months of data (Dec 2010 to Dec 2011), true year-over-year seasonality cannot be conclusively confirmed without multiple annual cycles.
4. **Bridge to Phase 8:** This phase intentionally omits customer segmentation clusters and RFM scores, which will be engineered in subsequent phases.
