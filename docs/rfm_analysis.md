# RFM (Recency, Frequency, Monetary) Analysis Report
## CustomerLens â€” Customer Segmentation & Targeted Marketing Analytics

---

## 1. What is RFM?

**RFM (Recency, Frequency, Monetary)** is an established behavioral modeling framework in quantitative marketing and customer relationship management (CRM). Rather than categorizing customers using static demographic attributes (such as age or income), RFM evaluates accounts based on their actual historical transaction events:

1. **Recency ($R$):** How recently did the customer place an order?
2. **Frequency ($F$):** How often does the customer place orders?
3. **Monetary ($M$):** How much total financial turnover does the customer generate?

By transforming high-dimensional transaction event logs into a low-dimensional, customer-level representation, RFM quantifies customer engagement and lifetime monetary contribution.

---

## 2. Why RFM is Useful

In retail and e-commerce analytics, customer behavior follows distinct commercial dynamics:
- **Past Behavior Predicts Future Activity:** Empirical marketing research demonstrates that customers who purchased recently are more likely to respond to subsequent outreach than dormant accounts.
- **Repeat Purchasing Drives Business Viability:** In CustomerLens, repeat buyers represent 65.58% of the customer base but account for **91.94% of all orders** and **93.09% of total revenue**. RFM distinguishes habitual repeat buyers from single-order buyers.
- **Identifies Revenue Concentration:** By measuring individual spend, RFM isolates key commercial accounts (e.g. wholesale buyers) from low-spend retail shoppers.
- **Enables Differentiated Marketing Strategies:** Facilitates targeted, hypothesis-driven marketing (e.g. VIP retention vs. first-order nurture vs. win-back outreach) rather than generic, one-size-fits-all broadcasts.

---

## 3. Mathematical & Operational Definitions

### Recency ($R$)
- **Definition:** The elapsed time in days between the customer's most recent completed checkout and the dataset reference anchor date.
- **Mathematical Formula:**
  $$\text{Recency}_i = \left\lfloor \frac{\text{Reference Date} - \max(\text{InvoiceDate}_i)}{1\text{ day}} \right\rfloor$$
- **Interpretation:** Strictly non-negative integer ($\text{Recency} \ge 0$). Lower recency values indicate more recent purchasing activity.

### Frequency ($F$)
- **Definition:** The count of unique completed checkout invoices associated with the customer account.
- **Mathematical Formula:**
  $$\text{Frequency}_i = \left| \{ \text{InvoiceNo}_{i, j} \} \right|$$
- **Interpretation:** Strictly positive integer ($\text{Frequency} \ge 1$). Transaction line-item rows are never counted as orders.

### Monetary ($M$)
- **Definition:** The cumulative gross revenue generated across all completed sales by the customer.
- **Mathematical Formula:**
  $$\text{Monetary}_i = \sum_{j} \text{Revenue}_{i, j} = \sum_{j} (\text{Quantity}_{i, j} \times \text{UnitPrice}_{i, j})$$
- **Interpretation:** Strictly positive currency value ($\text{Monetary} > 0$), expressed in GBP (Â£) rounded to 2 decimal places.

---

## 4. Reference Date Formulation

Because this is a retrospective analytical dataset, elapsed days cannot be computed relative to the current calendar date (`CURRENT_DATE` or `datetime.now()`), which would falsely inflate all recencies by over a decade.

- **Source Maximum Transaction Timestamp:** `2011-12-09 12:50:00`
- **Dynamic Reference Date:**
  $$\text{Reference Date} = \max(\text{InvoiceDate}) + 1\text{ day} = \text{2011-12-10 12:50:00}$$
- **Operational Rationale:** Adding an offset of 1 full day guarantees that the most recent customer transaction (occurring on December 9) has an integer recency of exactly 1 day ($\ge 0$), avoiding fractional day artifacts and providing a standard operational snapshot anchor.

---

## 5. Data Source & Customer Inclusion Rules

### Data Source
The RFM features are engineered from `data/processed/customer_transactions.csv`, matching the PostgreSQL fact table `analytics.customer_transactions`.

### Strict Inclusion Invariants
1. **Identified Customer Accounts Only:** `CustomerID IS NOT NULL` (eliminates unattributed guest checkouts).
2. **Completed Purchases Only:** `TransactionType == 'Sale'` (cancellations and credit notes excluded).
3. **Valid Pricing and Volume:** `Quantity > 0` and `UnitPrice > 0`.
4. **Strict Customer Uniqueness:** Exactly one row per customer ID in the final feature matrix.

---

## 6. Empirical RFM Distribution Summary

| Metric Feature | Mean | Std Dev | Min | P25 (Q1) | Median (P50) | P75 (Q3) | P90 | P99 | Max | Skewness |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Recency (Days)** | 92.5 | 100.0 | 1 | 18 | 51 | 142 | 263 | 369 | 374 | +1.25 |
| **Frequency (Orders)** | 4.27 | 7.70 | 1 | 1 | 2 | 5 | 9 | 30 | 209 | +9.80 |
| **Monetary (Â£)** | Â£2,048.69 | Â£8,985.23 | Â£3.75 | Â£306.48 | Â£668.57 | Â£1,660.60 | Â£3,641.24 | Â£17,575.06 | Â£280,206.02 | +19.39 |

