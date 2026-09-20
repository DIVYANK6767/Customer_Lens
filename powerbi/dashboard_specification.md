# Power BI Dashboard Specification — CustomerLens

This document provides the formal visual layout, field bindings, formatting rules, slicer interactions, and business takeaway text for building the 4-page CustomerLens Power BI report.

---

## Global Design Standards & Formatting Palette

- **Canvas Size:** 16:9 widescreen ($1920 \times 1080$ px or standard $1280 \times 720$ px).
- **Color Palette:**
  - Primary Corporate Blue: `#1F77B4`
  - High-Value Engaged (*Protect & Grow*): `#2CA02C` (Forest Green)
  - Established Valuable (*Nurture*): `#1F77B4` (Royal Blue)
  - Recent Developing (*Develop*): `#FF7F0E` (Vibrant Orange)
  - Low-Engagement / Reactivation (*Reactivate*): `#D62728` (Muted Crimson)
  - Neutral Background: `#F8F9FA`
  - Card Fill: `#FFFFFF` with `#E9ECEF` 1px border.
  - Text Primary: `#212529`
  - Text Secondary / Captions: `#6C757D`
- **Typography:** Segoe UI or DIN (Modern Clean Sans-Serif).
- **Navigation:** Persistent left-hand page navigation pane or clean native page tab bar.

---

## Page 1 — Executive Overview

### 1. Objective & Target Audience
Provides C-suite and commercial leadership with high-level commercial performance, order volume velocity, geographic revenue concentration, and buyer retention dynamics.

### 2. Top-Level KPI Summary Cards (Grid: $1 \times 5$, Top Ribbon)

| Card # | Metric Name | Bound DAX Measure | Target Format | Baseline Value | Subtext / Micro-Label |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **C1** | **Total Revenue** | `[Total Revenue]` | `£#,##0.00` | **£8,887,208.89** | Validated Completed Sales |
| **C2** | **Active Customers** | `[Total Customers]` | `#,##0` | **4,338** | Distinct Verified Accounts |
| **C3** | **Total Orders** | `[Total Orders]` | `#,##0` | **18,532** | Completed Invoices |
| **C4** | **Average Order Value** | `[Average Order Value]` | `£#,##0.00` | **£479.56** | Revenue / Order |
| **C5** | **Repeat Customer Rate** | `[Repeat Customer Rate]` | `0.0%` | **65.6%** | 2,845 / 4,338 Customers |

---

### 3. Visual Components & Field Mappings

#### Visual 1.1: Monthly Revenue Velocity & Order Volume
- **Visual Type:** Line and Clustered Column Chart.
- **X-Axis:** `customer_transactions[InvoiceDate]` (Aggregated to `Year-Month`).
- **Column Y-Axis:** `[Total Revenue]`.
- **Line Y-Axis:** `[Total Orders]`.
- **Title:** *Monthly Revenue Trend (£) and Completed Orders (Dec 2010 – Dec 2011)*.
- **Data Labels:** Enabled on peak columns.
- **Visual Callout / Annotation:** Callout on **November 2011** (£1,156,205.61, 2,657 orders), noting peak seasonal holiday buying volume. Annotation on **December 2011** noting truncation on 9 December 2011.

#### Visual 1.2: Geographic Revenue Distribution (Top 10 Markets)
- **Visual Type:** Horizontal Stacked Bar Chart.
- **Y-Axis:** `customer_transactions[Country]` (Filtered to Top 10 by Revenue).
- **X-Axis:** `[Total Revenue]`.
- **Data Labels:** Value (`£M`) and % of Total.
- **Title:** *Top 10 Geographic Markets by Revenue*.
- **Key Insight Callout:** United Kingdom accounts for **88.80%** (£7,308,391.55) of enterprise turnover; Netherlands, EIRE, Germany, and France represent the core international footprint.

#### Visual 1.3: Customer Account Distribution by Country
- **Visual Type:** Treemap or Horizontal Bar Chart.
- **Category:** `business_segments[country]`.
- **Values:** `[Total Customers]`.
- **Title:** *Active Customer Accounts by Geographic Origin*.

#### Visual 1.4: Repeat vs. One-Time Customer Analysis (Pareto Analysis)
- **Visual Type:** 100% Stacked Bar Chart or Dual Donut Charts.
- **Dimensions / Legend:** `Customer Type` (`Repeat Buyer (2+ Orders)` vs. `One-Time Buyer (1 Order)`).
- **Chart A (Volume):** `[Repeat Customers]` (2,845; 65.6%) vs. `[One-Time Customers]` (1,493; 34.4%).
- **Chart B (Revenue):** Repeat Revenue (£8,273,219.33; **93.09%**) vs. One-Time Revenue (£613,989.56; **6.91%**).
- **Title:** *Customer Retention Disparity: Customer Volume vs. Revenue Contribution*.

