-- =============================================================================
-- CustomerLens: Strategic Business-Oriented SQL Analytics
-- Phase 7.2 — PostgreSQL Analytical Layer
-- =============================================================================
-- Database: customer_lens
-- Schema:   analytics
-- Table:    analytics.customer_transactions
-- Purpose:  Answer key executive, commercial, and operational business questions
--           using PostgreSQL SQL. Demonstrates advanced analytics, CTEs,
--           window functions, percentile distributions, and cohort breakdowns.
-- =============================================================================

-- =============================================================================
-- Q1. How many active customers do we have?
-- Business Context: Active customers represent verified accounts with at least
--                   one completed purchase during the dataset horizon.
-- =============================================================================
SELECT 
    COUNT(DISTINCT customerid) AS active_customers
FROM analytics.customer_transactions;


-- =============================================================================
-- Q2. How many completed orders do we have?
-- Business Context: Completed orders measure discrete checkout transactions.
--                   Individual line items must not be counted as orders.
-- =============================================================================
SELECT 
    COUNT(DISTINCT invoiceno) AS completed_orders
FROM analytics.customer_transactions;


-- =============================================================================
-- Q3. What is total revenue?
-- Business Context: Gross financial turnover generated across all completed sales.
-- =============================================================================
SELECT 
    ROUND(SUM(revenue), 2) AS total_revenue_gbp
FROM analytics.customer_transactions;


-- =============================================================================
-- Q4. What is average order value (AOV)?
-- Business Context: Measures average transaction basket monetary size.
--                   Formula: Total Revenue / Distinct Completed Orders.
-- =============================================================================
SELECT 
    ROUND(
        SUM(revenue) / NULLIF(COUNT(DISTINCT invoiceno), 0),
        2
    ) AS average_order_value_gbp
FROM analytics.customer_transactions;


-- =============================================================================
-- Q5. What percentage of customers are repeat customers?
-- Business Context: Repeat customers have completed more than one discrete order.
--                   Identifies the baseline customer loyalty foundation.
-- =============================================================================
WITH customer_orders AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS order_count
    FROM analytics.customer_transactions
    GROUP BY customerid
)
SELECT 
    COUNT(CASE WHEN order_count = 1 THEN 1 END) AS one_time_customers,
    COUNT(CASE WHEN order_count > 1 THEN 1 END) AS repeat_customers,
    COUNT(*) AS total_active_customers,
    ROUND(
        COUNT(CASE WHEN order_count = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS one_time_customer_pct,
    ROUND(
        COUNT(CASE WHEN order_count > 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS repeat_customer_pct
FROM customer_orders;


-- =============================================================================
-- Q6. What percentage of revenue comes from repeat customers?
-- Business Context: Measures revenue reliance on repeat vs one-time buyers.
-- =============================================================================
WITH customer_orders AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS order_count,
        SUM(revenue) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
)
SELECT 
    ROUND(SUM(CASE WHEN order_count = 1 THEN customer_revenue ELSE 0 END), 2) AS one_time_revenue_gbp,
    ROUND(SUM(CASE WHEN order_count > 1 THEN customer_revenue ELSE 0 END), 2) AS repeat_revenue_gbp,
    ROUND(SUM(customer_revenue), 2) AS total_revenue_gbp,
    ROUND(
        SUM(CASE WHEN order_count = 1 THEN customer_revenue ELSE 0 END) * 100.0 / 
        NULLIF(SUM(customer_revenue), 0),
        2
    ) AS one_time_revenue_pct,
    ROUND(
        SUM(CASE WHEN order_count > 1 THEN customer_revenue ELSE 0 END) * 100.0 / 
        NULLIF(SUM(customer_revenue), 0),
        2
    ) AS repeat_revenue_pct
FROM customer_orders;


-- =============================================================================
-- Q7. Which countries generate the highest revenue?
-- Business Context: Identifies top geographic markets by total sales, customer
--                   density, order volume, and average order value.
-- =============================================================================
SELECT 
    country,
    COUNT(DISTINCT customerid) AS customer_count,
    COUNT(DISTINCT invoiceno) AS order_count,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue_gbp,
    ROUND(
        SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (),
        2
    ) AS revenue_pct_share,
    ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT invoiceno), 0), 2) AS average_order_value_gbp
FROM analytics.customer_transactions
GROUP BY country
ORDER BY total_revenue_gbp DESC
LIMIT 10;


