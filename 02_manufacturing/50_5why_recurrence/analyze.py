import pandas as pd

REQUIRED_COLUMNS = ["date", "issue_id", "root_cause_category", "recurrence_flag"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    total = len(df)
    recurrence_count = int(df["recurrence_flag"].sum())
    recurrence_rate = recurrence_count / total * 100 if total > 0 else 0

    category_df = df.groupby("root_cause_category").agg(
        count=("issue_id", "count"),
        recurrence=("recurrence_flag", "sum"),
    ).reset_index()
    category_df["recurrence_rate"] = category_df["recurrence"] / category_df["count"] * 100
    category_df = category_df.sort_values("count", ascending=False)

    monthly_df = df.groupby("month").agg(
        count=("issue_id", "count"),
        recurrence=("recurrence_flag", "sum"),
    ).reset_index()
    monthly_df["recurrence_rate"] = monthly_df["recurrence"] / monthly_df["count"] * 100

    top_category = category_df.iloc[0]["root_cause_category"]

    if recurrence_rate <= 5:
        verdict = "good"
    elif recurrence_rate <= 15:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "category_df": category_df,
        "monthly_df": monthly_df,
        "total": int(total),
        "recurrence_count": recurrence_count,
        "recurrence_rate": float(recurrence_rate),
        "top_category": top_category,
        "verdict": verdict,
    }