### Key Empirical Invariants Verified
- **Active Customers ($N$):** Exactly `4,338`
- **Total Frequency ($\sum F$):** Exactly `18,532` completed orders
- **Total Monetary ($\sum M$):** Exactly `Â£8,887,208.89`

---

## 7. Outlier Inspection & Characterization

In statistical screening, the interquartile range rule ($Q_3 + 1.5 \times \text{IQR}$) flags:
- **Frequency Outliers:** 318 customers ($> 11$ orders), generating **Â£3,865,047.88** (43.49% of total revenue).
- **Monetary Outliers:** 423 customers ($> Â£3,691.77$), generating **Â£5,386,432.40** (60.61% of total revenue).

### Data Errors vs. Genuine Commercial Behavior
- **Inspection Finding:** Detailed review of transaction records confirms that extreme customers (e.g. Customer `14646` with 73 orders and Â£280,206.02 spend; Customer `18102` with 60 orders and Â£259,657.30 spend; Customer `16446` with 2 orders and Â£168,472.50 spend) represent **genuine commercial wholesale accounts** and bulk exporters.
- **Handling Principle:** These accounts must **never be deleted**. Truncating or deleting them would eliminate over 60% of commercial revenue.
- **Treatment Strategy:** Raw values are preserved in the feature store. In Phase 9 (K-Means), log-transformation ($\log(x + 1)$) and robust scaling will be applied to prevent distance distortion during clustering.

---

## 8. Correlation Structure

| Pairwise Relationship | Pearson ($r$) | Spearman ($\rho$) | Analytical Interpretation |
| :--- | :---: | :---: | :--- |
| **Frequency vs. Monetary** | +0.84 | +0.76 | Strong positive relationship. High-frequency buyers drive superior cumulative revenue. |
| **Recency vs. Frequency** | -0.21 | -0.59 | Moderate-to-strong negative monotonic relationship. Customers who purchase frequently tend to have ordered recently. |
| **Recency vs. Monetary** | -0.12 | -0.45 | Moderate negative monotonic relationship. High-spending accounts maintain shorter inter-purchase intervals. |

---

## 9. RFM Quantile Scoring Methodology

We adopt a 5-tier quantile scoring framework (scores 1 through 5):
- **$R\_Score$:** 5 = Most Recent (lowest recency, top 20%), 1 = Least Recent (highest recency, bottom 20%).
- **$F\_Score$:** 5 = Highest Order Frequency, 1 = Lowest Order Frequency.
- **$M\_Score$:** 5 = Highest Spend (top 20%), 1 = Lowest Spend (bottom 20%).

### Graceful Resolution of Duplicate Quantile Boundaries
Standard `pd.qcut` splits data into equal frequency percentiles. However, in retail datasets, order frequency is heavily discrete:
- 34.42% of customers have $\text{Frequency} = 1$
- 19.25% of customers have $\text{Frequency} = 2$

Consequently, 53.67% of accounts reside in the bottom two order tiers, causing quantile boundary edges to collide (`[1.0, 1.0, 2.0, 3.0, 6.0, 209.0]`).
- **Solution:** Our scoring implementation applies `pd.qcut(..., duplicates='drop')`.
- When duplicate edges occur, the function drops redundant boundaries, producing 4 clean, non-overlapping frequency tiers (`[1â€“2 orders]`, `[3 orders]`, `[4â€“6 orders]`, `[7+ orders]`) labeled deterministically with valid integer scores in range $[1, 5]$.
- Identical customers receive identical scores; no arbitrary ordering artifacts are introduced.

---

## 10. Analytical Customer Segments

Using the combination of $R\_Score$ and $F\_Score$, accounts are mapped into 8 transparent, mutually exclusive behavioral segments:

| Segment Name | Exact Boolean Rule | Behavioral Description |
| :--- | :--- | :--- |
| **Champions** | $R \ge 4 \text{ and } F \ge 4$ | Bought recently, buy frequently, and generate top-tier spend. |
| **Loyal Customers** | $R \ge 3 \text{ and } F \ge 3$ *(excl. Champions)* | Steady repeat buyers with dependable purchase velocity. |
| **Potential Loyalists** | $R \ge 4 \text{ and } F \in [2, 3]$ | Recent buyers with 2â€“3 purchases; showing conversion potential. |
| **Recent Customers** | $R \ge 4 \text{ and } F = 1$ | New accounts who completed their first purchase recently. |
| **At Risk** | $R \le 2 \text{ and } F \ge 3$ | Formerly frequent repeat buyers who have not purchased recently. |
| **Need Attention** | $R = 3 \text{ and } F \in [1, 2]$ | Moderate recency and low frequency; engagement is cooling. |
| **Hibernating** | $R = 2 \text{ and } F \le 2$ | Inactive for an extended duration; low historical frequency. |
| **Lost** | $R = 1 \text{ and } F \le 2$ | Longest elapsed inactivity (over 180+ days) and single/low purchases. |

