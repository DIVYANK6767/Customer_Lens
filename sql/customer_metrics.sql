-- =============================================================================
-- CustomerLens: Customer-Level SQL Analytics
-- Phase 7.2 — PostgreSQL Analytical Layer
-- =============================================================================
-- Database: customer_lens
-- Schema:   analytics
-- Table:    analytics.customer_transactions
-- Purpose:  Advanced customer behavior, order frequency, monetary value,
--           revenue contribution, cumulative concentration, repeat purchase
--           rates, and recency/inactivity analysis.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Section A: Customer Revenue & Lifetime Value Summary
-- Business Purpose: Calculate core lifetime transactional metrics for every customer.
-- -----------------------------------------------------------------------------
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


-- -----------------------------------------------------------------------------
-- Section B: Customer Purchase Frequency Distribution
-- Business Purpose: Quantify purchasing frequency and group customers by order volume.
-- -----------------------------------------------------------------------------
WITH customer_orders AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS order_count,
        SUM(revenue) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
)
SELECT 
    order_count AS completed_orders,
    COUNT(customerid) AS customer_count,
    ROUND(COUNT(customerid) * 100.0 / SUM(COUNT(customerid)) OVER (), 2) AS pct_of_customers,
    ROUND(SUM(customer_revenue), 2) AS tier_revenue,
    ROUND(SUM(customer_revenue) * 100.0 / SUM(SUM(customer_revenue)) OVER (), 2) AS pct_of_revenue
FROM customer_orders
GROUP BY order_count
ORDER BY order_count ASC;


-- -----------------------------------------------------------------------------
-- Section C: Customer Ranking by Revenue
-- Business Purpose: Rank customers based on revenue using RANK() and DENSE_RANK().
-- -----------------------------------------------------------------------------
WITH customer_spend AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS total_orders,
        ROUND(SUM(revenue), 2) AS total_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
)
SELECT 
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY total_revenue DESC) AS revenue_dense_rank,
    customerid,
    total_orders,
    total_revenue
FROM customer_spend
ORDER BY revenue_rank ASC
LIMIT 25;


-- -----------------------------------------------------------------------------
-- Section D: Customer Revenue Contribution (Window Function)
-- Business Purpose: Calculate each customer's individual percentage contribution
-- to total company revenue using SUM() OVER ().
-- -----------------------------------------------------------------------------
WITH customer_spend AS (
    SELECT 
        customerid,
        ROUND(SUM(revenue), 2) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
)
SELECT 
    customerid,
    customer_revenue,
    ROUND(SUM(customer_revenue) OVER (), 2) AS total_company_revenue,
    ROUND((customer_revenue * 100.0 / NULLIF(SUM(customer_revenue) OVER (), 0)), 4) AS revenue_pct_contribution
FROM customer_spend
ORDER BY customer_revenue DESC
LIMIT 25;


-- -----------------------------------------------------------------------------
-- Section E: Cumulative Revenue Contribution (Lorenz / Concentration Curve)
-- Business Purpose: Compute cumulative running total and cumulative percentage
-- to evaluate revenue concentration across descending customer spenders.
-- -----------------------------------------------------------------------------
WITH customer_spend AS (
    SELECT 
        customerid,
        ROUND(SUM(revenue), 2) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
),
ranked_spend AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY customer_revenue DESC) AS customer_rank,
        customerid,
        customer_revenue,
        SUM(customer_revenue) OVER (
            ORDER BY customer_revenue DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue,
        SUM(customer_revenue) OVER () AS total_revenue,
        COUNT(*) OVER () AS total_customers
    FROM customer_spend
)
SELECT 
    customer_rank,
    customerid,
    customer_revenue,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND(customer_rank * 100.0 / total_customers, 2) AS cumulative_pct_customers,
    ROUND(cumulative_revenue * 100.0 / total_revenue, 2) AS cumulative_pct_revenue
FROM ranked_spend
ORDER BY customer_rank ASC
LIMIT 30;


