import pandas as pd

REQUIRED_COLUMNS = ["date", "customer", "category", "severity", "status"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly_df = df.groupby("month").size().reset_index(name="count")
    category_df = df.groupby("category").size().reset_index(name="count").sort_values("count", ascending=False)
    customer_df = df.groupby("customer").size().reset_index(name="count").sort_values("count", ascending=False)

    total_count = len(df)
    open_count = (df["status"] != "完了").sum()
    avg_monthly = monthly_df["count"].mean()

    if avg_monthly <= 5:
        verdict = "good"
    elif avg_monthly <= 10:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "monthly_df": monthly_df,
        "category_df": category_df,
        "customer_df": customer_df,
        "total_count": int(total_count),
        "open_count": int(open_count),
        "avg_monthly": float(avg_monthly),
        "top_category": category_df.iloc[0]["category"],
        "verdict": verdict,
    }