-- =============================================================================
-- Q8. Which customers generate the highest revenue?
-- Business Context: Identifies key commercial accounts and enterprise buyers
--                   driving the highest top-line cash flow.
-- =============================================================================
SELECT 
    customerid,
    COUNT(DISTINCT invoiceno) AS total_orders,
    SUM(quantity) AS total_units_purchased,
    ROUND(SUM(revenue), 2) AS total_revenue_gbp,
    ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT invoiceno), 0), 2) AS average_order_value_gbp,
    ROUND(
        SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (),
        2
    ) AS revenue_pct_contribution
FROM analytics.customer_transactions
GROUP BY customerid
ORDER BY total_revenue_gbp DESC
LIMIT 10;


-- =============================================================================
-- Q9. What percentage of total revenue comes from the top 10 customers?
-- Business Context: Quantifies top-10 customer concentration risk.
-- =============================================================================
WITH customer_spend AS (
    SELECT 
        customerid,
        SUM(revenue) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
),
ranked_spend AS (
    SELECT 
        customerid,
        customer_revenue,
        ROW_NUMBER() OVER (ORDER BY customer_revenue DESC) AS rank_pos
    FROM customer_spend
)
SELECT 
    COUNT(*) AS cohort_size,
    ROUND(SUM(customer_revenue), 2) AS top_10_revenue_gbp,
    ROUND(
        SUM(customer_revenue) * 100.0 / (SELECT SUM(revenue) FROM analytics.customer_transactions),
        2
    ) AS top_10_pct_of_total_revenue
FROM ranked_spend
WHERE rank_pos <= 10;


-- =============================================================================
-- Q10. What percentage of total revenue comes from the top 20 customers?
-- Business Context: Quantifies top-20 customer concentration risk.
-- =============================================================================
WITH customer_spend AS (
    SELECT 
        customerid,
        SUM(revenue) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
),
ranked_spend AS (
    SELECT 
        customerid,
        customer_revenue,
        ROW_NUMBER() OVER (ORDER BY customer_revenue DESC) AS rank_pos
    FROM customer_spend
)
SELECT 
    COUNT(*) AS cohort_size,
    ROUND(SUM(customer_revenue), 2) AS top_20_revenue_gbp,
    ROUND(
        SUM(customer_revenue) * 100.0 / (SELECT SUM(revenue) FROM analytics.customer_transactions),
        2
    ) AS top_20_pct_of_total_revenue
FROM ranked_spend
WHERE rank_pos <= 20;


-- =============================================================================
-- Q11. What percentage of customers generate approximately 80% of revenue?
-- Business Context: Empirical verification of the Pareto Principle (80/20 Rule).
--                   Calculates the exact customer rank threshold where
--                   cumulative revenue crosses 80%.
-- =============================================================================
WITH customer_spend AS (
    SELECT 
        customerid,
        ROUND(SUM(revenue), 2) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
),
cumulative_analysis AS (
    SELECT 
        customerid,
        customer_revenue,
        ROW_NUMBER() OVER (ORDER BY customer_revenue DESC) AS customer_rank,
        COUNT(*) OVER () AS total_customers,
        SUM(customer_revenue) OVER (
            ORDER BY customer_revenue DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue,
        SUM(customer_revenue) OVER () AS total_revenue
    FROM customer_spend
),
pareto_calc AS (
    SELECT 
        customer_rank,
        customerid,
        customer_revenue,
        cumulative_revenue,
        total_customers,
        total_revenue,
        ROUND((customer_rank * 100.0) / total_customers, 2) AS cumulative_pct_customers,
        ROUND((cumulative_revenue * 100.0) / total_revenue, 2) AS cumulative_pct_revenue
    FROM cumulative_analysis
)
SELECT 
    customer_rank AS threshold_customer_rank,
    total_customers,
    customerid AS boundary_customer_id,
    customer_revenue AS boundary_customer_spend,
    cumulative_revenue,
    cumulative_pct_customers,
    cumulative_pct_revenue
FROM pareto_calc
WHERE cumulative_pct_revenue >= 80.0
ORDER BY customer_rank ASC
LIMIT 1;


-- =============================================================================
-- Q12. Which customers have not purchased recently?
-- Business Context: Identifies dormant accounts based on days elapsed between
--                   their latest order and the dynamic dataset reference date
--                   (MAX(invoicedate) + INTERVAL '1 day' = 2011-12-10 12:50:00).
-- =============================================================================
WITH dataset_anchor AS (
    SELECT 
        MAX(invoicedate) + INTERVAL '1 day' AS reference_date
    FROM analytics.customer_transactions
),
customer_recency AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS total_orders,
        ROUND(SUM(revenue), 2) AS total_revenue,
        MAX(invoicedate) AS last_purchase_date
    FROM analytics.customer_transactions
    GROUP BY customerid
)
SELECT 
    c.customerid,
    c.total_orders,
    c.total_revenue,
    c.last_purchase_date,
    ROUND(EXTRACT(EPOCH FROM (a.reference_date - c.last_purchase_date)) / 86400, 1) AS days_since_last_purchase
