import pandas as pd

REQUIRED_COLUMNS = ["date", "product", "lot_id", "result", "hold_flag"]

def analyze(df: pd.DataFrame) -> dict:
    """
    Analyze shipping inspection data and return weekly pass rates and hold counts.

    Args:
        df: DataFrame with columns: date, product, lot_id, result, hold_flag

    Returns:
        dict with keys: weekly_df, product_df, total, pass_rate, hold_count, verdict
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W").astype(str)

    total = len(df)
    passed = (df["result"] == "合格").sum()
    pass_rate = passed / total * 100 if total > 0 else 0
    hold_count = df["hold_flag"].sum()

    weekly_df = df.groupby("week").agg(
        total=("lot_id", "count"),
        passed=("result", lambda x: (x == "合格").sum()),
        hold=("hold_flag", "sum"),
    ).reset_index()
    weekly_df["pass_rate"] = weekly_df["passed"] / weekly_df["total"] * 100

    product_df = df.groupby("product").agg(
        total=("lot_id", "count"),
        passed=("result", lambda x: (x == "合格").sum()),
    ).reset_index()
    product_df["pass_rate"] = product_df["passed"] / product_df["total"] * 100

    if pass_rate >= 98:
        verdict = "good"
    elif pass_rate >= 95:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "weekly_df": weekly_df,
        "product_df": product_df,
        "total": int(total),
        "pass_rate": float(pass_rate),
        "hold_count": int(hold_count),
        "verdict": verdict,
    }
