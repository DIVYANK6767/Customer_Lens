"""Exploratory Data Analysis (EDA) support module for CustomerLens.

Provides reusable, deterministic, and testable analytical functions to summarize
customer transaction data, compute key performance indicators (KPIs), evaluate
time-series patterns, and measure customer revenue concentration.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.data_loader import get_project_root

PROJECT_ROOT = get_project_root()
DEFAULT_CUSTOMER_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "customer_transactions.csv"

REQUIRED_EDA_COLUMNS: List[str] = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
    "Revenue",
]


# ---------------------------------------------------------------------------
# 1. Validation & Input Sanity
# ---------------------------------------------------------------------------

def validate_eda_input(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
) -> bool:
    """Validate that the DataFrame meets the structural invariants for customer EDA.

    Invariants:
    - All required columns must be present.
    - CustomerID must have no missing values.
    - Quantity must be strictly positive (> 0).
    - UnitPrice must be strictly positive (> 0).
    - Revenue must have no missing values.

    Args:
        df: Input DataFrame to validate.
        required_columns: List of required columns. Defaults to REQUIRED_EDA_COLUMNS.

    Returns:
        bool: True if validation succeeds.

    Raises:
        ValueError: If required columns are missing or analytical invariants are violated.
    """
    if required_columns is None:
        required_columns = REQUIRED_EDA_COLUMNS

    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        raise ValueError(f"EDA input validation failed. Missing required column(s): {missing_cols}")

    if df.empty:
        return True

    # Check CustomerID missingness
    if df["CustomerID"].isna().any():
        null_count = int(df["CustomerID"].isna().sum())
        raise ValueError(
            f"EDA input validation failed: Found {null_count} rows with missing CustomerID. "
            "Customer transactions dataset must not contain null customer IDs."
        )

    # Check Quantity > 0
    neg_qty = int((df["Quantity"] <= 0).sum())
    if neg_qty > 0:
        raise ValueError(
            f"EDA input validation failed: Found {neg_qty} rows with Quantity <= 0. "
            "Customer transactions must only contain positive quantities."
        )

    # Check UnitPrice > 0
    neg_price = int((df["UnitPrice"] <= 0).sum())
    if neg_price > 0:
        raise ValueError(
            f"EDA input validation failed: Found {neg_price} rows with UnitPrice <= 0. "
            "Customer transactions must only contain positive prices."
        )

    # Check Revenue is not null
    if df["Revenue"].isna().any():
        null_rev = int(df["Revenue"].isna().sum())
        raise ValueError(f"EDA input validation failed: Found {null_rev} rows with missing Revenue.")

    return True


# ---------------------------------------------------------------------------
# 2. Dataset Level Overview
# ---------------------------------------------------------------------------

def get_dataset_summary(df: pd.DataFrame) -> Dict[str, Union[int, float, str]]:
    """Compute overall high-level summary KPIs for the customer transaction dataset.

    Args:
        df: Customer transaction DataFrame.

    Returns:
        Dict: Dictionary of dataset-level KPIs.
    """
    if df.empty:
        return {
            "total_rows": 0,
            "total_columns": len(df.columns),
            "unique_customers": 0,
            "unique_orders": 0,
            "unique_products": 0,
            "unique_countries": 0,
            "date_min": "N/A",
            "date_max": "N/A",
            "total_quantity": 0,
            "total_revenue": 0.0,
            "aov": 0.0,
            "memory_usage_mb": 0.0,
        }

    date_series = pd.to_datetime(df["InvoiceDate"])
    total_rev = float(df["Revenue"].sum())
    unique_orders = int(df["InvoiceNo"].nunique())
    aov = round(total_rev / unique_orders, 2) if unique_orders > 0 else 0.0

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "unique_customers": int(df["CustomerID"].nunique()),
        "unique_orders": unique_orders,
        "unique_products": int(df["StockCode"].nunique()),
        "unique_countries": int(df["Country"].nunique()),
        "date_min": str(date_series.min()),
        "date_max": str(date_series.max()),
        "total_quantity": int(df["Quantity"].sum()),
        "total_revenue": round(total_rev, 2),
        "aov": aov,
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
    }


# ---------------------------------------------------------------------------
# 3. Time Series Analytics
# ---------------------------------------------------------------------------

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived analytical time fields for exploratory data analysis.

    Does not modify the original DataFrame.

    Args:
        df: DataFrame with 'InvoiceDate' column.

    Returns:
        pd.DataFrame: Copy of df with Year, Month, YearMonth, DayOfWeek, and Hour.
    """
    df_out = df.copy()
    dt = pd.to_datetime(df_out["InvoiceDate"])

    df_out["Year"] = dt.dt.year
    df_out["Month"] = dt.dt.month
    df_out["YearMonth"] = dt.dt.strftime("%Y-%m")
    df_out["DayOfWeek"] = dt.dt.day_name()
    df_out["Hour"] = dt.dt.hour

    return df_out