FROM customer_recency c
CROSS JOIN dataset_anchor a
ORDER BY days_since_last_purchase DESC
LIMIT 25;


-- =============================================================================
-- Q13. What are the monthly revenue trends?
-- Business Context: Evaluates macro business velocity over the 13-month operating
--                   window (active accounts, orders, unit volume, revenue, AOV).
-- =============================================================================
SELECT 
    DATE_TRUNC('month', invoicedate)::DATE AS sales_month,
    COUNT(DISTINCT customerid) AS active_customers,
    COUNT(DISTINCT invoiceno) AS completed_orders,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(revenue), 2) AS monthly_revenue_gbp,
    ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT invoiceno), 0), 2) AS average_order_value_gbp
FROM analytics.customer_transactions
GROUP BY DATE_TRUNC('month', invoicedate)
ORDER BY sales_month ASC;


-- =============================================================================
-- Q14. Which months have the highest revenue?
-- Business Context: Highlights peak seasonal demand periods ranked by sales.
-- =============================================================================
SELECT 
    DENSE_RANK() OVER (ORDER BY SUM(revenue) DESC) AS revenue_rank,
    DATE_TRUNC('month', invoicedate)::DATE AS sales_month,
    ROUND(SUM(revenue), 2) AS monthly_revenue_gbp,
    COUNT(DISTINCT invoiceno) AS completed_orders,
    COUNT(DISTINCT customerid) AS active_customers,
    ROUND(
        SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (),
        2
    ) AS pct_of_annual_revenue
FROM analytics.customer_transactions
GROUP BY DATE_TRUNC('month', invoicedate)
ORDER BY monthly_revenue_gbp DESC;


-- =============================================================================
-- Q15. Which countries have high revenue relative to their customer count?
-- Business Context: Highlights high-yield international markets where customer
--                   density generates disproportionately high revenue per account.
--                   A filter of >= 5 customers ensures statistical reliability.
-- =============================================================================
SELECT 
    country,
    COUNT(DISTINCT customerid) AS active_customers,
    COUNT(DISTINCT invoiceno) AS completed_orders,
    ROUND(SUM(revenue), 2) AS total_revenue_gbp,
    ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT customerid), 0), 2) AS revenue_per_customer_gbp,
    ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT invoiceno), 0), 2) AS average_order_value_gbp,
    ROUND(COUNT(DISTINCT invoiceno)::NUMERIC / NULLIF(COUNT(DISTINCT customerid), 0), 2) AS orders_per_customer
FROM analytics.customer_transactions
GROUP BY country
HAVING COUNT(DISTINCT customerid) >= 5
ORDER BY revenue_per_customer_gbp DESC
LIMIT 10;


-- =============================================================================
-- Q16. Which customers have high order frequency but relatively low AOV?
-- Business Context: Highlights habitual, frequent shoppers who purchase small
--                   baskets (ideal targets for cross-sell and basket-building).
--                   Threshold: Order count >= 75th percentile (5+ orders) and
--                              AOV < median customer AOV (£290).
-- =============================================================================
WITH customer_aggregates AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS order_count,
        SUM(revenue) AS total_revenue,
        SUM(revenue) / NULLIF(COUNT(DISTINCT invoiceno), 0) AS customer_aov
    FROM analytics.customer_transactions
    GROUP BY customerid
),
portfolio_benchmarks AS (
    SELECT 
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY order_count) AS freq_p75,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY customer_aov) AS aov_p50
    FROM customer_aggregates
)
SELECT 
    c.customerid,
    c.order_count,
    ROUND(c.total_revenue, 2) AS total_revenue_gbp,
    ROUND(c.customer_aov, 2) AS customer_aov_gbp
FROM customer_aggregates c
CROSS JOIN portfolio_benchmarks b
WHERE c.order_count >= b.freq_p75
  AND c.customer_aov < b.aov_p50
ORDER BY c.order_count DESC, customer_aov_gbp ASC
LIMIT 20;


