import pandas as pd

REQUIRED_COLUMNS = ["month", "cost_category", "amount"]
FAILURE_CATEGORIES = ["内部失敗コスト", "外部失敗コスト"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()

    category_df = df.groupby("cost_category")["amount"].sum().reset_index()
    category_df.columns = ["cost_category", "total_amount"]

    total = category_df["total_amount"].sum()
    failure_total = category_df[category_df["cost_category"].isin(FAILURE_CATEGORIES)]["total_amount"].sum()
    failure_ratio = failure_total / total * 100 if total > 0 else 0

    trend_df = df.pivot_table(index="month", columns="cost_category", values="amount", aggfunc="sum", fill_value=0).reset_index()

    if failure_ratio <= 30:
        verdict = "good"
    elif failure_ratio <= 50:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "category_df": category_df,
        "trend_df": trend_df,
        "total_cost": float(total),
        "failure_ratio": float(failure_ratio),
        "verdict": verdict,
    }