def get_time_summary(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Generate monthly, daily, and hourly transaction performance tables.

    Args:
        df: Customer transaction DataFrame.

    Returns:
        Dict: Contains 'monthly', 'day_of_week', and 'hourly' DataFrames.
    """
    if df.empty:
        return {
            "monthly": pd.DataFrame(),
            "day_of_week": pd.DataFrame(),
            "hourly": pd.DataFrame(),
        }

    df_time = add_time_features(df)

    # Monthly aggregation
    monthly = (
        df_time.groupby("YearMonth")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
            Quantity=("Quantity", "sum"),
        )
        .reset_index()
    )
    monthly["AOV"] = (monthly["Revenue"] / monthly["Orders"]).round(2)
    monthly["Revenue"] = monthly["Revenue"].round(2)

    # Day of week aggregation (ordered chronologically Monday-Sunday)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = (
        df_time.groupby("DayOfWeek")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
            Quantity=("Quantity", "sum"),
        )
        .reindex(day_order)
        .dropna(how="all")
        .reset_index()
    )
    dow["Revenue"] = dow["Revenue"].round(2)
    dow["AOV"] = (dow["Revenue"] / dow["Orders"]).round(2)

    # Hourly aggregation
    hourly = (
        df_time.groupby("Hour")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Quantity=("Quantity", "sum"),
        )
        .reset_index()
    )
    hourly["Revenue"] = hourly["Revenue"].round(2)

    return {
        "monthly": monthly,
        "day_of_week": dow,
        "hourly": hourly,
    }


# ---------------------------------------------------------------------------
# 4. Customer Level Summaries & Concentration
# ---------------------------------------------------------------------------

def get_customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transactional records into customer-level descriptive summaries.

    Args:
        df: Customer transaction DataFrame.

    Returns:
        pd.DataFrame: One row per CustomerID with order_count, total_revenue, total_quantity, and aov.
    """
    if df.empty:
        return pd.DataFrame(columns=["CustomerID", "order_count", "total_revenue", "total_quantity", "aov"])

    cust_df = (
        df.groupby("CustomerID")
        .agg(
            order_count=("InvoiceNo", "nunique"),
            total_revenue=("Revenue", "sum"),
            total_quantity=("Quantity", "sum"),
        )
        .reset_index()
    )
    cust_df["aov"] = (cust_df["total_revenue"] / cust_df["order_count"]).round(2)
    cust_df["total_revenue"] = cust_df["total_revenue"].round(2)
    return cust_df.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)