-- =============================================================================
-- Q17. Which customers have high revenue but low order frequency?
-- Business Context: Identifies high-value infrequent purchasers (e.g. bulk wholesale
--                   accounts or occasional corporate gifting accounts).
--                   Threshold: Revenue >= 90th percentile (£3,600+) and
--                              order count <= 2.
-- =============================================================================
WITH customer_aggregates AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS order_count,
        SUM(revenue) AS total_revenue,
        SUM(revenue) / NULLIF(COUNT(DISTINCT invoiceno), 0) AS customer_aov
    FROM analytics.customer_transactions
    GROUP BY customerid
),
portfolio_benchmarks AS (
    SELECT 
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_revenue) AS rev_p90
    FROM customer_aggregates
)
SELECT 
    c.customerid,
    c.order_count,
    ROUND(c.total_revenue, 2) AS total_revenue_gbp,
    ROUND(c.customer_aov, 2) AS customer_aov_gbp
FROM customer_aggregates c
CROSS JOIN portfolio_benchmarks b
WHERE c.total_revenue >= b.rev_p90
  AND c.order_count <= 2
ORDER BY c.total_revenue DESC
LIMIT 20;


-- =============================================================================
-- Q18. What percentage of orders come from repeat customers?
-- Business Context: Assesses transactional order volume generated by repeat buyers
--                   versus one-time customer acquisition volume.
-- =============================================================================
WITH customer_orders AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS order_count
    FROM analytics.customer_transactions
    GROUP BY customerid
)
SELECT 
    SUM(CASE WHEN order_count = 1 THEN order_count ELSE 0 END) AS one_time_orders,
    SUM(CASE WHEN order_count > 1 THEN order_count ELSE 0 END) AS repeat_orders,
    SUM(order_count) AS total_completed_orders,
    ROUND(
        SUM(CASE WHEN order_count = 1 THEN order_count ELSE 0 END) * 100.0 / NULLIF(SUM(order_count), 0),
        2
    ) AS one_time_order_pct,
    ROUND(
        SUM(CASE WHEN order_count > 1 THEN order_count ELSE 0 END) * 100.0 / NULLIF(SUM(order_count), 0),
        2
    ) AS repeat_order_pct
FROM customer_orders;


-- =============================================================================
-- Q19. What is the distribution of orders per customer?
-- Business Context: Evaluates overall customer purchase frequency distribution
--                   and cumulative adoption curve across order tiers.
-- =============================================================================
WITH customer_orders AS (
    SELECT 
        customerid,
        COUNT(DISTINCT invoiceno) AS order_count
    FROM analytics.customer_transactions
    GROUP BY customerid
)
SELECT 
    order_count AS completed_orders,
    COUNT(customerid) AS customer_count,
    ROUND(COUNT(customerid) * 100.0 / SUM(COUNT(customerid)) OVER (), 2) AS pct_of_customers,
    SUM(COUNT(customerid)) OVER (ORDER BY order_count ASC) AS cumulative_customers,
    ROUND(
        SUM(COUNT(customerid)) OVER (ORDER BY order_count ASC) * 100.0 / SUM(COUNT(customerid)) OVER (),
        2
    ) AS cumulative_pct_customers
FROM customer_orders
GROUP BY order_count
ORDER BY completed_orders ASC
LIMIT 25;


-- =============================================================================
-- Q20. What is the revenue concentration among customers? (Decile Analysis)
-- Business Context: Divides all customers into 10 equal tiers (deciles) ranked
--                   by total monetary spend to demonstrate portfolio concentration.
-- =============================================================================
WITH customer_spend AS (
    SELECT 
        customerid,
        SUM(revenue) AS customer_revenue
    FROM analytics.customer_transactions
    GROUP BY customerid
),
customer_deciles AS (
    SELECT 
        customerid,
        customer_revenue,
        NTILE(10) OVER (ORDER BY customer_revenue DESC) AS revenue_decile
    FROM customer_spend
)
SELECT 
    revenue_decile,
    COUNT(customerid) AS customer_count,
    ROUND(MIN(customer_revenue), 2) AS min_customer_spend_gbp,
    ROUND(MAX(customer_revenue), 2) AS max_customer_spend_gbp,
    ROUND(SUM(customer_revenue), 2) AS decile_revenue_gbp,
    ROUND(
        SUM(customer_revenue) * 100.0 / SUM(SUM(customer_revenue)) OVER (),
        2
    ) AS decile_revenue_pct,
    ROUND(
        SUM(SUM(customer_revenue)) OVER (ORDER BY revenue_decile ASC) * 100.0 / 
        SUM(SUM(customer_revenue)) OVER (),
        2
    ) AS cumulative_revenue_pct
FROM customer_deciles
GROUP BY revenue_decile
ORDER BY revenue_decile ASC;
