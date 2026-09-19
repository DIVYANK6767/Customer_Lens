-- =============================================================================
-- CustomerLens: Foundational SQL Exploration
-- Phase 7.2 — PostgreSQL Analytical Layer
-- =============================================================================
-- Database: customer_lens
-- Schema:   analytics
-- Table:    analytics.customer_transactions
-- Purpose:  Foundational data exploration queries establishing baseline
--           metrics across transactions, customers, orders, products,
--           geography, and temporal boundaries.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Total Transaction Rows
-- Business Purpose: Verify the complete volume of individual purchase line items.
-- -----------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_transaction_rows
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 2. Total Active Identified Customers
-- Business Purpose: Quantify the unique customer accounts with purchasing history.
-- -----------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT customerid) AS total_active_customers
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 3. Total Completed Orders
-- Business Purpose: Count unique completed checkout transactions (invoices).
-- -----------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT invoiceno) AS total_completed_orders
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 4. Total Gross Revenue
-- Business Purpose: Establish the aggregate top-line revenue generated.
-- -----------------------------------------------------------------------------
SELECT 
    ROUND(SUM(revenue), 2) AS total_revenue_gbp
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 5. Total Physical Merchandise Units Sold
-- Business Purpose: Measure physical volume of goods transacted.
-- -----------------------------------------------------------------------------
SELECT 
    SUM(quantity) AS total_units_sold
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 6. Unique Products (Catalog Breadth)
-- Business Purpose: Determine the active product catalog variety sold.
-- -----------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT stockcode) AS unique_products_sold
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 7. Unique Destination Countries
-- Business Purpose: Quantify geographic market presence across billing countries.
-- -----------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT country) AS unique_countries
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 8. Earliest Transaction Timestamp (Dataset Start)
-- Business Purpose: Identify historical starting boundary of transaction data.
-- -----------------------------------------------------------------------------
SELECT 
    MIN(invoicedate) AS earliest_transaction_date
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 9. Latest Transaction Timestamp (Dataset End / Snapshot Anchor)
-- Business Purpose: Identify the latest recorded sale, anchoring the reference date.
-- -----------------------------------------------------------------------------
SELECT 
    MAX(invoicedate) AS latest_transaction_date
FROM analytics.customer_transactions;


-- -----------------------------------------------------------------------------
-- 10. Foundational Customer-Level Summary
-- Business Purpose: Inspect customer-level distributions (orders, spend, units).
-- -----------------------------------------------------------------------------
SELECT 
    customerid,
    COUNT(DISTINCT invoiceno) AS total_orders,
    SUM(quantity) AS total_units,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value,
    MIN(invoicedate) AS first_order_date,
    MAX(invoicedate) AS last_order_date
FROM analytics.customer_transactions
GROUP BY customerid
ORDER BY total_revenue DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- 11. Foundational Country-Level Summary
-- Business Purpose: Inspect revenue and order density by destination nation.
-- -----------------------------------------------------------------------------
SELECT 
    country,
    COUNT(DISTINCT customerid) AS active_customers,
    COUNT(DISTINCT invoiceno) AS total_orders,
    SUM(quantity) AS total_units,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (), 2) AS pct_global_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value
FROM analytics.customer_transactions
GROUP BY country
ORDER BY total_revenue DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- 12. Foundational Monthly Trajectory
-- Business Purpose: Track macro monthly sales velocity, order count, and active accounts.
-- -----------------------------------------------------------------------------
SELECT 
    DATE_TRUNC('month', invoicedate) AS transaction_month,
    COUNT(DISTINCT invoiceno) AS monthly_orders,
    COUNT(DISTINCT customerid) AS monthly_active_customers,
    SUM(quantity) AS monthly_units,
    ROUND(SUM(revenue), 2) AS monthly_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS monthly_aov
FROM analytics.customer_transactions
GROUP BY DATE_TRUNC('month', invoicedate)
ORDER BY transaction_month ASC;
