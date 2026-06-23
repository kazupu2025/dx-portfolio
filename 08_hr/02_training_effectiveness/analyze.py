import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["employee_id","name","department","training_name","training_date",
                    "pre_score","post_score","training_cost","training_hours"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["training_date"] = pd.to_datetime(df["training_date"])
    df["score_improvement"] = df["post_score"] - df["pre_score"]
    df["improvement_rate"] = df["score_improvement"] / df["pre_score"] * 100
    df["cost_per_point"] = df["training_cost"] / df["score_improvement"].replace(0, np.nan)

    avg_improvement = df["score_improvement"].mean()
    avg_improvement_rate = df["improvement_rate"].mean()
    total_cost = df["training_cost"].sum()
    cost_efficiency = avg_improvement / (total_cost / len(df)) * 1000  # 1000円あたり改善点数

    # 研修別効果
    training_df = df.groupby("training_name").agg(
        count=("employee_id","count"),
        avg_pre=("pre_score","mean"),
        avg_post=("post_score","mean"),
        avg_improvement=("score_improvement","mean"),
        avg_improvement_rate=("improvement_rate","mean"),
        total_cost=("training_cost","sum"),
    ).reset_index().sort_values("avg_improvement", ascending=False)

    # 部署別効果
    dept_df = df.groupby("department").agg(
        count=("employee_id","count"),
        avg_improvement=("score_improvement","mean"),
        total_cost=("training_cost","sum"),
    ).reset_index().sort_values("avg_improvement", ascending=False)

    # 判定: 平均改善 ≥15→good, ≥8→warning, <8→alert
    if avg_improvement >= 15:
        verdict = "good"
    elif avg_improvement >= 8:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "training_df": training_df,
        "dept_df": dept_df,
        "avg_improvement": float(avg_improvement),
        "avg_improvement_rate": float(avg_improvement_rate),
        "total_cost": float(total_cost),
        "total_participants": int(len(df)),
        "cost_efficiency": float(cost_efficiency) if not np.isnan(cost_efficiency) else 0.0,
        "verdict": verdict,
    }
