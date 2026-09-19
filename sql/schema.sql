-- =============================================================================
-- CustomerLens: PostgreSQL Analytical Schema Definition
-- Phase 7.1 — PostgreSQL Analytical Layer Foundation
-- =============================================================================
-- This script creates the dedicated 'analytics' schema and the primary analytical
-- table 'analytics.customer_transactions' designed to store verified, cleaned
-- customer-attributed purchase transactions.
-- =============================================================================

-- 1. Create dedicated analytical schema
CREATE SCHEMA IF NOT EXISTS analytics;

-- 2. Drop existing table if recreating schema (controlled idempotency for DDL)
DROP TABLE IF EXISTS analytics.customer_transactions CASCADE;

-- 3. Create analytical customer transactions table
CREATE TABLE analytics.customer_transactions (
    InvoiceNo           TEXT            NOT NULL,
    StockCode           TEXT            NOT NULL,
    Description         TEXT,
    Quantity            INTEGER         NOT NULL,
    InvoiceDate         TIMESTAMP       NOT NULL,
    UnitPrice           NUMERIC(12, 4)  NOT NULL,
    CustomerID          TEXT            NOT NULL,
    Country             TEXT            NOT NULL,
    TransactionType     TEXT            NOT NULL,
    DescriptionMissing  BOOLEAN         NOT NULL DEFAULT FALSE,
    Revenue             NUMERIC(14, 2)  NOT NULL,

    -- Table Constraints Reflecting Validated Analytical Invariants
    CONSTRAINT chk_customer_transactions_quantity
        CHECK (Quantity > 0),
    CONSTRAINT chk_customer_transactions_unitprice
        CHECK (UnitPrice > 0),
    CONSTRAINT chk_customer_transactions_transaction_type
        CHECK (TransactionType = 'Sale'),
    CONSTRAINT chk_customer_transactions_revenue
        CHECK (Revenue >= 0),
    CONSTRAINT chk_customer_transactions_customer_id
        CHECK (CustomerID IS NOT NULL AND length(trim(CustomerID)) > 0)
);

-- Comments for documentation & data cataloging
COMMENT ON SCHEMA analytics IS 'Dedicated schema for CustomerLens analytical tables and queries.';
COMMENT ON TABLE analytics.customer_transactions IS 'Cleaned, customer-attributed purchase transactions for RFM modeling and analytical SQL queries.';
COMMENT ON COLUMN analytics.customer_transactions.InvoiceNo IS '6-digit unique commercial invoice number identifying completed orders.';
COMMENT ON COLUMN analytics.customer_transactions.StockCode IS 'Alphanumeric item identifier for catalog merchandise.';
COMMENT ON COLUMN analytics.customer_transactions.Description IS 'Standardized product description text.';
COMMENT ON COLUMN analytics.customer_transactions.Quantity IS 'Number of physical units purchased (Quantity > 0).';
COMMENT ON COLUMN analytics.customer_transactions.InvoiceDate IS 'Timestamp when transaction was recorded.';
COMMENT ON COLUMN analytics.customer_transactions.UnitPrice IS 'Unit price in GBP (£) (UnitPrice > 0).';
COMMENT ON COLUMN analytics.customer_transactions.CustomerID IS '5-digit identified customer identifier string.';
COMMENT ON COLUMN analytics.customer_transactions.Country IS 'Customer billing destination country.';
COMMENT ON COLUMN analytics.customer_transactions.TransactionType IS 'Operational category; strictly Sale in this analytical table.';
COMMENT ON COLUMN analytics.customer_transactions.DescriptionMissing IS 'Flag indicating whether original Description was missing.';
COMMENT ON COLUMN analytics.customer_transactions.Revenue IS 'Computed monetary gross spend (Quantity * UnitPrice, rounded to 2 decimals).';
