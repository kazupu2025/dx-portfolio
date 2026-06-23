import pandas as pd

REQUIRED_COLUMNS = ["capa_id", "open_date", "due_date", "close_date", "category"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["open_date"] = pd.to_datetime(df["open_date"])
    df["due_date"] = pd.to_datetime(df["due_date"])
    df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")

    total = len(df)
    completed = df["close_date"].notna().sum()
    completion_rate = completed / total * 100 if total > 0 else 0

    completed_df = df[df["close_date"].notna()].copy()
    on_time = (completed_df["close_date"] <= completed_df["due_date"]).sum()
    on_time_rate = on_time / completed if completed > 0 else 0
    on_time_rate_pct = on_time_rate * 100

    overdue = df[(df["close_date"].isna()) & (pd.Timestamp.now() > df["due_date"])].shape[0]

    category_df = df.groupby("category").size().reset_index(name="count")

    if completion_rate >= 90:
        verdict = "good"
    elif completion_rate >= 70:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "total": int(total),
        "completed": int(completed),
        "completion_rate": float(completion_rate),
        "on_time_rate": float(on_time_rate_pct),
        "overdue": int(overdue),
        "category_df": category_df,
        "verdict": verdict,
    }