#### Visual 1.5: Revenue Concentration Multiplier
- **Visual Type:** Gauge or Card Callout.
- **Metric:** 65.6% of customers generate 93.1% of revenue (1.42x concentration ratio for repeat buyers overall).

---

### 4. Interactive Slicers
- **Slicer 1 (Date Range):** `customer_transactions[InvoiceDate]` (Relative Date or Slider between `2010-12-01` and `2011-12-09`).
- **Slicer 2 (Country):** `customer_transactions[Country]` (Dropdown, Multi-select, Default = All).

---

### 5. Executive Takeaway Box (Bottom Ribbon / Side Panel)
> **Executive Summary & Evidence-Based Insights:**
> 1. **Extreme Revenue Concentration:** Repeat customers represent 65.6% of the account base but generate **93.1%** of enterprise turnover (£8.27M). Commercial longevity depends heavily on retention and second-order activation rather than single-purchase acquisition.
> 2. **Domestic Core with European Footholds:** The UK represents £7,308,391.55 (88.80%) of turnover, while 4 Western European markets (Netherlands, EIRE, Germany, France) account for an additional £988K (11.1%).
> 3. **Seasonal Peak:** November 2011 represents the annual turnover peak (£1.16M across 2,657 orders). December 2011 reflects partial-month data ending 9 December 2011.

---

## Page 2 — Customer Segmentation

### 1. Objective & Target Audience
Presents the 4 unsupervised K-Means customer personas, their relative financial and volumetric weights, behavioral profile benchmarks, and model selection diagnostics.

---

### 2. Segment Summary Table & Scorecard
- **Visual Type:** Matrix / Table.
- **Rows:** `segment_summary[business_segment]`.
- **Columns / Values:**
  - `action_category` (*Action Strategy*)
  - `customer_count` (*Customer Count*)
  - `customer_percentage` (*Customer Share %*)
  - `total_revenue` (*Total Revenue £*)
  - `revenue_percentage` (*Revenue Share %*)
  - `[Revenue Concentration Multiplier]` (*M% / C%*)
  - `median_recency` (*Median Recency d*)
  - `median_frequency` (*Median Frequency*)
  - `median_monetary` (*Median Spend £*)

#### Validated Scorecard Benchmark Data:
| Business Segment | Action Category | Customers | % Base | Revenue (£) | % Rev | Concentration | Median R | Median F | Median M |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **High-Value Engaged** | **Protect & Grow** | 716 | 16.51% | £5,781,509.02 | 65.05% | **3.94x** | 8.0 d | 10.0 | £3,730.61 |
| **Established Valuable** | **Nurture** | 1,170 | 26.97% | £2,092,321.70 | 23.54% | **0.87x** | 57.0 d | 4.0 | £1,340.08 |
| **Recent Developing** | **Develop** | 834 | 19.23% | £465,608.17 | 5.24% | **0.27x** | 17.0 d | 2.0 | £481.03 |
| **Low-Engagement / Reactivation** | **Reactivate** | 1,618 | 37.30% | £547,770.00 | 6.16% | **0.17x** | 174.5 d | 1.0 | £293.78 |

---

### 3. Visual Components & Field Mappings

#### Visual 2.1: Customer Share vs. Revenue Share Disparity
- **Visual Type:** Clustered Column Chart.
- **X-Axis:** `segment_summary[business_segment]`.
- **Y-Axis Series 1:** `segment_summary[customer_percentage]` (Customer Share %).
- **Y-Axis Series 2:** `segment_summary[revenue_percentage]` (Revenue Share %).
- **Title:** *Segment Disparity: Customer Volume % vs. Revenue Contribution %*.
- **Color Coding:** Customer Share in Slate Grey (`#6C757D`); Revenue Share in Royal Blue (`#1F77B4`).

#### Visual 2.2: Revenue Concentration Multiplier Index
- **Visual Type:** Horizontal Bar Chart.
- **Y-Axis:** `segment_summary[business_segment]`.
- **X-Axis:** `[Revenue Concentration Multiplier]`.
- **Reference Line:** Constant line at `X = 1.0` (Equitable baseline).
- **Title:** *Revenue Density Index (% Revenue / % Customer Volume)*.
- **Highlight:** High-Value Engaged at **3.94x**; Low-Engagement at **0.17x**.

#### Visual 2.3: Behavioral Separation Across Personas (3 Small Multiples or Grouped Bars)
- **Visual Type:** Clustered Bar Chart.
- **Y-Axis:** `segment_summary[business_segment]`.
- **Chart A (Recency):** `segment_summary[median_recency]` (Days, lower is more recent).
- **Chart B (Frequency):** `segment_summary[median_frequency]` (Orders completed).
- **Chart C (Monetary):** `segment_summary[median_monetary]` (Spend in £).
- **Title:** *Behavioral Differentiation Across Personas (Median RFM Dimensions)*.

