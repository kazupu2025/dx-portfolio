import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "date",
    "crop",
    "product_name",
    "category",
    "quantity_kg",
    "unit_price",
    "total_cost",
    "field_area_ha",
    "application_reason",
]


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze pesticide and fertilizer cost data and compute KPIs, verdicts.

    Args:
        df: DataFrame with columns as per REQUIRED_COLUMNS

    Returns:
        dict with keys:
            - df: processed DataFrame with cost_per_ha column added
            - category_df: cost aggregation by category (total_cost, count, avg_unit_price)
            - crop_df: cost aggregation by crop (total_cost, avg_cost_per_ha, category_count)
            - monthly_df: monthly cost aggregation (total_cost, avg_cost_per_ha)
            - total_cost: total pesticide & fertilizer cost
            - cost_per_ha: average cost per hectare
            - category_count: number of distinct categories used
            - verdict: cost assessment ('good', 'warning', 'alert')
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["cost_per_ha"] = df["total_cost"] / df["field_area_ha"]

    # Category-level aggregation
    category_df = (
        df.groupby("category")
        .agg(
            total_cost=("total_cost", "sum"),
            count=("product_name", "count"),
            avg_unit_price=("unit_price", "mean"),
        )
        .reset_index()
        .sort_values("total_cost", ascending=False)
    )

    # Crop-level aggregation
    crop_df = (
        df.groupby("crop")
        .agg(
            total_cost=("total_cost", "sum"),
            avg_cost_per_ha=("cost_per_ha", "mean"),
            category_count=("category", "nunique"),
            field_area_ha=("field_area_ha", "mean"),
        )
        .reset_index()
        .sort_values("avg_cost_per_ha", ascending=False)
    )

    # Monthly trends
    monthly_df = (
        df.groupby("date")
        .agg(
            total_cost=("total_cost", "sum"),
            avg_cost_per_ha=("cost_per_ha", "mean"),
        )
        .reset_index()
    )

    total_cost = float(df["total_cost"].sum())
    cost_per_ha = float(df["cost_per_ha"].mean())
    category_count = int(df["category"].nunique())

    # Verdict logic: cost_per_ha <= 50000 → good, <= 80000 → warning, > 80000 → alert
    if cost_per_ha <= 50000:
        verdict = "good"
    elif cost_per_ha <= 80000:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "category_df": category_df,
        "crop_df": crop_df,
        "monthly_df": monthly_df,
        "total_cost": total_cost,
        "cost_per_ha": cost_per_ha,
        "category_count": category_count,
        "verdict": verdict,
    }
