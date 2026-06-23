import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["month", "site", "defect_rate", "cpk", "claim_count", "yield_rate"]

def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze multisite quality data and return comprehensive results.

    Args:
        df: DataFrame with columns [month, site, defect_rate, cpk, claim_count, yield_rate]

    Returns:
        dict with keys:
            - site_df: Aggregated metrics per site with overall score
            - trend_df: Monthly trend data (defect_rate by month and site)
            - best_site: Site name with highest score
            - worst_site: Site name with lowest score
            - avg_defect: Average defect rate across all data
            - n_sites: Number of unique sites
            - verdict: "good", "warning", or "alert" based on avg_defect
    """
    df = df.copy()

    # Site-level aggregation
    site_df = df.groupby("site").agg(
        avg_defect_rate=("defect_rate", "mean"),
        avg_cpk=("cpk", "mean"),
        total_claims=("claim_count", "sum"),
        avg_yield=("yield_rate", "mean"),
    ).reset_index()

    # Calculate composite score (0-100)
    # Higher score is better: low defect_rate, high cpk, low claim_count, high yield_rate
    max_defect = site_df["avg_defect_rate"].max()
    max_cpk = site_df["avg_cpk"].max()
    max_claims = site_df["total_claims"].max() + 1  # Avoid division by zero

    site_df["score"] = (
        (1 - site_df["avg_defect_rate"] / max_defect) * 25 +
        (site_df["avg_cpk"] / max_cpk) * 25 +
        (1 - site_df["total_claims"] / max_claims) * 25 +
        (site_df["avg_yield"] / 100) * 25
    )

    # Sort by score (descending)
    site_df = site_df.sort_values("score", ascending=False).reset_index(drop=True)

    # Monthly trend: defect_rate by month and site
    trend_df = df.groupby(["month", "site"])["defect_rate"].mean().reset_index()

    # Identify best and worst sites
    best_site = site_df.iloc[0]["site"]
    worst_site = site_df.iloc[-1]["site"]
    avg_defect = float(df["defect_rate"].mean())

    # Verdict based on average defect rate
    if avg_defect <= 0.5:
        verdict = "good"
    elif avg_defect <= 1.5:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "site_df": site_df,
        "trend_df": trend_df,
        "best_site": best_site,
        "worst_site": worst_site,
        "avg_defect": avg_defect,
        "n_sites": int(df["site"].nunique()),
        "verdict": verdict,
    }