---

## 11. Empirical Segment Scorecard

| Segment Name | Customers | Pct Base | Completed Orders | Total Revenue (Â£) | Pct Revenue | Mean Recency | Mean Freq | Mean Spend (Â£) | AOV (Â£) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Champions** | 578 | 13.32% | 8,788 | Â£4,678,619.12 | **52.64%** | 8.8d | 15.20 | Â£8,094.49 | Â£532.39 |
| **Loyal Customers** | 721 | 16.62% | 3,744 | Â£1,659,183.05 | **18.67%** | 43.1d | 5.19 | Â£2,301.22 | Â£443.16 |
| **Potential Loyalists** | 210 | 4.84% | 496 | Â£317,665.25 | **3.57%** | 13.2d | 2.36 | Â£1,512.69 | Â£640.45 |
| **Recent Customers** | 527 | 12.15% | 527 | Â£251,555.20 | **2.83%** | 14.1d | 1.00 | Â£477.33 | Â£477.33 |
| **At Risk** | 203 | 4.68% | 895 | Â£401,986.37 | **4.52%** | 160.0d | 4.41 | Â£1,980.23 | Â£449.15 |
| **Need Attention** | 594 | 13.69% | 848 | Â£434,142.10 | **4.89%** | 51.5d | 1.43 | Â£730.88 | Â£511.96 |
| **Hibernating** | 676 | 15.58% | 948 | Â£487,798.15 | **5.49%** | 114.7d | 1.40 | Â£721.60 | Â£514.56 |
| **Lost** | 829 | 19.11% | 1,286 | Â£656,259.65 | **7.38%** | 269.1d | 1.55 | Â£791.63 | Â£510.31 |
| **Total / Overall** | **4,338** | **100.0%** | **18,532** | **Â£8,887,208.89** | **100.0%** | **92.5d** | **4.27** | **Â£2,048.69** | **Â£479.56** |

---

## 12. Strategic Business Interpretations & Hypotheses

### 1. Retention is the Primary Value Driver
- **Finding:** *Champions* and *Loyal Customers* collectively constitute **29.94% of the customer base** but generate **71.31% of total gross revenue** (Â£6.34M).
- **Hypothesis for Testing:** Providing dedicated account management, exclusive volume pricing, and automated replenishment reminders will protect high-margin cash flow.

### 2. Second-Order Conversion Gap
- **Finding:** *Recent Customers* represent 527 accounts (12.15%) with healthy recent activity (mean recency 14.1 days) but only 1 purchase.
- **Hypothesis for Testing:** An automated post-purchase onboarding email series triggered within 7â€“14 days of delivery could accelerate second-purchase conversion.

### 3. Re-Engagement / Win-Back Opportunity
- **Finding:** *At Risk* accounts (203 customers, Â£401k past spend) previously averaged 4.41 orders but have been inactive for an average of 160 days.
- **Hypothesis for Testing:** Win-back campaigns offering targeted incentives on historically purchased categories may recover a fraction of lapsed high-frequency buyers (to be evaluated via randomized A/B trials).

---

## 13. Analytical Limitations & Governance Guardrails

To maintain rigorous data science integrity, the following boundaries must be observed:
1. **No Demographic Data:** The dataset contains no customer age, gender, household income, or corporate sector. Segmentation reflects purchasing behavior only.
2. **No Campaign History:** We observe no email open rates, ad spend, marketing channel attribution, or coupon usage.
3. **No True Churn Labels:** Non-subscription retail customers do not explicitly "cancel" accounts; absence of transactions reflects inactivity, not confirmed churn.
4. **Descriptive, Not Causal:** RFM categorizes what customers *did*, not *why* they did it. Proposed marketing strategies are hypotheses subject to empirical validation.

---

## 14. Relationship Between RFM and Later K-Means Clustering

While rule-based RFM scoring provides an intuitive heuristic scorecard, it possesses inherent geometric limitations:
- **Rigid Rectilinear Boundaries:** Rectangular score thresholds (e.g. $R \ge 4$ vs. $R = 3$) arbitrarily separate customers who differ by only a fraction of a day.
- **Equal Weighting Assumption:** Quantile binning assumes equal behavioral significance across all score steps regardless of scale.

### Transition to Phase 9:
In **Phase 9**, we will use the raw RFM features engineered here as inputs to **K-Means Clustering**:
1. Apply logarithmic transformation ($\log(x + 1)$) to compress monetary and frequency skewness.
2. Apply `StandardScaler` to normalize feature variance.
3. Optimize cluster counts ($k$) using Inertia Elbow analysis and Silhouette coefficients.
4. Compare unsupervised geometric clusters against the rule-based RFM scorecard to discover natural customer personas.
