# Data Cleaning & Quality Pipeline Documentation

## CustomerLens — Customer Segmentation & Targeted Marketing Analytics

---

### 1. Why Data Cleaning Is Needed

In real-world retail environments, transaction logs are rarely pristine. Datasets capture messy operational realities:
- Customers cancel orders or return merchandise.
- Warehouse workers log inventory write-downs, damaged items, and audit adjustments directly into POS terminals.
- Shoppers complete guest checkouts without creating or logging into customer accounts.
- Network re-transmissions and POS double-clicks create identical duplicate records.
- Bad debt write-offs and complimentary gifts result in zero or negative unit prices.

If these operational anomalies are not identified, cleaned, and properly segregated before modeling:
1. **Gross Revenue Distortion:** Including cancellations and negative quantities in raw sales would distort basket sizes and understate or overstate transaction velocity.
2. **Customer Segmentation Failure:** K-Means clustering calculates Euclidean distances across Recency, Frequency, and Monetary (RFM) metrics. Assigning thousands of guest checkout transactions to a single fake customer or including bad debt write-offs would corrupt cluster centers.
3. **Misleading Marketing Recommendations:** Recommending a VIP retention campaign to an account whose order history consists entirely of returned merchandise would waste marketing resources.

The CustomerLens cleaning pipeline establishes a deterministic, reproducible, and conservative data-cleaning process that preserves raw data while producing clean, audit-ready analytical datasets.

---

### 2. Raw Data Observations

The raw dataset at `data/raw/Online_Retail.csv` contains **541,909 rows** and **8 columns**:
- **Date Range:** December 1, 2010 08:26:00 to December 9, 2011 12:50:00 (373 days).
- **Exact Duplicate Rows:** 5,268 rows are byte-for-byte identical duplicates.
- **Missing CustomerID:** 135,080 rows (24.93%) lack a customer identifier.
- **Missing Description:** 1,454 rows (0.27%) lack product descriptions.
- **Negative Quantities:** 10,624 rows have `Quantity < 0`:
  - 9,288 are customer cancellations prefixed with `'C'` in `InvoiceNo`.
  - 1,336 are unprefixed inventory write-offs (`damaged`, `check`, `thrown away`), all lacking CustomerID.
- **Zero Quantities:** 0 rows (every record has non-zero quantity).
- **Zero UnitPrices:** 2,515 rows have `UnitPrice == 0.0` (2,475 lack CustomerID).
- **Negative UnitPrices:** Exactly 2 rows have `UnitPrice == -11062.06` (`A563186` and `A563187`, bad debt accounting entries).
- **Geographic Distribution:** 38 unique countries, with the United Kingdom accounting for 495,478 rows (91.43%).

---

### 3. Duplicate Handling

- **Observed:** 5,268 exact duplicate rows across all 8 fields.
- **Root Cause:** Double-clicks during checkout, network retry requests, or batch ingestion duplicate logs.
- **Rule Applied:** Exact duplicates are removed using `df.drop_duplicates(keep='first')`.
- **Rationale:** Keeping identical line-item copies of the exact same transaction would artificially inflate order frequency, product unit counts, and customer monetary spend. Non-identical rows sharing an `InvoiceNo` are preserved because an invoice contains multiple distinct catalog items.
- **Preservation:** The raw CSV remains untouched; deduplication occurs in memory during pipeline execution.

---

### 4. Cancellation & Return Handling

- **Observed:** 9,288 rows have `InvoiceNo` beginning with `'C'` (or `'c'`), representing 3,836 distinct cancellation invoices.
- **Classification:** Tagged with `TransactionType = 'Cancellation'`.
- **Rule Applied:**
  - Cancellations are **excluded from the primary completed-purchase customer analytics dataset** (`customer_transactions.csv`) so that order frequency ($F$) represents genuine completed purchases.
  - Cancellations are **retained in the comprehensive transaction dataset** (`clean_transactions.csv`) with the `'Cancellation'` tag, enabling future returns and refund analysis.
  - Negative quantities on cancellation rows are **never silently converted to positive numbers**.

---

### 5. Adjustment Handling

- **Observed:**
  - 3 rows with `InvoiceNo` starting with `'A'` (`A563185`, `A563186`, `A563187`), stock code `'B'`, description `'Adjust bad debt'`, and null CustomerID.
  - 1,336 rows with `Quantity < 0` that have **no `'C'` prefix**. 100% of these rows have null `CustomerID` and carry operational inventory notes (`check`, `damaged`, `thrown away`, `sold as set on dotcom`).
- **Classification:** Tagged with `TransactionType = 'Adjustment'`.
- **Rule Applied:**
  - Adjustments are excluded from completed customer sales.
  - They are preserved in `clean_transactions.csv` to allow auditing of inventory loss and bookkeeping entries.
  - They are excluded from customer-level RFM modeling because they do not represent retail customer purchase behavior.

---

### 6. Price & Quantity Validation

- **Observed:**
  - 2,515 rows with `UnitPrice == 0.0`.
  - 2 rows with `UnitPrice < 0.0` (`-11062.06`).
  - 0 rows with `Quantity == 0`.
