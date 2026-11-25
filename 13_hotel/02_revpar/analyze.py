import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["month", "room_type", "total_rooms", "sold_rooms", "adr", "revenue"]


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze RevPAR and occupancy data.

    Args:
        df: DataFrame with columns [month, room_type, total_rooms, sold_rooms, adr, revenue]

    Returns:
        Dictionary containing:
        - monthly_df: Monthly aggregated data
        - room_df: Room type analysis sorted by RevPAR
        - avg_occ: Average occupancy rate (%)
        - avg_revpar: Average RevPAR
        - avg_adr: Average ADR
        - total_revenue: Total revenue
        - verdict: Health status (good/warning/alert)
    """
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])

    # Calculate occupancy and RevPAR
    df["occ"] = df["sold_rooms"] / df["total_rooms"] * 100
    df["revpar"] = df["revenue"] / df["total_rooms"]

    # Monthly aggregation
    monthly_df = df.groupby("month").agg(
        total_rooms=("total_rooms", "sum"),
        sold_rooms=("sold_rooms", "sum"),
        total_revenue=("revenue", "sum"),
    ).reset_index()
    monthly_df["occ"] = monthly_df["sold_rooms"] / monthly_df["total_rooms"] * 100
    monthly_df["revpar"] = monthly_df["total_revenue"] / monthly_df["total_rooms"]
    monthly_df["adr"] = monthly_df["total_revenue"] / monthly_df["sold_rooms"].replace(0, np.nan)

    # Room type analysis
    room_df = df.groupby("room_type").agg(
        avg_occ=("occ", "mean"),
        avg_adr=("adr", "mean"),
        avg_revpar=("revpar", "mean"),
        total_revenue=("revenue", "sum"),
    ).reset_index().sort_values("avg_revpar", ascending=False)

    # Calculate KPIs
    avg_occ = float(monthly_df["occ"].mean())
    avg_revpar = float(monthly_df["revpar"].mean())
    avg_adr = float(monthly_df["adr"].mean())
    total_revenue = float(df["revenue"].sum())

    # Verdict based on occupancy
    if avg_occ >= 70:
        verdict = "good"
    elif avg_occ >= 55:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "monthly_df": monthly_df,
        "room_df": room_df,
        "avg_occ": avg_occ,
        "avg_revpar": avg_revpar,
        "avg_adr": avg_adr,
        "total_revenue": total_revenue,
        "verdict": verdict,
    }
