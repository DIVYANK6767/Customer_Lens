# Data Cleaning Audit Report

## CustomerLens — Pipeline Execution Summary

---

### Executive Overview

The CustomerLens data cleaning pipeline was executed against the raw transactional source `data/raw/Online_Retail.csv`. The pipeline completed deterministically, removing exact duplicate logging records, categorizing transactions into explicit operational types, preserving unidentified guest checkouts in a store-wide dataset, and extracting valid customer purchases for RFM modeling.

---

### Before vs. After Quantitative Audit

| Metric | Raw Dataset (Before) | Clean Transactions (`clean_transactions.csv`) | Customer Analytics (`customer_transactions.csv`) | Notes & Business Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Total Rows** | **541,909** | **536,641** | **392,692** | 5,268 exact duplicates removed; 143,949 non-customer/non-sale rows segregated. |
| **Percentage Retained** | 100.00% | **99.03%** | **72.46%** | 72.46% of raw lines represent identified customer retail purchases. |
| **Exact Duplicate Rows** | 5,268 | **0** | **0** | Dropped identical line items across all 8 attributes. |
| **Missing CustomerID Rows** | 135,080 (24.93%) | **135,037** (25.16%) | **0** (0.00%) | Anonymous transactions preserved in clean set; excluded from RFM. |
| **Missing Description Rows** | 1,454 (0.27%) | **1,454** (0.27%) | **0** (0.00%) | All 1,454 belonged to adjustments/anonymous rows; 0 in customer purchases. |
| **Cancellation Rows (`'C'` prefix)** | 9,288 | **9,251** | **0** | Excluded from completed sales; preserved in clean set for return analysis. |
| **Adjustment Rows** | 1,338 | **1,339** | **0** | 3 bad-debt entries ('A') + 1,336 warehouse write-offs; excluded from sales. |
| **Zero UnitPrice Rows (`0.0`)** | 2,515 | **2,510** | **0** | 1,174 classified as Invalid, 1,336 as Adjustments; excluded from sales. |
| **Negative UnitPrice Rows (`< 0`)** | 2 | **2** | **0** | Both bad-debt adjustments (-11,062.06); excluded from sales. |
| **Negative Quantity Rows (`< 0`)** | 10,624 | **10,587** | **0** | 9,251 cancellations + 1,336 adjustments; excluded from sales. |
| **Zero Quantity Rows (`= 0`)** | 0 | **0** | **0** | None present in raw or cleaned data. |
| **Completed Sale Rows** | — | **524,877** | **392,692** | 524,877 sales store-wide; 392,692 have valid CustomerID. |
| **Non-Sale / Excluded Rows** | — | **11,764** | **143,949** | Cancellations (9,251) + Adjustments (1,339) + Invalid (1,174). |
| **Unique Identified Customers** | 4,372 | 4,372 | **4,338** | 34 customers had only cancellations or zero-price entries. |
| **Unique Invoices / Orders** | 25,900 | 25,900 | **18,532** | Distinct completed purchase orders placed by identified customers. |
| **Total Monetary Revenue** | — | — | **£8,887,208.89** | Net completed purchase expenditure across identified customers. |

---

### Key Cleaning Decisions & Logic

1. **Exact Duplicate Removal:**
   - 5,268 records were identical across all 8 fields.
   - Removed to prevent artificial inflation of frequency, units, and customer spend.
2. **Transaction Classification Engine:**
   - Evaluates each row deterministically into:
     - `Sale`: Completed retail merchandise purchase ($\text{Quantity} > 0, \text{UnitPrice} > 0$).
     - `Cancellation`: Customer returns prefixed with `'C'`.
     - `Adjustment`: Accounting entries (`'A'` prefix) or warehouse deductions ($\text{Quantity} < 0$ without `'C'`).
     - `Invalid`: $\text{Quantity} = 0$ or $\text{UnitPrice} \le 0$.
3. **Conservative Missing CustomerID Policy:**
   - 135,080 records lacked a Customer ID.
   - **No fake imputation was performed.** Anonymous rows are preserved in `clean_transactions.csv` for store-level sales reconciliation and excluded from `customer_transactions.csv` for RFM segmentation.
4. **Preservation of Missing Descriptions:**
   - Descriptions are not required for RFM; missing values were flagged with `DescriptionMissing = True` without deleting valid rows or inventing names.
5. **Vectorized Revenue Computation:**
   - Calculated strictly as $\text{Revenue} = \text{Quantity} \times \text{UnitPrice}$ and rounded to 2 decimal places.

---

### Output File Verification

- **Comprehensive Transactions:** `data/processed/clean_transactions.csv` (536,641 rows, 11 columns, 55.8 MB)
- **Customer Purchase Transactions:** `data/processed/customer_transactions.csv` (392,692 rows, 11 columns, 41.2 MB)
- **Machine-Readable Summary:** `data/processed/cleaning_report.csv` (1 row, 20 metric columns)
- **Raw File Checksum (SHA-256):** `A2F79BBDD4463DF6DB8A3F5A50B9C980AE8F645A370BF5E2C0D6097F9E817B05` (Unchanged)