#### Visual 2.4: K-Means Model Selection & Diagnostic Visual ($K=2..10$)
- **Visual Type:** Line Chart with dual Y-axes (or side-by-side lines).
- **X-Axis:** `clustering_metrics[k]` (Values 2 through 10).
- **Left Y-Axis:** `clustering_metrics[silhouette_score]` (Blue line, points marked).
- **Right Y-Axis:** `clustering_metrics[inertia]` (Grey dashed line, WCSS Elbow).
- **Title:** *K-Means Validation Diagnostics: Silhouette Score & Inertia across K=2..10*.
- **Model Selection Callout:**
  > **Model Selection Rationale ($K=4$):**
  > Candidate cluster sizes were evaluated across $K \in [2, 10]$. While $K=2$ achieved a higher silhouette score (0.4328), it produced a simplistic dichotomy merging dormant wholesale accounts with single-purchase retail buyers. **$K=4$ was selected as a business-oriented segmentation solution** because it achieved a local silhouette inflection (**0.3374**), stable cluster sizes (716 to 1,618 accounts), and distinct commercial lifecycle actionability. $K=4$ is not described as mathematically optimal, but as an explainable, operationally viable segmentation structure.

---

### 4. Interactive Slicers & Filters
- **Slicer 1:** `segment_summary[business_segment]` (Buttons / Tile slicer).
- **Slicer 2:** `business_segments[country]` (Dropdown).

---

## Page 3 — RFM Analysis

### 1. Objective & Target Audience
Explains the underlying continuous Recency, Frequency, and Monetary distributions that form the mathematical inputs to customer segmentation, educating analysts and marketing operators on behavioral distributions.

---

### 2. Educational Metric Definition Cards (Top Banner)

| Dimension | Plain-Language Definition | Dataset Median | 75th Percentile (P75) | Skewness Note |
| :--- | :--- | :---: | :---: | :--- |
| **Recency (R)** | Days elapsed between customer's last order and reference anchor (2011-12-10). | **51.0 days** | 143.0 days | Positive right skew; 50% purchased within 51 days. |
| **Frequency (F)** | Total count of distinct completed orders (`InvoiceNo`) per customer. | **2.0 orders** | 5.0 orders | Heavy right skew; 34.4% have $F=1$; max $F=210$. |
| **Monetary (M)**| Total cumulative gross spend (£) per customer. | **£668.57** | £1,664.71 | Extreme positive right skew; mean spend is £2,048.69. |

---

### 3. Visual Components & Field Mappings

#### Visual 3.1: Recency Distribution
- **Visual Type:** Column Chart / Histogram (Bin width = 30 days).
- **X-Axis:** `business_segments[recency]` (Binned: 0-30, 31-60, 61-90, 91-180, 181-365 days).
- **Y-Axis:** `[Total Customers]`.
- **Title:** *Recency Distribution: Customer Account Volume by Days Inactive*.

#### Visual 3.2: Frequency Distribution (Log/Exponential Presentation)
- **Visual Type:** Column Chart.
- **X-Axis:** `business_segments[frequency]` (Binned: 1, 2, 3-5, 6-10, 11-20, 20+ orders).
- **Y-Axis:** `[Total Customers]`.
- **Title:** *Order Frequency Distribution: Customer Volume by Lifetime Completed Invoices*.

#### Visual 3.3: Monetary Spend Distribution
- **Visual Type:** Column Chart.
- **X-Axis:** `business_segments[monetary]` (Binned: <£250, £250-£500, £500-£1K, £1K-£2.5K, £2.5K-£5K, >£5K).
- **Y-Axis:** `[Total Customers]`.
- **Title:** *Gross Monetary Spend Distribution*.

#### Visual 3.4: Customer RFM Quintile Score Distribution
- **Visual Type:** 100% Stacked Bar Chart.
- **Y-Axis:** Quintile Rank (1 through 5).
- **Values:** Customer count across `R_score`, `F_score`, and `M_score`.
- **Title:** *Distribution of Standardized RFM Quintile Scores (1 = Lowest, 5 = Highest)*.

#### Visual 3.5: Recency vs. Monetary Spend Relationship
- **Visual Type:** Scatter Plot.
- **X-Axis:** `business_segments[recency]`.
- **Y-Axis:** `business_segments[monetary]` (Logarithmic scale recommended in Power BI axis settings).
- **Legend:** `business_segments[business_segment]`.
- **Size:** `business_segments[frequency]`.
- **Tooltip:** `customerid`, `business_segment`, `recency`, `frequency`, `monetary`.
- **Title:** *Customer Account Scatter: Recency vs. Monetary Value (Colored by Persona)*.

---

