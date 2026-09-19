-- =============================================================================
-- CustomerLens: Customer-Level RFM Segmentation Base
-- Phase 8 â€” RFM Analysis Layer
-- =============================================================================
-- Database: customer_lens
-- Schema:   analytics
-- Table:    analytics.customer_transactions
-- Purpose:  Transform transaction-level customer purchase records into
--           customer-level behavioral features (Recency, Frequency, Monetary)
--           anchored to the dataset reference date.
-- =============================================================================

WITH dataset_anchor AS (
    -- Reference date is dynamically derived as MAX(InvoiceDate) + 1 day
    -- Baseline: 2011-12-09 12:50:00 + 1 day = 2011-12-10 12:50:00
    SELECT
        MAX(invoicedate) + INTERVAL '1 day' AS reference_date
    FROM analytics.customer_transactions
),
customer_aggregates AS (
    SELECT
        t.customerid,
        -- Recency: integer number of full elapsed days between reference date and latest purchase
        FLOOR(EXTRACT(EPOCH FROM (a.reference_date - MAX(t.invoicedate))) / 86400)::INTEGER AS recency,
        -- Frequency: count of distinct completed orders (invoices)
        COUNT(DISTINCT t.invoiceno) AS frequency,
        -- Monetary: total gross spend across all completed orders
        ROUND(SUM(t.revenue), 2) AS monetary,
        -- First and last transaction timestamps
        MIN(t.invoicedate) AS first_purchase_date,
        MAX(t.invoicedate) AS last_purchase_date,
        -- Primary country: mode country to preserve strict 1-to-1 customer record integrity
        MODE() WITHIN GROUP (ORDER BY t.country) AS country
    FROM analytics.customer_transactions t
    CROSS JOIN dataset_anchor a
    GROUP BY t.customerid, a.reference_date
)
SELECT
    customerid,
    recency,
    frequency,
    monetary,
    first_purchase_date,
    last_purchase_date,
    country
FROM customer_aggregates
ORDER BY monetary DESC, customerid ASC;
