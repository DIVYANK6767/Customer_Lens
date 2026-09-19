"""
CustomerLens — Business Insights & Marketing Opportunities Engine (Phase 10).

This module translates empirical cluster profiles and business segment assignments
into explainable business characteristics, strategic hypotheses, and testable
experimentation frameworks without making unsupported predictive claims.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "segment_summary.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

FORBIDDEN_PREDICTIVE_TERMS = [
    "will churn",
    "certain to churn",
    "churn probability",
    "guaranteed roi",
    "guaranteed uplift",
    "proven uplift",
    "predicted churn",
]

REQUIRED_OPPORTUNITY_COLUMNS = [
    "cluster_id",
    "business_segment",
    "action_category",
    "customer_count",
    "customer_percentage",
    "revenue",
    "revenue_percentage",
    "primary_characteristic",
    "business_opportunity",
    "recommended_action",
    "measurement_metric",
    "caveat",
]


def calculate_segment_contribution(summary_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate customer vs. revenue contribution ratios and average metrics.

    Args:
        summary_df: Segment summary DataFrame.

    Returns:
        pd.DataFrame: Augmented DataFrame with concentration ratios.
    """
    df = summary_df.copy()
    # Revenue to customer share ratio (e.g. 65.05 / 16.51 = 3.94x)
    df["revenue_concentration_ratio"] = (
        df["revenue_percentage"] / df["customer_percentage"]
    ).round(2)
    return df


def identify_segment_characteristics(summary_df: pd.DataFrame) -> Dict[int, str]:
    """
    Generate metric-grounded summaries from actual summary statistics.

    Args:
        summary_df: Segment summary DataFrame.

    Returns:
        Dict[int, str]: Mapping of cluster_id to descriptive characteristics.
    """
    characteristics = {}
    for _, row in summary_df.iterrows():
        cid = int(row["cluster_id"])
        char = (
            f"Segment {row['business_segment']} (Cluster {cid}): "
            f"{row['customer_count']:,} customers ({row['customer_percentage']:.2f}% of base), "
            f"£{row['total_revenue']:,.2f} total revenue ({row['revenue_percentage']:.2f}% of turnover), "
            f"median recency {row['median_recency']:.1f} days, median frequency {row['median_frequency']:.1f} orders, "
            f"median spend £{row['median_monetary']:,.2f}."
        )
        characteristics[cid] = char
    return characteristics


def build_opportunity_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct structured marketing opportunities and experimentation framework.

    All recommendations are formulated as testable hypotheses with explicit
    measurement metrics and risk caveats.

    Args:
        summary_df: Segment summary DataFrame.

    Returns:
        pd.DataFrame: Structured marketing opportunities table.
    """
    records = []

    # Look up rows by cluster_id for data grounding
    summary_map = {int(r["cluster_id"]): r for _, r in summary_df.iterrows()}

    # Cluster 3: High-Value Engaged
    r3 = summary_map[3]
    records.append({
        "cluster_id": 3,
        "business_segment": r3["business_segment"],
        "action_category": r3["action_category"],
        "customer_count": int(r3["customer_count"]),
        "customer_percentage": float(r3["customer_percentage"]),
        "revenue": float(r3["total_revenue"]),
        "revenue_percentage": float(r3["revenue_percentage"]),
        "primary_characteristic": (
            "Recent engagement (median 8.0 days), highest order frequency (median 10.0 orders), "
            "and highest monetary contribution (£3,730.61 median; £8,074.73 mean)."
        ),
        "business_opportunity": (
            "VIP account retention, high-touch support, automated restock scheduling, "
            "and wholesale contract continuity."
        ),
        "recommended_action": (
            "Provide dedicated account management support, priority delivery SLAs, "
            "and scheduled quarterly replenishment reviews."
        ),
        "measurement_metric": (
            "90-day account retention rate, order frequency consistency, and gross margin per account."
        ),
        "caveat": (
            "High revenue concentration risk (65.05% of turnover in 16.51% of customers); "
            "avoid excessive price discounting that erodes gross margins."
        ),
    })

    # Cluster 2: Established Valuable
    r2 = summary_map[2]
    records.append({
        "cluster_id": 2,
        "business_segment": r2["business_segment"],
        "action_category": r2["action_category"],
        "customer_count": int(r2["customer_count"]),
        "customer_percentage": float(r2["customer_percentage"]),
        "revenue": float(r2["total_revenue"]),
        "revenue_percentage": float(r2["revenue_percentage"]),
        "primary_characteristic": (
            "Consistent repeat purchasing (median 4.0 orders), moderate recency (median 57.0 days), "
            "and substantial spend (£1,340.08 median; £1,788.31 mean)."
        ),
        "business_opportunity": (
            "Order frequency acceleration, basket threshold incentives, and loyalty tier advancement."
        ),
        "recommended_action": (
            "Introduce tiered spend incentives (£500+ order threshold discounts) and category cross-sell recommendations."
        ),
        "measurement_metric": (
            "Quarterly re-order velocity, average order value (AOV), and repeat purchase frequency."
        ),
        "caveat": (
            "Incentive design must maintain minimum order thresholds to prevent subsidizing purchases "
            "that would have occurred organically."
        ),
    })

    # Cluster 0: Recent Developing
    r0 = summary_map[0]
    records.append({
        "cluster_id": 0,
        "business_segment": r0["business_segment"],
        "action_category": r0["action_category"],
        "customer_count": int(r0["customer_count"]),
        "customer_percentage": float(r0["customer_percentage"]),
        "revenue": float(r0["total_revenue"]),
        "revenue_percentage": float(r0["revenue_percentage"]),
        "primary_characteristic": (
            "Recent purchasing activity (median 17.0 days), introductory frequency (median 2.0 orders), "
            "and modest spend (£481.03 median; £558.28 mean)."
        ),
        "business_opportunity": (
            "Second-order and third-order conversion, post-onboarding habituation, and product discovery."
        ),
        "recommended_action": (
            "Deploy automated post-purchase email onboarding sequences (Day 7 satisfaction, Day 14 discovery, "
            "Day 21 restock trigger)."
        ),
        "measurement_metric": (
            "60-day repeat conversion rate, time-to-second-order, and early customer revenue growth."
        ),
        "caveat": (
            "Risk of email communication fatigue; communications must deliver genuine product relevance "
            "rather than generic discounting."
        ),
    })

    # Cluster 1: Low-Engagement / Reactivation
    r1 = summary_map[1]
    records.append({
        "cluster_id": 1,
        "business_segment": r1["business_segment"],
        "action_category": r1["action_category"],
        "customer_count": int(r1["customer_count"]),
        "customer_percentage": float(r1["customer_percentage"]),
        "revenue": float(r1["total_revenue"]),
        "revenue_percentage": float(r1["revenue_percentage"]),
        "primary_characteristic": (
            "Prolonged inactivity (median recency 174.5 days), single-order concentration (median 1.0 order), "
            "and low monetary spend (£293.78 median; £338.55 mean)."
        ),
        "business_opportunity": (
            "Low-cost digital reactivation testing, clearance promotions, and email list hygiene."
        ),
        "recommended_action": (
            "Test low-cost automated win-back email sequences with seasonal clearance offers and opt-out preference surveys."
        ),
        "measurement_metric": (
            "Reactivation response rate, net incremental margin per reactivated account, and list unsubscribe rate."
        ),
        "caveat": (
            "Over 78% of this cohort made only 1 purchase; paid advertising or physical mailings carry negative "
            "expected ROI."
        ),
    })

    opp_df = pd.DataFrame(records)
    validate_business_insights(opp_df)
    return opp_df.sort_values(by="cluster_id").reset_index(drop=True)


def generate_segment_insights(summary_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate detailed structured analytical insights for business reporting.

    Args:
        summary_df: Segment summary DataFrame.

    Returns:
        List[Dict[str, Any]]: List of insight dictionaries per segment.
    """
    opp_df = build_opportunity_table(summary_df)
    insights = []
    for _, row in opp_df.iterrows():
        insights.append(row.to_dict())
    return insights


