-- =============================================================================
-- CustomerLens: PostgreSQL Analytical Data Validation Script
-- Phase 7.1 — PostgreSQL Analytical Layer Foundation
-- =============================================================================
-- Purpose: Validate data integrity, schema consistency, and mathematical
-- invariants of analytics.customer_transactions after loading from the
-- validated dataset (data/processed/customer_transactions.csv).
--
-- Expected Baselines:
--   Total Rows:              392,692
--   Active Customers:        4,338
--   Completed Orders:        18,532
--   Total Gross Revenue:     £8,887,208.89
--   TransactionType:         100% 'Sale'
--   Missing CustomerID:      0
--   Non-Positive Quantity:   0
--   Non-Positive UnitPrice:  0
--   Unique Countries:        37
--   Date Range:              2010-12-01 08:26:00 to 2011-12-09 12:50:00
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Total Row Count Validation
-- Expected: 392,692 rows
-- -----------------------------------------------------------------------------
SELECT 
    '1. Row Count' AS check_name,
    COUNT(*) AS actual_value,
    392692 AS expected_value,
    CASE WHEN COUNT(*) = 392692 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM analytics.customer_transactions;

-- -----------------------------------------------------------------------------
-- 2. Column Availability & Schema Types
-- Expected: 11 columns in analytics.customer_transactions
-- -----------------------------------------------------------------------------
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'analytics' 
  AND table_name = 'customer_transactions'
ORDER BY ordinal_position;

-- -----------------------------------------------------------------------------
-- 3. Missing or Blank CustomerID Check
-- Expected: 0 rows with NULL or empty CustomerID
-- -----------------------------------------------------------------------------
SELECT 
    '3. Missing CustomerID' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM analytics.customer_transactions
WHERE CustomerID IS NULL OR TRIM(CustomerID) = '';

-- -----------------------------------------------------------------------------
-- 4. NULL or Negative Revenue Check
-- Expected: 0 rows with NULL or Revenue < 0
-- -----------------------------------------------------------------------------
SELECT 
    '4. NULL or Negative Revenue' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM analytics.customer_transactions
WHERE Revenue IS NULL OR Revenue < 0;

-- -----------------------------------------------------------------------------
-- 5. Non-Positive Quantity Check
-- Expected: 0 rows with Quantity <= 0
-- -----------------------------------------------------------------------------
SELECT 
    '5. Non-Positive Quantity' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM analytics.customer_transactions
WHERE Quantity <= 0;

-- -----------------------------------------------------------------------------
-- 6. Non-Positive UnitPrice Check
-- Expected: 0 rows with UnitPrice <= 0
-- -----------------------------------------------------------------------------
SELECT 
    '6. Non-Positive UnitPrice' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM analytics.customer_transactions
WHERE UnitPrice <= 0;

-- -----------------------------------------------------------------------------
-- 7. TransactionType Distribution Check
-- Expected: 392,692 'Sale' transactions (100%), 0 other
-- -----------------------------------------------------------------------------
SELECT 
    TransactionType,
    COUNT(*) AS row_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_share
FROM analytics.customer_transactions
GROUP BY TransactionType;

-- -----------------------------------------------------------------------------
-- 8. Distinct Customer Count
-- Expected: 4,338 unique active purchasing customers
-- -----------------------------------------------------------------------------
SELECT 
    '8. Distinct Customers' AS check_name,
    COUNT(DISTINCT CustomerID) AS actual_value,
    4338 AS expected_value,
    CASE WHEN COUNT(DISTINCT CustomerID) = 4338 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM analytics.customer_transactions;

-- -----------------------------------------------------------------------------
-- 9. Distinct Completed Invoices (Orders)
-- Expected: 18,532 unique purchase orders
-- -----------------------------------------------------------------------------
SELECT 
    '9. Distinct Orders' AS check_name,
    COUNT(DISTINCT InvoiceNo) AS actual_value,
    18532 AS expected_value,
    CASE WHEN COUNT(DISTINCT InvoiceNo) = 18532 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM analytics.customer_transactions;