def calculate_revenue_concentration(df: pd.DataFrame) -> Dict[str, Union[int, float]]:
    """Measure revenue concentration across top customer tiers.

    Args:
        df: Customer transaction DataFrame.

    Returns:
        Dict: Metrics for top 10, top 20, top 5%, and top 10% customer revenue share.
    """
    if df.empty:
        return {
            "total_customers": 0,
            "total_revenue": 0.0,
            "top_10_revenue": 0.0,
            "top_10_pct": 0.0,
            "top_20_revenue": 0.0,
            "top_20_pct": 0.0,
            "top_5pct_count": 0,
            "top_5pct_revenue": 0.0,
            "top_5pct_pct": 0.0,
            "top_10pct_count": 0,
            "top_10pct_revenue": 0.0,
            "top_10pct_pct": 0.0,
        }

    cust_rev = df.groupby("CustomerID")["Revenue"].sum().sort_values(ascending=False)
    total_rev = float(cust_rev.sum())
    n_cust = len(cust_rev)

    if total_rev == 0 or n_cust == 0:
        return {
            "total_customers": n_cust,
            "total_revenue": 0.0,
            "top_10_revenue": 0.0,
            "top_10_pct": 0.0,
            "top_20_revenue": 0.0,
            "top_20_pct": 0.0,
            "top_5pct_count": 0,
            "top_5pct_revenue": 0.0,
            "top_5pct_pct": 0.0,
            "top_10pct_count": 0,
            "top_10pct_revenue": 0.0,
            "top_10pct_pct": 0.0,
        }

    top_10_rev = float(cust_rev.head(10).sum())
    top_20_rev = float(cust_rev.head(20).sum())

    n_5pct = max(1, int(np.ceil(n_cust * 0.05)))
    n_10pct = max(1, int(np.ceil(n_cust * 0.10)))

    top_5pct_rev = float(cust_rev.head(n_5pct).sum())
    top_10pct_rev = float(cust_rev.head(n_10pct).sum())

    return {
        "total_customers": n_cust,
        "total_revenue": round(total_rev, 2),
        "top_10_revenue": round(top_10_rev, 2),
        "top_10_pct": round((top_10_rev / total_rev) * 100, 2),
        "top_20_revenue": round(top_20_rev, 2),
        "top_20_pct": round((top_20_rev / total_rev) * 100, 2),
        "top_5pct_count": n_5pct,
        "top_5pct_revenue": round(top_5pct_rev, 2),
        "top_5pct_pct": round((top_5pct_rev / total_rev) * 100, 2),
        "top_10pct_count": n_10pct,
        "top_10pct_revenue": round(top_10pct_rev, 2),
        "top_10pct_pct": round((top_10pct_rev / total_rev) * 100, 2),
    }


# ---------------------------------------------------------------------------
# 5. Order Analytics & Repeat Rates
# ---------------------------------------------------------------------------

def calculate_aov(df: pd.DataFrame) -> float:
    """Calculate Average Order Value as Total Revenue divided by unique completed orders.

    Args:
        df: Customer transaction DataFrame.

    Returns:
        float: Average Order Value in GBP rounded to 2 decimals.
    """
    if df.empty:
        return 0.0
    orders = df["InvoiceNo"].nunique()
    if orders == 0:
        return 0.0
    return round(float(df["Revenue"].sum()) / orders, 2)


def calculate_repeat_customer_rate(df: pd.DataFrame) -> Dict[str, Union[int, float]]:
    """Determine the proportion of customers with > 1 distinct completed invoice.

    Args:
        df: Customer transaction DataFrame.

    Returns:
        Dict: One-time count, repeat count, and repeat customer percentage rate.
    """
    if df.empty:
        return {
            "total_customers": 0,
            "one_time_customers": 0,
            "repeat_customers": 0,
            "repeat_customer_rate": 0.0,
            "one_time_customer_rate": 0.0,
        }

    orders_per_cust = df.groupby("CustomerID")["InvoiceNo"].nunique()
    total_cust = len(orders_per_cust)
    one_time = int((orders_per_cust == 1).sum())
    repeat = int((orders_per_cust > 1).sum())

    repeat_rate = round((repeat / total_cust) * 100, 2) if total_cust > 0 else 0.0
    one_time_rate = round((one_time / total_cust) * 100, 2) if total_cust > 0 else 0.0

    return {
        "total_customers": total_cust,
        "one_time_customers": one_time,
        "repeat_customers": repeat,
        "repeat_customer_rate": repeat_rate,
        "one_time_customer_rate": one_time_rate,
    }


