"""
CustomerLens — Application Utility Functions (Phase 11).

Provides pure formatting, KPI calculation, filtering, and validation helpers
for the Streamlit application and automated test suites.
"""

from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd


def format_currency(value: Any, precision: int = 2) -> str:
    """
    Format a numeric value as GBP (£) currency string with comma separators.

    Args:
        value: Numeric value or None.
        precision: Decimal places.

    Returns:
        str: Formatted string (e.g. '£8,887,208.89').
    """
    if value is None or pd.isna(value):
        return "£0.00"
    try:
        val = float(value)
        return f"£{val:,.{precision}f}"
    except (ValueError, TypeError):
        return "£0.00"


def format_number(value: Any, precision: int = 0) -> str:
    """
    Format a numeric value with comma thousands separators.

    Args:
        value: Numeric value or None.
        precision: Decimal places.

    Returns:
        str: Formatted string (e.g. '4,338').
    """
    if value is None or pd.isna(value):
        return "0"
    try:
        val = float(value)
        if precision == 0:
            return f"{int(round(val)):,}"
        return f"{val:,.{precision}f}"
    except (ValueError, TypeError):
        return "0"


def format_percentage(value: Any, precision: int = 1) -> str:
    """
    Format a numeric value as percentage string. Assumes 0-100 scale.

    Args:
        value: Percentage value (e.g. 16.51).
        precision: Decimal places.

    Returns:
        str: Formatted string (e.g. '16.5%').
    """
    if value is None or pd.isna(value):
        return "0.0%"
    try:
        val = float(value)
        return f"{val:.{precision}f}%"
    except (ValueError, TypeError):
        return "0.0%"


def safe_percentage(numerator: float, denominator: float) -> float:
    """
    Compute safe percentage avoiding division by zero.

    Args:
        numerator: Numerator value.
        denominator: Denominator value.

    Returns:
        float: (numerator / denominator) * 100 or 0.0 if denominator <= 0.
    """
    try:
        num = float(numerator)
        denom = float(denominator)
        if denom == 0 or np.isnan(denom) or np.isnan(num):
            return 0.0
        return round((num / denom) * 100.0, 2)
    except (ZeroDivisionError, ValueError, TypeError):
        return 0.0


def calculate_executive_kpis(
    transactions_df: pd.DataFrame,
    customers_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Calculate top-line empirical KPIs from transaction and customer datasets.

    Args:
        transactions_df: Customer transactions fact DataFrame.
        customers_df: Customer business segments or RFM DataFrame.

    Returns:
        Dict[str, Any]: Dictionary of empirical KPI metrics.
    """
    tx = transactions_df.copy()
    tx.columns = tx.columns.str.lower()
    cust = customers_df.copy()
    cust.columns = cust.columns.str.lower()

    total_customers = int(cust["customerid"].nunique())
    total_orders = int(tx["invoiceno"].nunique())
    total_revenue = float(tx["revenue"].sum())

    aov = total_revenue / total_orders if total_orders > 0 else 0.0

    # Repeat purchasing calculations
    cust_freq = cust.set_index("customerid")["frequency"]
    repeat_customers = int((cust_freq > 1).sum())
    repeat_customer_rate = safe_percentage(repeat_customers, total_customers)

    cust_monetary = cust.set_index("customerid")["monetary"]
    repeat_revenue = float(cust_monetary[cust_freq > 1].sum())
    repeat_revenue_rate = safe_percentage(repeat_revenue, total_revenue)

    return {
        "total_customers": total_customers,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "average_order_value": round(aov, 2),
        "repeat_customers": repeat_customers,
        "repeat_customer_rate": round(repeat_customer_rate, 2),
        "repeat_revenue": round(repeat_revenue, 2),
        "repeat_revenue_rate": round(repeat_revenue_rate, 2),
    }



def filter_customers(
    df: pd.DataFrame,
    search_query: Optional[str] = None,
    segments: Optional[List[str]] = None,
    action_categories: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
    min_monetary: Optional[float] = None,
    max_monetary: Optional[float] = None,
    min_frequency: Optional[int] = None,
    max_recency: Optional[int] = None,
) -> pd.DataFrame:
    """
    Filter customer dataset by multiple operational criteria.

    Args:
        df: Customer DataFrame.
        search_query: Optional string search for customerid.
        segments: Optional list of selected business segments.
        action_categories: Optional list of selected action categories.
        countries: Optional list of selected countries.
        min_monetary: Optional minimum spend threshold.
        max_monetary: Optional maximum spend threshold.
        min_frequency: Optional minimum order count.
        max_recency: Optional maximum recency in days.

    Returns:
        pd.DataFrame: Filtered copy of customer DataFrame.
    """
    if df.empty:
        return df.copy()

    filtered = df.copy()

    # Search customer ID
    if search_query:
        query_str = str(search_query).strip()
        filtered = filtered[filtered["customerid"].astype(str).str.contains(query_str, case=False, na=False)]

    # Segment filter
    if segments:
        filtered = filtered[filtered["business_segment"].isin(segments)]

    # Action category filter
    if action_categories and "action_category" in filtered.columns:
        filtered = filtered[filtered["action_category"].isin(action_categories)]

    # Country filter
    if countries and "country" in filtered.columns:
        filtered = filtered[filtered["country"].isin(countries)]

    # Numerical range filters
    if min_monetary is not None:
        filtered = filtered[filtered["monetary"] >= min_monetary]

    if max_monetary is not None:
        filtered = filtered[filtered["monetary"] <= max_monetary]

    if min_frequency is not None:
        filtered = filtered[filtered["frequency"] >= min_frequency]

    if max_recency is not None:
        filtered = filtered[filtered["recency"] <= max_recency]

    return filtered


def validate_required_columns(df: pd.DataFrame, required_cols: List[str], dataset_name: str) -> None:
    """
    Validate that required columns exist in a loaded DataFrame.

    Args:
        df: DataFrame to check.
        required_cols: List of required column names.
        dataset_name: Human-readable name for error messages.
    """
    if df.empty:
        raise ValueError(f"{dataset_name} is empty.")
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{dataset_name} missing required columns: {missing}")


def generate_customer_interpretation(customer_row: pd.Series) -> str:
    """
    Generate factual, metric-grounded plain-language summary for a single customer.

    Strictly avoids unsupported predictive or demographic claims.

    Args:
        customer_row: Series representing a customer record.

    Returns:
        str: Factual interpretation string.
    """
    cid = customer_row.get("customerid", "N/A")
    seg = customer_row.get("business_segment", "Unknown")
    action = customer_row.get("action_category", "Unknown")
    rec = customer_row.get("recency", 0)
    freq = customer_row.get("frequency", 0)
    mon = customer_row.get("monetary", 0.0)
    country = customer_row.get("country", "Unknown")

    desc = (
        f"Customer {cid} (located in {country}) has completed {freq} order(s) with total cumulative "
        f"spend of £{mon:,.2f}. The last completed transaction occurred {rec} day(s) prior to the dataset anchor. "
        f"Based on these empirical attributes, this customer belongs to the '{seg}' segment "
        f"with an operational priority of '{action}'."
    )
    return desc
