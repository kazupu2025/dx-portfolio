import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "month",
    "crop",
    "channel",
    "quantity_kg",
    "unit_price",
    "revenue",
    "grade",
]


def analyze(df: pd.DataFrame, config: dict = None) -> dict:
    """
    Analyze sales channel data and compute KPIs, channel breakdown, and verdicts.

    Args:
        df: DataFrame with columns as per REQUIRED_COLUMNS
        config: Configuration dict with thresholds (optional)

    Returns:
        dict with keys:
            - df: processed DataFrame
            - channel_df: channel-level aggregation
            - crop_df: crop-level aggregation
            - monthly_df: monthly trend data
            - channel_crop_df: channel x crop cross-tabulation
            - total_revenue: total sales in yen
            - avg_unit_price: average unit price
            - direct_sales_ratio: direct sales percentage
            - verdict: assessment ('good', 'warning', 'alert')
    """
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])

    # Default thresholds
    if config is None:
        config = {}
    direct_good = config.get("direct_sales_good", 0.30)
    direct_warning = config.get("direct_sales_warning", 0.15)

    # Channel-level aggregation
    channel_df = (
        df.groupby("channel")
        .agg(
            total_quantity=("quantity_kg", "sum"),
            total_revenue=("revenue", "sum"),
            avg_unit_price=("unit_price", "mean"),
            num_records=("channel", "count"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )

    # Crop-level aggregation
    crop_df = (
        df.groupby("crop")
        .agg(
            total_quantity=("quantity_kg", "sum"),
            total_revenue=("revenue", "sum"),
            avg_unit_price=("unit_price", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )

    # Monthly trends by channel
    monthly_df = (
        df.groupby("month")
        .agg(
            total_revenue=("revenue", "sum"),
            total_quantity=("quantity_kg", "sum"),
            avg_unit_price=("unit_price", "mean"),
        )
        .reset_index()
    )

    # Channel x Crop cross-tabulation (revenue)
    channel_crop_df = (
        df.groupby(["channel", "crop"])
        .agg(
            total_revenue=("revenue", "sum"),
            total_quantity=("quantity_kg", "sum"),
            avg_unit_price=("unit_price", "mean"),
        )
        .reset_index()
    )

    # KPI calculations
    total_revenue = float(df["revenue"].sum())
    avg_unit_price = float(df["unit_price"].mean())

    # Direct sales ratio (高単価チャネル活用度)
    direct_sales_revenue = float(
        df[df["channel"] == "直販"]["revenue"].sum()
    )
    direct_sales_ratio = (
        direct_sales_revenue / total_revenue
        if total_revenue > 0
        else 0
    )

    # Verdict logic: direct_sales_ratio >= 30% → good, >= 15% → warning, < 15% → alert
    if direct_sales_ratio >= direct_good:
        verdict = "good"
    elif direct_sales_ratio >= direct_warning:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "channel_df": channel_df,
        "crop_df": crop_df,
        "monthly_df": monthly_df,
        "channel_crop_df": channel_crop_df,
        "total_revenue": total_revenue,
        "avg_unit_price": avg_unit_price,
        "direct_sales_ratio": direct_sales_ratio,
        "verdict": verdict,
    }
