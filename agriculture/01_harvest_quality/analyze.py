import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "month",
    "crop",
    "field_area_ha",
    "yield_kg",
    "grade_a_rate",
    "grade_b_rate",
    "grade_c_rate",
    "avg_brix",
    "moisture_pct",
]


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze harvest data and compute KPIs, trends, and quality verdicts.

    Args:
        df: DataFrame with columns as per REQUIRED_COLUMNS

    Returns:
        dict with keys:
            - df: processed DataFrame with yield_per_ha column added
            - crop_df: crop-level aggregation (yield, avg_yield_per_ha, grade_a, brix, area)
            - monthly_df: monthly aggregation (total_yield, avg_grade_a, avg_brix)
            - total_yield: total harvest in kg
            - avg_grade_a: average A-grade rate (%)
            - avg_brix: average sugar content (Brix)
            - verdict: quality assessment ('good', 'warning', 'alert')
    """
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])
    df["yield_per_ha"] = df["yield_kg"] / df["field_area_ha"]

    # Crop-level aggregation
    crop_df = (
        df.groupby("crop")
        .agg(
            total_yield=("yield_kg", "sum"),
            avg_yield_per_ha=("yield_per_ha", "mean"),
            avg_grade_a=("grade_a_rate", "mean"),
            avg_brix=("avg_brix", "mean"),
            area=("field_area_ha", "mean"),
        )
        .reset_index()
        .sort_values("avg_yield_per_ha", ascending=False)
    )

    # Monthly trends
    monthly_df = (
        df.groupby("month")
        .agg(
            total_yield=("yield_kg", "sum"),
            avg_grade_a=("grade_a_rate", "mean"),
            avg_brix=("avg_brix", "mean"),
        )
        .reset_index()
    )

    total_yield = float(df["yield_kg"].sum())
    avg_grade_a = float(df["grade_a_rate"].mean())
    avg_brix = float(df["avg_brix"].mean())

    # Verdict logic: A-grade rate >= 75% → good, >= 60% → warning, < 60% → alert
    if avg_grade_a >= 75:
        verdict = "good"
    elif avg_grade_a >= 60:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "crop_df": crop_df,
        "monthly_df": monthly_df,
        "total_yield": total_yield,
        "avg_grade_a": avg_grade_a,
        "avg_brix": avg_brix,
        "verdict": verdict,
    }
