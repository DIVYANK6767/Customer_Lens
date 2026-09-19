-- =============================================================================
-- CustomerLens: Revenue & Financial Analytics
-- Phase 7.2 — PostgreSQL Analytical Layer
-- =============================================================================
-- Database: customer_lens
-- Schema:   analytics
-- Table:    analytics.customer_transactions
-- Purpose:  Comprehensive financial analysis including monthly trajectories,
--           month-over-month growth, geographic concentration, diurnal rhythms,
--           day-of-week trends, and basket-level order value percentiles.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Section A: Monthly Revenue & Core Velocity Metrics
-- Business Purpose: Track monthly top-line trajectory, order volume, customer counts, and units.
-- -----------------------------------------------------------------------------
SELECT 
    DATE_TRUNC('month', invoicedate)::DATE AS sales_month,
    COUNT(DISTINCT customerid) AS active_customers,
    COUNT(DISTINCT invoiceno) AS total_orders,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue_gbp,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value_gbp
FROM analytics.customer_transactions
GROUP BY DATE_TRUNC('month', invoicedate)
ORDER BY sales_month ASC;


-- -----------------------------------------------------------------------------
-- Section B: Month-over-Month Revenue Growth (LAG Window Function)
-- Business Purpose: Compute monthly growth rates, absolute revenue delta, and percentage change.
-- Protected against division-by-zero with NULLIF.
-- -----------------------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT 
        DATE_TRUNC('month', invoicedate)::DATE AS sales_month,
        COUNT(DISTINCT invoiceno) AS monthly_orders,
        ROUND(SUM(revenue), 2) AS current_revenue
    FROM analytics.customer_transactions
    GROUP BY DATE_TRUNC('month', invoicedate)
),
monthly_growth AS (
    SELECT 
        sales_month,
        monthly_orders,
        current_revenue,
        LAG(current_revenue, 1) OVER (ORDER BY sales_month ASC) AS previous_month_revenue,
        current_revenue - LAG(current_revenue, 1) OVER (ORDER BY sales_month ASC) AS absolute_change
    FROM monthly_revenue
)
SELECT 
    sales_month,
    monthly_orders,
    current_revenue,
    previous_month_revenue,
    ROUND(absolute_change, 2) AS revenue_delta_gbp,
    ROUND(
        (absolute_change * 100.0) / NULLIF(previous_month_revenue, 0),
        2
    ) AS mom_growth_pct
FROM monthly_growth
ORDER BY sales_month ASC;


-- -----------------------------------------------------------------------------
-- Section C: Country Revenue & Geographic Breakdown
-- Business Purpose: Evaluate revenue, customer counts, order frequency, and AOV by destination nation.
-- -----------------------------------------------------------------------------
SELECT 
    country,
    COUNT(DISTINCT customerid) AS customer_count,
    COUNT(DISTINCT invoiceno) AS order_count,
    SUM(quantity) AS total_units,
    ROUND(SUM(revenue), 2) AS total_revenue_gbp,
    ROUND(
        SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (),
        2
    ) AS pct_of_global_revenue,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value_gbp
FROM analytics.customer_transactions
GROUP BY country
ORDER BY total_revenue_gbp DESC;


-- -----------------------------------------------------------------------------
-- Section D: Country Revenue Ranking (Window Functions)
-- Business Purpose: Rank destination countries using RANK() and DENSE_RANK().
-- -----------------------------------------------------------------------------
WITH country_totals AS (
    SELECT 
        country,
        COUNT(DISTINCT customerid) AS customers,
        COUNT(DISTINCT invoiceno) AS orders,
        ROUND(SUM(revenue), 2) AS total_revenue
    FROM analytics.customer_transactions
    GROUP BY country
)
SELECT 
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY total_revenue DESC) AS revenue_dense_rank,
    country,
    customers,
    orders,
    total_revenue,
    ROUND(total_revenue * 100.0 / SUM(total_revenue) OVER (), 2) AS pct_share
