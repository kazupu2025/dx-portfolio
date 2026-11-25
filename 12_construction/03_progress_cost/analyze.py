import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "project_id", "project_name", "phase", "planned_start", "planned_end",
    "actual_start", "actual_end", "planned_cost", "actual_cost", "progress_pct"
]

def analyze(df: pd.DataFrame) -> dict:
    """
    工程進捗・原価差異分析

    Args:
        df: 入力DataFrame（sample_progress_cost.csvと同じスキーマ）

    Returns:
        dict: 以下のキーを含む分析結果
            - df: 計算済みの詳細データ
            - project_df: プロジェクト別集計
            - total_planned: 計画総額
            - total_actual: 実績総額
            - overall_variance_pct: 総原価差異率（%）
            - avg_delay: 平均開始遅延日数
            - avg_progress: 平均進捗率（%）
            - verdict: 判定（good/warning/alert）
    """
    df = df.copy()

    # 日付列の変換
    for col in ["planned_start", "planned_end", "actual_start"]:
        df[col] = pd.to_datetime(df[col])
    df["actual_end"] = pd.to_datetime(df["actual_end"], errors="coerce")

    # 工期遅延日数の計算
    df["start_delay"] = (df["actual_start"] - df["planned_start"]).dt.days
    df["end_delay"] = (df["actual_end"] - df["planned_end"]).dt.days

    # 原価差異の計算
    df["cost_variance"] = df["actual_cost"] - df["planned_cost"]
    df["cost_variance_pct"] = df["cost_variance"] / df["planned_cost"] * 100

    # プロジェクト別集計
    project_df = df.groupby(["project_id", "project_name"]).agg(
        total_planned=("planned_cost", "sum"),
        total_actual=("actual_cost", "sum"),
        avg_progress=("progress_pct", "mean"),
        avg_start_delay=("start_delay", "mean"),
        phase_count=("phase", "count"),
    ).reset_index()

    project_df["total_variance_pct"] = (
        (project_df["total_actual"] - project_df["total_planned"]) / project_df["total_planned"] * 100
    )
    project_df = project_df.sort_values("total_variance_pct", ascending=False)

    # 全体統計
    total_planned = float(df["planned_cost"].sum())
    total_actual = float(df["actual_cost"].sum())
    overall_variance_pct = (total_actual - total_planned) / total_planned * 100
    avg_delay = float(df["start_delay"].mean())
    avg_progress = float(df["progress_pct"].mean())

    # 判定ロジック: 原価超過率 ≤5% → good, ≤15% → warning, >15% → alert
    if overall_variance_pct <= 5:
        verdict = "good"
    elif overall_variance_pct <= 15:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "df": df,
        "project_df": project_df,
        "total_planned": total_planned,
        "total_actual": total_actual,
        "overall_variance_pct": float(overall_variance_pct),
        "avg_delay": avg_delay,
        "avg_progress": avg_progress,
        "verdict": verdict,
    }