-- -----------------------------------------------------------------------------
-- 10. Revenue Reconciliation Check
-- Expected: Total Revenue = £8,887,208.89
-- Formula: Difference between stored Revenue and computed (Quantity * UnitPrice)
-- -----------------------------------------------------------------------------
SELECT 
    '10. Revenue Reconciliation' AS check_name,
    ROUND(SUM(Revenue), 2) AS total_stored_revenue,
    8887208.89 AS expected_revenue,
    ROUND(SUM(Revenue) - 8887208.89, 2) AS difference,
    MAX(ABS(Revenue - ROUND(Quantity * UnitPrice, 2))) AS max_line_discrepancy,
    CASE 
        WHEN ROUND(SUM(Revenue), 2) = 8887208.89 THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS status
FROM analytics.customer_transactions;

-- -----------------------------------------------------------------------------
-- 11. Invoice Date Range Check
-- Expected: Earliest 2010-12-01 08:26:00, Latest 2011-12-09 12:50:00
-- -----------------------------------------------------------------------------
SELECT 
    '11. Date Range' AS check_name,
    MIN(InvoiceDate) AS earliest_date,
    MAX(InvoiceDate) AS latest_date,
    CASE 
        WHEN MIN(InvoiceDate) = '2010-12-01 08:26:00' 
         AND MAX(InvoiceDate) = '2011-12-09 12:50:00' 
        THEN 'PASSED' 
        ELSE 'FAILED' 
    END AS status
FROM analytics.customer_transactions;

-- -----------------------------------------------------------------------------
-- 12. Distinct Country Count Check
-- Expected: 37 unique countries in customer transactions
-- -----------------------------------------------------------------------------
SELECT 
    '12. Country Count' AS check_name,
    COUNT(DISTINCT Country) AS actual_value,
    37 AS expected_value,
    CASE WHEN COUNT(DISTINCT Country) = 37 THEN 'PASSED' ELSE 'FAILED' END AS status
FROM analytics.customer_transactions;

-- -----------------------------------------------------------------------------
-- 13. Comprehensive Validation Scorecard Summary
-- Single executive dashboard row summarizing all invariants
-- -----------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_rows,
    COUNT(DISTINCT CustomerID) AS active_customers,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    COUNT(DISTINCT StockCode) AS unique_products,
    COUNT(DISTINCT Country) AS total_countries,
    ROUND(SUM(Revenue), 2) AS total_revenue_gbp,
    ROUND(SUM(Revenue) / COUNT(DISTINCT InvoiceNo), 2) AS average_order_value_gbp,
    SUM(CASE WHEN CustomerID IS NULL OR TRIM(CustomerID) = '' THEN 1 ELSE 0 END) AS missing_customer_ids,
    SUM(CASE WHEN Quantity <= 0 THEN 1 ELSE 0 END) AS invalid_quantities,
    SUM(CASE WHEN UnitPrice <= 0 THEN 1 ELSE 0 END) AS invalid_prices,
    SUM(CASE WHEN TransactionType != 'Sale' THEN 1 ELSE 0 END) AS non_sale_rows,
    CASE 
        WHEN COUNT(*) = 392692
         AND COUNT(DISTINCT CustomerID) = 4338
         AND COUNT(DISTINCT InvoiceNo) = 18532
         AND COUNT(DISTINCT Country) = 37
         AND ROUND(SUM(Revenue), 2) = 8887208.89
         AND SUM(CASE WHEN CustomerID IS NULL THEN 1 ELSE 0 END) = 0
         AND SUM(CASE WHEN Quantity <= 0 THEN 1 ELSE 0 END) = 0
         AND SUM(CASE WHEN UnitPrice <= 0 THEN 1 ELSE 0 END) = 0
        THEN 'ALL INVARIANTS SATISFIED (PASSED)'
        ELSE 'VALIDATION ISSUES DETECTED (FAILED)'
    END AS overall_status
FROM analytics.customer_transactions;
