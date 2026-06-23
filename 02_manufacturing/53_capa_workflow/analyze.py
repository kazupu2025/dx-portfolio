import pandas as pd
from db import get_all, STATUSES, init_db

def analyze() -> dict:
    init_db()
    items = get_all()
    if not items:
        return {"total": 0, "completed": 0, "status_df": pd.DataFrame(), "completion_rate": 0.0, "overdue_count": 0, "verdict": "good"}

    df = pd.DataFrame(items)
    total = len(df)
    completed = (df["status"] == "完了").sum()
    completion_rate = completed / total * 100

    status_df = df.groupby("status").size().reset_index(name="count")
    # 順序を固定
    status_order = pd.CategoricalDtype(categories=STATUSES, ordered=True)
    status_df["status"] = status_df["status"].astype(status_order)
    status_df = status_df.sort_values("status")

    overdue_count = 0
    if "due_date" in df.columns:
        import datetime
        today = datetime.date.today().isoformat()
        overdue_count = ((df["due_date"] < today) & (df["status"] != "完了") & df["due_date"].notna()).sum()

    if completion_rate >= 70:
        verdict = "good"
    elif completion_rate >= 40:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "total": int(total),
        "completed": int(completed),
        "completion_rate": float(completion_rate),
        "status_df": status_df,
        "overdue_count": int(overdue_count),
        "verdict": verdict,
    }