### 4. Non-Predictive Boundary Note (Callout Card)
> **Scientific Integrity & Scope Boundary:**
> RFM analysis captures **observed historical transaction behavior**. It reflects historical purchase timing, frequency, and spend. It does not measure customer sentiment, NPS, or external market conditions. RFM scores and segments must not be interpreted as deterministic churn probabilities or guaranteed future spend predictions.

---

## Page 4 — Marketing Opportunities

### 1. Objective & Target Audience
Translates the 4 validated business segments into commercial action strategies, proposed success KPIs, and a structured A/B testing experimentation matrix.

---

### 2. Strategy Cards (Grid: $2 \times 2$)

#### Card 4.1: Protect & Grow (*High-Value Engaged*)
- **Target Cohort:** 716 accounts (16.51% of base, £5.78M revenue, 65.05% share).
- **Behavioral Profile:** Median Recency: 8.0 d, Frequency: 10.0, Spend: £3,730.61.
- **Recommended Action:** Dedicated B2B account manager support, priority dispatch SLAs, scheduled replenishment cadence, and executive relationship touchpoints.
- **Suggested KPI:** 90-day account retention rate, gross margin per account, and order schedule consistency.
- **Risk Caveat:** Severe revenue concentration risk. Avoid margin erosion through unwarranted price discounts; focus on service SLAs.

#### Card 4.2: Nurture (*Established Valuable*)
- **Target Cohort:** 1,170 accounts (26.97% of base, £2.09M revenue, 23.54% share).
- **Behavioral Profile:** Median Recency: 57.0 d, Frequency: 4.0, Spend: £1,340.08.
- **Recommended Action:** Minimum order threshold incentives (£500+ free shipping/volume discount), category cross-selling, and seasonal catalog previews.
- **Suggested KPI:** Quarterly re-order velocity, Average Order Value (AOV), and category adoption rate.
- **Risk Caveat:** Ensure volume discounts do not subsidize baseline replenishment orders that would have occurred organically.

#### Card 4.3: Develop (*Recent Developing*)
- **Target Cohort:** 834 accounts (19.23% of base, £465.6K revenue, 5.24% share).
- **Behavioral Profile:** Median Recency: 17.0 d, Frequency: 2.0, Spend: £481.03.
- **Recommended Action:** Structured 30-day automated post-purchase onboarding sequence (Day 7 satisfaction check, Day 14 category guide, Day 21 restock trigger).
- **Suggested KPI:** 60-day second-purchase conversion rate, time-to-second-order, and early customer lifetime value.
- **Risk Caveat:** Avoid communication fatigue; prioritize relevant product use cases over high-frequency sales messaging.

#### Card 4.4: Reactivate (*Low-Engagement / Reactivation*)
- **Target Cohort:** 1,618 accounts (37.30% of base, £547.8K revenue, 6.16% share).
- **Behavioral Profile:** Median Recency: 174.5 d, Frequency: 1.0, Spend: £293.78.
- **Recommended Action:** Low-cost automated email win-back sequences with clearance offers, product discovery roundups, and list preference opt-downs.
- **Suggested KPI:** Reactivation conversion rate, net contribution margin per reactivated account, and list unsubscribe rate.
- **Risk Caveat:** 78.4% of this cohort completed only 1 order. Costly outbound paid media or direct mail carries negative expected ROI.

---

### 3. Structured A/B Testing Experimentation Framework (Matrix Table)

| Target Segment | Action Category | Treatment Strategy (Test Group) | Control Group Baseline | Primary Success KPI | Guardrail Metric |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **High-Value Engaged** | **Protect & Grow** | Dedicated B2B specialist & automated re-order reminders | Standard self-serve ordering portal | 90-Day Account Retention Rate | Gross Margin % per Account (protect margins) |
| **Established Valuable** | **Nurture** | £500+ tiered order threshold incentives & category cross-sell | Standard promotional calendar | Quarterly Order Velocity & AOV | Gross Margin after promotional discounts |
| **Recent Developing** | **Develop** | 30-day multi-touch onboarding sequence | Single generic transactional confirmation | 60-Day Repeat Conversion Rate | Email Opt-Out & Unsubscribe Rate |
| **Low-Engagement** | **Reactivate** | Automated win-back clearance email sequence | Uncontacted holdout control (zero outreach) | Net Reactivated Contribution (£) | Campaign Cost per Reactivated Account |

---

### 4. Hypothesis & Experimentation Guardrail Callout
> **Scientific Integrity & Marketing Attribution Policy:**
> The strategies above represent **evidence-based empirical hypotheses**, not guaranteed campaign outcomes. Because the underlying dataset contains historical transactions without experimental marketing touchpoints, all marketing interventions must be evaluated via **Randomized Controlled Trials (RCT)** against an uncontacted holdout baseline before enterprise-wide budget allocation.