- **Classification:** Rows where `Quantity == 0` or `UnitPrice <= 0` (that were not already classified as Cancellation or Adjustment) are tagged with `TransactionType = 'Invalid'`. (In the deduplicated dataset, exactly 1,174 rows with `Quantity > 0` and `UnitPrice == 0.0` receive the `'Invalid'` tag).
- **Rule Applied:**
  - Standard completed retail sales must satisfy $\text{Quantity} > 0$ and $\text{UnitPrice} > 0$.
  - Prices are **never replaced with arbitrary or imputed numbers**.
  - All non-positive price rows are excluded from customer revenue calculations.

---

### 7. Missing CustomerID Strategy

- **Observed:** 135,080 rows (24.93%) lack a `CustomerID`.
- **Root Cause:** Anonymous guest checkouts where customers completed transactions without registering an account.
- **Rule Applied:**
  - **No Fake Imputation:** Missing CustomerIDs are **NEVER filled** with `0`, `-1`, `"Unknown"`, forward-fill, or random IDs. Doing so would combine thousands of unrelated individuals into a massive pseudo-customer that would dominate clustering.
  - **Comprehensive Dataset (`clean_transactions.csv`):** Preserves anonymous transactions with `CustomerID = None`, allowing store-level aggregate revenue reporting.
  - **Customer Analytics Dataset (`customer_transactions.csv`):** Excludes rows with null `CustomerID` because individual repeat behavior cannot be tracked without a persistent entity identifier.
  - **Reporting:** Total revenue generated by unidentified customers is tracked and reported transparently.

---

### 8. Missing Description Strategy

- **Observed:** 1,454 rows (0.27%) lack product descriptions.
- **Rule Applied:**
  - Descriptions are **not required** for customer-level RFM modeling (which relies solely on transaction dates, invoice IDs, and monetary spend).
  - Missing descriptions are **not fabricated or filled with arbitrary strings**.
  - An explicit boolean indicator, `DescriptionMissing = True`, is added.
  - In the primary customer analytics dataset (`customer_transactions.csv`), exactly **0 rows have missing descriptions** (all 1,454 missing descriptions belonged to inventory adjustments or anonymous transactions).

---

### 9. Revenue Calculation

- **Formula:**
  $$\text{Revenue} = \text{Quantity} \times \text{UnitPrice}$$
- **Rule Applied:**
  - Calculated using vectorized arithmetic and rounded to 2 decimal places.
  - Calculated on all rows in `clean_transactions.csv`.
  - For `customer_transactions.csv`, revenue is guaranteed to be strictly positive ($\text{Quantity} > 0$, $\text{UnitPrice} > 0$, $\text{TransactionType} = \text{'Sale'}$).
- **Verified Metrics:**
  - Total Revenue across valid customer purchases: **£8,887,208.89**.

---

### 10. Final Output Datasets

The cleaning pipeline generates two separate, purpose-built datasets stored in `data/processed/` (both excluded from Git via `.gitignore`):

| Dataset File | Row Count | Granularity & Contents | Primary Analytical Purpose |
| :--- | :--- | :--- | :--- |
| **`clean_transactions.csv`** | **536,641** | All deduplicated, normalized, and classified transactions (including Sales, Cancellations, Adjustments, and Guest Checkouts). | Store-wide operational auditing, refund analysis, inventory write-off analysis, and total store revenue reconciliation. |
| **`customer_transactions.csv`** | **392,692** | Only valid completed purchases ($\text{TransactionType} = \text{'Sale'}$, $\text{Quantity} > 0$, $\text{UnitPrice} > 0$, non-null $\text{CustomerID}$). | PostgreSQL database loading, SQL analytics, RFM feature engineering, and K-Means customer segmentation. |
| **`cleaning_report.csv`** | **1** | Machine-readable single-row audit log of all before/after cleaning metrics. | Automated pipeline verification and CI testing. |

#### Schema of Processed Datasets:
1. `InvoiceNo` (`str`): 6-digit invoice identifier (or C/A prefixed code).
2. `StockCode` (`str`): Normalized product code.
3. `Description` (`str`): Normalized uppercase product title.
4. `Quantity` (`int`): Item quantity.
5. `InvoiceDate` (`datetime64[ns]`): Parsed timestamp.
6. `UnitPrice` (`float`): Unit price in GBP.
7. `CustomerID` (`str` / nullable): Clean 5-digit customer ID string without trailing decimals.
8. `Country` (`str`): Customer billing country.
9. `TransactionType` (`str`): `'Sale'`, `'Cancellation'`, `'Adjustment'`, or `'Invalid'`.
10. `DescriptionMissing` (`bool`): Flag indicating whether description was missing.
11. `Revenue` (`float`): $\text{Quantity} \times \text{UnitPrice}$ rounded to 2 decimals.

---

### 11. Known Limitations

1. **Non-Identified Guest Checkouts:** Approximately 24.93% of transaction rows cannot be tied to specific customer profiles, meaning customer segmentation reflects the identified customer base (~72.46% of records; 392,692 purchase rows across 4,338 active purchasing customers).
2. **Unmatched Returns:** Some cancellation invoices occur without a matching historical purchase in the dataset (due to returns occurring for purchases made prior to December 2010).
3. **Bulk Outliers:** A small number of extreme wholesale purchases (e.g., 80,995 units) exist in completed customer sales; these will require logarithmic transformation before distance-based clustering in Phase 7.
