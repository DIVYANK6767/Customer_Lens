"""
CustomerLens — Reusable Charting Components (Phase 11).

Provides pure matplotlib / seaborn visualization functions for all analytical pages.
Handles empty datasets and edge cases safely.
"""

from typing import Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Consistent corporate color palette
SEGMENT_PALETTE = {
    "High-Value Engaged": "#1b5e20",      # Forest Green
    "Established Valuable": "#1976d2",    # Deep Blue
    "Recent Developing": "#f57c00",       # Vivid Amber
    "Low-Engagement / Reactivation": "#757575", # Slate Grey
}

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10


def _empty_figure(message: str = "No data matches the current filters.") -> plt.Figure:
    """Helper to return a clean empty placeholder figure."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, color="#64748b", fontweight="bold")
    ax.axis("off")
    return fig


def plot_revenue_by_month(transactions_df: pd.DataFrame) -> plt.Figure:
    """
    Plot monthly revenue trajectory highlighting seasonal velocity.

    Args:
        transactions_df: Transactions fact table with invoicedate and revenue.

    Returns:
        plt.Figure: Matplotlib figure.
    """
    if transactions_df.empty:
        return _empty_figure()

    df = transactions_df.copy()
    df["year_month"] = df["invoicedate"].dt.to_period("M").astype(str)
    monthly_rev = df.groupby("year_month")["revenue"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(10, 4.5))
    bars = ax.bar(monthly_rev["year_month"], monthly_rev["revenue"] / 1e3, color="#1976d2", width=0.6)

    ax.set_title("Monthly Revenue Trajectory (December 2010 – December 2011)", fontweight="bold", pad=12)
    ax.set_ylabel("Revenue (£ Thousands)")
    ax.set_xlabel("Transaction Month")
    ax.set_xticklabels(monthly_rev["year_month"], rotation=35, ha="right")

    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"£{h:,.0f}k", (bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    return fig


def plot_customer_vs_revenue_share(summary_df: pd.DataFrame) -> plt.Figure:
    """
    Plot side-by-side comparison of Customer Share vs. Revenue Share.

    Args:
        summary_df: Segment summary table.

    Returns:
        plt.Figure: Matplotlib figure.
    """
    if summary_df.empty:
        return _empty_figure()

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    # Customer Share
    sns.barplot(
        data=summary_df,
        x="business_segment",
        y="customer_percentage",
        palette=SEGMENT_PALETTE,
        ax=axes[0],
    )
    axes[0].set_title("Customer Share (% of Base)", fontweight="bold")
    axes[0].set_ylabel("Customer Share (%)")
    axes[0].set_xlabel("")
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=20, ha="right")
    for p in axes[0].patches:
        axes[0].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2, p.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontweight="bold")

    # Revenue Share
    sns.barplot(
        data=summary_df,
        x="business_segment",
        y="revenue_percentage",
        palette=SEGMENT_PALETTE,
        ax=axes[1],
    )
    axes[1].set_title("Revenue Share (% of Turnover)", fontweight="bold")
    axes[1].set_ylabel("Revenue Share (%)")
    axes[1].set_xlabel("")
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=20, ha="right")
    for p in axes[1].patches:
        axes[1].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2, p.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontweight="bold")

    plt.suptitle("Customer Base vs. Gross Revenue Disparity Across Segments", fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    return fig


def plot_revenue_by_country(transactions_df: pd.DataFrame, top_n: int = 10) -> plt.Figure:
    """
    Plot top countries by gross revenue.

    Args:
        transactions_df: Transactions fact table.
        top_n: Number of top countries to show.

    Returns:
        plt.Figure: Matplotlib figure.
    """
    if transactions_df.empty:
        return _empty_figure()

    country_rev = (
        transactions_df.groupby("country")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(10, 4.5))
    bars = ax.barh(country_rev["country"][::-1], country_rev["revenue"][::-1] / 1e3, color="#2e7d32", height=0.6)

    ax.set_title(f"Top {top_n} Revenue Generating Countries", fontweight="bold", pad=12)
    ax.set_xlabel("Revenue (£ Thousands)")
    ax.set_ylabel("")

    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"£{w:,.0f}k", (w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", ha="left", va="center", fontsize=9)

    plt.tight_layout()
    return fig


def plot_repeat_vs_onetime(customers_df: pd.DataFrame) -> plt.Figure:
    """
    Plot repeat vs. one-time buyer breakdown.

    Args:
        customers_df: Customer dataset with frequency and monetary columns.

    Returns:
        plt.Figure: Matplotlib figure.
    """
    if customers_df.empty:
        return _empty_figure()

    repeat_mask = customers_df["frequency"] > 1
    labels = ["One-Time Buyers (1 Order)", "Repeat Buyers (2+ Orders)"]
    counts = [int((~repeat_mask).sum()), int(repeat_mask.sum())]
    revs = [float(customers_df.loc[~repeat_mask, "monetary"].sum()), float(customers_df.loc[repeat_mask, "monetary"].sum())]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    colors = ["#90a4ae", "#1976d2"]

    # Counts
    bars1 = axes[0].bar(labels, counts, color=colors, width=0.5)
    axes[0].set_title("Customer Volume", fontweight="bold")
    axes[0].set_ylabel("Customer Count")
    for bar in bars1:
        h = bar.get_height()
        pct = (h / sum(counts)) * 100
        axes[0].annotate(f"{h:,}\n({pct:.1f}%)", (bar.get_x() + bar.get_width() / 2, h / 2),
                        ha="center", va="center", color="white", fontweight="bold")

    # Revenue
    bars2 = axes[1].bar(labels, [r / 1e6 for r in revs], color=colors, width=0.5)
    axes[1].set_title("Revenue Contribution (£ Millions)", fontweight="bold")
    axes[1].set_ylabel("Gross Turnover (£M)")
    for bar in bars2:
        h = bar.get_height()
        pct = (h / (sum(revs) / 1e6)) * 100
        axes[1].annotate(f"£{h:.2f}M\n({pct:.1f}%)", (bar.get_x() + bar.get_width() / 2, h / 2),
                        ha="center", va="center", color="white", fontweight="bold")

    plt.suptitle("Repeat Buyer Dominance: 65.6% of Customers Drive 93.1% of Revenue", fontsize=11, fontweight="bold", y=1.02)
    plt.tight_layout()
    return fig


def plot_revenue_concentration(summary_df: pd.DataFrame) -> plt.Figure:
    """
    Plot revenue concentration ratio (% Revenue / % Customer share).

    Args:
        summary_df: Segment summary table.

    Returns:
        plt.Figure: Matplotlib figure.
    """
    if summary_df.empty:
        return _empty_figure()

    df = summary_df.copy()
    df["concentration"] = (df["revenue_percentage"] / df["customer_percentage"]).round(2)
    df = df.sort_values(by="concentration", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 4))
    colors = [SEGMENT_PALETTE.get(s, "#1976d2") for s in df["business_segment"]]
    bars = ax.barh(df["business_segment"], df["concentration"], color=colors, height=0.55)
    ax.axvline(1.0, color="crimson", linestyle="--", linewidth=1.5, label="Parity (1.0x)")

    ax.set_title("Revenue Concentration Ratio (Revenue Share / Customer Share)", fontweight="bold", pad=10)
    ax.set_xlabel("Ratio (Values > 1.0 indicate disproportionate revenue generation)")
    ax.legend(loc="lower right")

    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"{w:.2f}x", (w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", ha="left", va="center", fontweight="bold")

    plt.tight_layout()
    return fig


def plot_rfm_metric_comparison(summary_df: pd.DataFrame) -> plt.Figure:
    """
    Plot 3-panel comparison of median Recency, Frequency, and Monetary spend across segments.

    Args:
        summary_df: Segment summary table.

    Returns:
        plt.Figure: Matplotlib figure.
    """
    if summary_df.empty:
        return _empty_figure()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))

    # Median Recency
    sns.barplot(data=summary_df, x="business_segment", y="median_recency", palette=SEGMENT_PALETTE, ax=axes[0])
    axes[0].set_title("Median Recency (Days)", fontweight="bold")
    axes[0].set_ylabel("Elapsed Days (Lower = More Recent)")
    axes[0].set_xlabel("")
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=25, ha="right")
    for p in axes[0].patches:
        axes[0].annotate(f"{p.get_height():.0f} d", (p.get_x() + p.get_width() / 2, p.get_height()),
                        xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontweight="bold")

    # Median Frequency
    sns.barplot(data=summary_df, x="business_segment", y="median_frequency", palette=SEGMENT_PALETTE, ax=axes[1])
    axes[1].set_title("Median Frequency (Orders)", fontweight="bold")
    axes[1].set_ylabel("Orders (Higher = More Frequent)")
    axes[1].set_xlabel("")
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=25, ha="right")
    for p in axes[1].patches:
        axes[1].annotate(f"{p.get_height():.0f} ord", (p.get_x() + p.get_width() / 2, p.get_height()),
                        xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontweight="bold")

    # Median Monetary
    sns.barplot(data=summary_df, x="business_segment", y="median_monetary", palette=SEGMENT_PALETTE, ax=axes[2])
    axes[2].set_title("Median Monetary Spend (£)", fontweight="bold")
    axes[2].set_ylabel("Spend (£) (Higher = More Valuable)")
    axes[2].set_xlabel("")
    axes[2].set_xticklabels(axes[2].get_xticklabels(), rotation=25, ha="right")
    for p in axes[2].patches:
        axes[2].annotate(f"£{p.get_height():,.0f}", (p.get_x() + p.get_width() / 2, p.get_height()),
                        xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontweight="bold")

    plt.suptitle("Behavioral Separation in Empirical RFM Space Across Segments", fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    return fig


def plot_rfm_distributions(rfm_df: pd.DataFrame, use_log: bool = False) -> plt.Figure:
    """
    Plot histograms with KDE for Recency, Frequency, and Monetary metrics.

    Args:
        rfm_df: Customer RFM DataFrame.
        use_log: If True, plots log1p transformed values.

    Returns:
        plt.Figure: Matplotlib figure.
    """
    if rfm_df.empty:
        return _empty_figure()

    fig, axes = plt.subplots(1, 3, figsize=(14, 3.8))
    cols = ["recency", "frequency", "monetary"]
    titles = [
        "Recency (Days)" if not use_log else "log1p(Recency)",
        "Order Frequency" if not use_log else "log1p(Frequency)",
        "Monetary Spend (£)" if not use_log else "log1p(Monetary)",
    ]

    for i, col in enumerate(cols):
        data = np.log1p(rfm_df[col]) if use_log else rfm_df[col]
        sns.histplot(data, kde=True, ax=axes[i], color="#0288d1", bins=30)
        axes[i].set_title(titles[i], fontweight="bold")
        axes[i].set_xlabel(titles[i])
        axes[i].set_ylabel("Customer Count")

    scale_text = "Log-Transformed [log(x+1)]" if use_log else "Raw Empirical Scale"
    plt.suptitle(f"Customer Distribution Profiles ({scale_text})", fontsize=11, fontweight="bold", y=1.02)
    plt.tight_layout()
    return fig


def plot_clustering_diagnostics(metrics_df: pd.DataFrame) -> plt.Figure:
    """
    Plot Elbow Inertia and Silhouette score curves across K=2..10.

    Args:
        metrics_df: Clustering metrics DataFrame.

    Returns:
        plt.Figure: Matplotlib figure.
    """
    if metrics_df.empty:
        return _empty_figure()

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))

    # Inertia (Elbow)
    axes[0].plot(metrics_df["k"], metrics_df["inertia"], marker="o", color="#d32f2f", linewidth=2)
    axes[0].axvline(4, color="black", linestyle="--", alpha=0.7, label="Selected Choice (K=4)")
    axes[0].set_title("Elbow Method: Within-Cluster Sum of Squares (Inertia)", fontweight="bold")
    axes[0].set_xlabel("Number of Clusters (K)")
    axes[0].set_ylabel("Inertia (WCSS)")
    axes[0].set_xticks(metrics_df["k"])
    axes[0].legend()

    # Silhouette Score
    axes[1].plot(metrics_df["k"], metrics_df["silhouette_score"], marker="s", color="#1976d2", linewidth=2)
    axes[1].axvline(4, color="black", linestyle="--", alpha=0.7, label="Selected Choice (K=4)")
    axes[1].set_title("Silhouette Coefficient Across Candidate K", fontweight="bold")
    axes[1].set_xlabel("Number of Clusters (K)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].set_xticks(metrics_df["k"])
    axes[1].legend()

    plt.suptitle("K-Means Model Selection Diagnostics (K=2 through K=10)", fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    return fig