def get_order_summary(df: pd.DataFrame) -> Dict[str, Union[int, float]]:
    """Compute comprehensive order behavior metrics.

    Args:
        df: Customer transaction DataFrame.

    Returns:
        Dict: Order summary metrics.
    """
    if df.empty:
        return {
            "total_orders": 0,
            "aov": 0.0,
            "orders_per_customer_mean": 0.0,
            "orders_per_customer_median": 0.0,
            "orders_per_customer_max": 0,
            "one_time_customers": 0,
            "repeat_customers": 0,
            "repeat_customer_rate": 0.0,
        }

    orders_per_cust = df.groupby("CustomerID")["InvoiceNo"].nunique()
    repeat_stats = calculate_repeat_customer_rate(df)

    return {
        "total_orders": int(df["InvoiceNo"].nunique()),
        "aov": calculate_aov(df),
        "orders_per_customer_mean": round(float(orders_per_cust.mean()), 2),
        "orders_per_customer_median": float(orders_per_cust.median()),
        "orders_per_customer_max": int(orders_per_cust.max()),
        "one_time_customers": repeat_stats["one_time_customers"],
        "repeat_customers": repeat_stats["repeat_customers"],
        "repeat_customer_rate": repeat_stats["repeat_customer_rate"],
    }


# ---------------------------------------------------------------------------
# 6. Country & Product Analytics
# ---------------------------------------------------------------------------

def get_country_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate customer behavior, orders, and revenue by billing country.

    Args:
        df: Customer transaction DataFrame.

    Returns:
        pd.DataFrame: Summary table sorted by Revenue descending.
    """
    if df.empty:
        return pd.DataFrame(columns=["Country", "Customers", "Orders", "Revenue", "Quantity", "AOV", "PctRevenue"])

    total_rev = float(df["Revenue"].sum())

    country_df = (
        df.groupby("Country")
        .agg(
            Customers=("CustomerID", "nunique"),
            Orders=("InvoiceNo", "nunique"),
            Revenue=("Revenue", "sum"),
            Quantity=("Quantity", "sum"),
        )
        .reset_index()
    )
    country_df["AOV"] = (country_df["Revenue"] / country_df["Orders"]).round(2)
    country_df["PctRevenue"] = (
        (country_df["Revenue"] / total_rev) * 100
    ).round(2) if total_rev > 0 else 0.0
    country_df["Revenue"] = country_df["Revenue"].round(2)

    return country_df.sort_values(by="Revenue", ascending=False).reset_index(drop=True)


def get_product_summary(df: pd.DataFrame, top_n: int = 10) -> Dict[str, Union[int, pd.DataFrame]]:
    """Identify top products by sales volume and monetary revenue.

    Args:
        df: Customer transaction DataFrame.
        top_n: Number of leading products to return.

    Returns:
        Dict: Total unique products, top_by_quantity, and top_by_revenue DataFrames.
    """
    if df.empty:
        return {
            "total_unique_products": 0,
            "top_by_quantity": pd.DataFrame(),
            "top_by_revenue": pd.DataFrame(),
        }

    # Group by StockCode and Description (taking the most frequent description)
    prod_grouped = (
        df.groupby(["StockCode", "Description"])
        .agg(
            Quantity=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            Transactions=("InvoiceNo", "count"),
        )
        .reset_index()
    )
    prod_grouped["Revenue"] = prod_grouped["Revenue"].round(2)

    top_qty = prod_grouped.sort_values(by="Quantity", ascending=False).head(top_n).reset_index(drop=True)
    top_rev = prod_grouped.sort_values(by="Revenue", ascending=False).head(top_n).reset_index(drop=True)

    return {
        "total_unique_products": int(df["StockCode"].nunique()),
        "top_by_quantity": top_qty,
        "top_by_revenue": top_rev,
    }