def validate_business_insights(opportunities_df: pd.DataFrame) -> None:
    """
    Validate schema, nulls, and ensure absence of unsupported predictive claims.

    Args:
        opportunities_df: Opportunities DataFrame.
    """
    if opportunities_df.empty:
        raise ValueError("Marketing opportunities DataFrame is empty.")

    missing = [c for c in REQUIRED_OPPORTUNITY_COLUMNS if c not in opportunities_df.columns]
    if missing:
        raise ValueError(f"Opportunities table missing required columns: {missing}")

    if opportunities_df.isnull().any().any():
        raise ValueError("Opportunities table contains null values.")

    # Validate against unsupported predictive wording
    for col in ["business_opportunity", "recommended_action", "caveat"]:
        for text in opportunities_df[col].dropna().astype(str):
            lower_text = text.lower()
            for forbidden in FORBIDDEN_PREDICTIVE_TERMS:
                if forbidden in lower_text:
                    raise ValueError(
                        f"Forbidden predictive term '{forbidden}' detected in column '{col}': {text}"
                    )


def save_insights_outputs(
    opportunities_df: pd.DataFrame,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Persist marketing opportunities table to CSV.

    Args:
        opportunities_df: Marketing opportunities DataFrame.
        output_dir: Target output directory.

    Returns:
        Path: Path to saved file.
    """
    target_dir = output_dir or DEFAULT_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    out_path = target_dir / "marketing_opportunities.csv"
    opportunities_df.to_csv(out_path, index=False)
    logger.info(f"Saved marketing opportunities ({len(opportunities_df)} rows) to: {out_path}")
    return out_path


def run_insights_pipeline(
    summary_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Execute business insights and marketing opportunities pipeline.

    Args:
        summary_path: Path to segment_summary.csv.
        output_dir: Directory to save generated files.

    Returns:
        pd.DataFrame: Marketing opportunities DataFrame.
    """
    logger.info("Executing Business Insights Pipeline (Phase 10)...")
    path = summary_path or DEFAULT_SUMMARY_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Segment summary file not found at: {path}. Please run src/segmentation.py first."
        )

    summary_df = pd.read_csv(path)
    opp_df = build_opportunity_table(summary_df)
    save_insights_outputs(opp_df, output_dir)

    logger.info("Business Insights Pipeline successfully completed.")
    return opp_df


if __name__ == "__main__":
    run_insights_pipeline()
