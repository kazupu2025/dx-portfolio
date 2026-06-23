import pandas as pd

REQUIRED_COLUMNS = ["date", "change_type", "process", "description", "risk_level"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly_df = df.groupby(["month", "change_type"]).size().reset_index(name="count")
    type_df = df.groupby("change_type").size().reset_index(name="count").sort_values("count", ascending=False)
    process_df = df.groupby("process").size().reset_index(name="count").sort_values("count", ascending=False)

    high_risk_count = (df["risk_level"] == "高").sum()
    total_count = len(df)
    avg_monthly = df.groupby("month").size().mean()

    if avg_monthly <= 5:
        verdict = "good"
    elif avg_monthly <= 15:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "monthly_df": monthly_df,
        "type_df": type_df,
        "process_df": process_df,
        "total_count": int(total_count),
        "high_risk_count": int(high_risk_count),
        "avg_monthly": float(avg_monthly),
        "verdict": verdict,
    }
