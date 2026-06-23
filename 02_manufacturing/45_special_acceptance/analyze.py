import pandas as pd

REQUIRED_COLUMNS = ["date", "lot_id", "reason_category", "approver", "quantity"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly_df = df.groupby("month").agg(
        count=("lot_id", "count"),
        total_quantity=("quantity", "sum"),
    ).reset_index()

    reason_df = df.groupby("reason_category").agg(
        count=("lot_id", "count"),
        total_quantity=("quantity", "sum"),
    ).reset_index().sort_values("count", ascending=False)

    avg_monthly = monthly_df["count"].mean()
    top_reason = reason_df.iloc[0]["reason_category"]

    if avg_monthly <= 3:
        verdict = "good"
    elif avg_monthly <= 10:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "monthly_df": monthly_df,
        "reason_df": reason_df,
        "total_count": int(len(df)),
        "avg_monthly": float(avg_monthly),
        "top_reason": top_reason,
        "verdict": verdict,
    }
