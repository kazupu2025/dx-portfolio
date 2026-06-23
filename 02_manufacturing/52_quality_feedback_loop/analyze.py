import pandas as pd

REQUIRED_COLUMNS = [
    "date",
    "product",
    "claim_type",
    "root_process",
    "action_taken",
    "before_rate",
    "after_rate",
    "action_date",
]


def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze quality feedback loop data.

    Args:
        df: DataFrame with columns:
            date, product, claim_type, root_process, action_taken,
            before_rate, after_rate, action_date

    Returns:
        Dictionary with analysis results:
        - df: processed dataframe with calculated columns
        - process_df: groupby root_process with aggregates
        - action_df: groupby action_taken with aggregates
        - product_df: groupby product with aggregates
        - avg_improvement: average improvement rate (%)
        - avg_lead_time: average lead time (days)
        - total_cases: number of records
        - verdict: "good" / "warning" / "alert"
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["action_date"] = pd.to_datetime(df["action_date"])

    # Calculate improvement rate: (before - after) / before * 100
    df["improvement_rate"] = (
        (df["before_rate"] - df["after_rate"]) / df["before_rate"] * 100
    )

    # Calculate lead time from claim date to action implementation
    df["lead_time_days"] = (df["action_date"] - df["date"]).dt.days

    avg_improvement = df["improvement_rate"].mean()
    avg_lead_time = df["lead_time_days"].mean()

    # Aggregate by root process
    process_df = (
        df.groupby("root_process")
        .agg(
            count=("product", "count"),
            avg_before=("before_rate", "mean"),
            avg_after=("after_rate", "mean"),
            avg_improvement=("improvement_rate", "mean"),
        )
        .reset_index()
        .sort_values("count", ascending=False)
    )

    # Aggregate by action taken
    action_df = (
        df.groupby("action_taken")
        .agg(
            count=("product", "count"),
            avg_improvement=("improvement_rate", "mean"),
        )
        .reset_index()
        .sort_values("avg_improvement", ascending=False)
    )

    # Aggregate by product
    product_df = (
        df.groupby("product")
        .agg(
            claim_count=("claim_type", "count"),
            avg_improvement=("improvement_rate", "mean"),
        )
        .reset_index()
        .sort_values("claim_count", ascending=False)
    )

    # Verdict based on average improvement rate
    if avg_improvement >= 50:
        verdict = "good"
    elif avg_improvement >= 25:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "process_df": process_df,
        "action_df": action_df,
        "product_df": product_df,
        "avg_improvement": float(avg_improvement),
        "avg_lead_time": float(avg_lead_time),
        "total_cases": int(len(df)),
        "verdict": verdict,
    }