-- -----------------------------------------------------------------------------
-- Section F: Repeat vs. One-Time Customer Analysis
-- Business Purpose: Classify customers into One-Time vs Repeat purchasers,
-- and calculate customer count share, order share, and revenue share.
-- Invariant Definition:
--   One-Time Customer = exactly 1 completed invoice
--   Repeat Customer   = 2 or more completed invoices
-- -----------------------------------------------------------------------------
WITH customer_order_counts AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS order_count,
        SUM(revenue) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
),
classified_customers AS (
    SELECT 
        customerid,
        order_count,
        customer_revenue,
        CASE 
            WHEN order_count = 1 THEN 'One-Time Customer'
            ELSE 'Repeat Customer'
        END AS customer_type
    FROM customer_order_counts
)
SELECT 
    customer_type,
    COUNT(customerid) AS customer_count,
    ROUND(COUNT(customerid) * 100.0 / SUM(COUNT(customerid)) OVER (), 2) AS pct_of_customers,
    SUM(order_count) AS total_orders,
    ROUND(SUM(order_count) * 100.0 / SUM(SUM(order_count)) OVER (), 2) AS pct_of_orders,
    ROUND(SUM(customer_revenue), 2) AS total_revenue,
    ROUND(SUM(customer_revenue) * 100.0 / SUM(SUM(customer_revenue)) OVER (), 2) AS pct_of_revenue,
    ROUND(SUM(customer_revenue) / SUM(order_count), 2) AS average_order_value
FROM classified_customers
GROUP BY customer_type
ORDER BY customer_count DESC;


-- -----------------------------------------------------------------------------
-- Section G: Customer Inactivity Analysis (Recency Preparation)
-- Business Purpose: Calculate elapsed days since each customer's last purchase,
-- anchored against the dynamic reference date: MAX(invoicedate) + INTERVAL '1 day'.
-- -----------------------------------------------------------------------------
WITH dataset_anchor AS (
    SELECT 
        MAX(invoicedate) + INTERVAL '1 day' AS reference_date
    FROM analytics.customer_transactions
),
customer_last_purchase AS (
    SELECT 
        t.customerid,
        COUNT(DISTINCT t.invoiceno) AS total_orders,
        ROUND(SUM(t.revenue), 2) AS total_revenue,
        MAX(t.invoicedate) AS last_purchase_date
    FROM analytics.customer_transactions t
    GROUP BY t.customerid
)
SELECT 
    c.customerid,
    c.total_orders,
    c.total_revenue,
    c.last_purchase_date,
    a.reference_date,
    -- Exact elapsed days between reference anchor and customer's last invoice
    ROUND(EXTRACT(EPOCH FROM (a.reference_date - c.last_purchase_date)) / 86400, 1) AS days_since_last_purchase
FROM customer_last_purchase c
CROSS JOIN dataset_anchor a
ORDER BY days_since_last_purchase DESC
LIMIT 25;


-- -----------------------------------------------------------------------------
-- Section H: Top Customers by Revenue (Top 10, 20, 50)
-- Business Purpose: Extract high-value accounts responsible for commercial bulk spend.
-- Note: Grouping strictly by customerid ensures 1-to-1 customer integrity.
-- -----------------------------------------------------------------------------
-- Top 10 Customers
SELECT 
    ROW_NUMBER() OVER (ORDER BY SUM(revenue) DESC) AS rank,
    customerid,
    MAX(country) AS primary_country,
    COUNT(DISTINCT invoiceno) AS total_orders,
    SUM(quantity) AS total_units,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value
FROM analytics.customer_transactions
GROUP BY customerid
ORDER BY total_revenue DESC
LIMIT 10;

-- Top 20 Customers
SELECT 
    ROW_NUMBER() OVER (ORDER BY SUM(revenue) DESC) AS rank,
    customerid,
    MAX(country) AS primary_country,
    COUNT(DISTINCT invoiceno) AS total_orders,
    SUM(quantity) AS total_units,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value
FROM analytics.customer_transactions
GROUP BY customerid
ORDER BY total_revenue DESC
LIMIT 20;

-- Top 50 Customers
SELECT 
    ROW_NUMBER() OVER (ORDER BY SUM(revenue) DESC) AS rank,
    customerid,
    MAX(country) AS primary_country,
    COUNT(DISTINCT invoiceno) AS total_orders,
    SUM(quantity) AS total_units,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value
FROM analytics.customer_transactions
GROUP BY customerid
ORDER BY total_revenue DESC
LIMIT 50;