FROM country_totals
ORDER BY revenue_rank ASC
LIMIT 20;


-- -----------------------------------------------------------------------------
-- Section E: Daily Revenue Time Series
-- Business Purpose: High-resolution daily sales trajectory tracking.
-- -----------------------------------------------------------------------------
SELECT 
    invoicedate::DATE AS transaction_date,
    COUNT(DISTINCT invoiceno) AS daily_orders,
    COUNT(DISTINCT customerid) AS daily_active_customers,
    SUM(quantity) AS daily_units_sold,
    ROUND(SUM(revenue), 2) AS daily_revenue_gbp,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS daily_aov_gbp
FROM analytics.customer_transactions
GROUP BY invoicedate::DATE
ORDER BY transaction_date ASC;


-- -----------------------------------------------------------------------------
-- Section F: Day-of-Week Operational Analysis
-- Business Purpose: Identify commercial purchasing rhythms across weekdays.
-- Note: ISODOW maps 1=Monday through 7=Sunday. FMDay trims whitespace padding.
-- -----------------------------------------------------------------------------
SELECT 
    EXTRACT(ISODOW FROM invoicedate)::INTEGER AS day_of_week_iso,
    TO_CHAR(invoicedate, 'FMDay') AS day_name,
    COUNT(DISTINCT invoiceno) AS total_orders,
    COUNT(DISTINCT customerid) AS unique_customers,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue_gbp,
    ROUND(SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (), 2) AS pct_revenue_share,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS average_order_value_gbp
FROM analytics.customer_transactions
GROUP BY EXTRACT(ISODOW FROM invoicedate), TO_CHAR(invoicedate, 'FMDay')
ORDER BY day_of_week_iso ASC;


-- -----------------------------------------------------------------------------
-- Section G: Hourly Diurnal Rhythm Analysis
-- Business Purpose: Measure order distribution and revenue velocity across 24 hours.
-- -----------------------------------------------------------------------------
SELECT 
    EXTRACT(HOUR FROM invoicedate)::INTEGER AS transaction_hour,
    COUNT(DISTINCT invoiceno) AS total_orders,
    COUNT(DISTINCT customerid) AS unique_customers,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue_gbp,
    ROUND(SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (), 2) AS pct_revenue_share,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoiceno), 2) AS hourly_aov_gbp
FROM analytics.customer_transactions
GROUP BY EXTRACT(HOUR FROM invoicedate)
ORDER BY transaction_hour ASC;


-- -----------------------------------------------------------------------------
-- Section H: Order Value Distribution & Percentiles
-- Business Purpose: Calculate basket-level monetary spend percentiles to assess
-- positive skewness (mean vs median) across all completed orders.
-- -----------------------------------------------------------------------------
WITH order_level_spend AS (
    SELECT 
        invoiceno,
        customerid,
        country,
        ROUND(SUM(revenue), 2) AS order_total_revenue,
        SUM(quantity) AS order_units
    FROM analytics.customer_transactions
    GROUP BY invoiceno, customerid, country
)
SELECT 
    COUNT(*) AS total_completed_orders,
    ROUND(MIN(order_total_revenue), 2) AS min_order_value,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY order_total_revenue)::NUMERIC, 2) AS percentile_25_order_value,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY order_total_revenue)::NUMERIC, 2) AS median_order_value,
    ROUND(AVG(order_total_revenue), 2) AS mean_order_value_aov,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY order_total_revenue)::NUMERIC, 2) AS percentile_75_order_value,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY order_total_revenue)::NUMERIC, 2) AS percentile_90_order_value,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY order_total_revenue)::NUMERIC, 2) AS percentile_95_order_value,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY order_total_revenue)::NUMERIC, 2) AS percentile_99_order_value,
    ROUND(MAX(order_total_revenue), 2) AS max_order_value
FROM order_level_spend;
