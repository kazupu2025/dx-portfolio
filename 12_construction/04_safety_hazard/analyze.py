import pandas as pd
import numpy as np
from datetime import datetime

REQUIRED_COLUMNS = [
    "date", "project_id", "location", "category", "severity",
    "description", "corrective_action", "reporter", "resolved"
]

def analyze(df: pd.DataFrame) -> dict:
    """
    安全管理・ヒヤリハット集計分析

    Args:
        df: 入力DataFrame（sample_safety.csvと同じスキーマ）

    Returns:
        dict: 以下のキーを含む分析結果
            - df: 処理済みの詳細データ
            - total_incidents: 総インシデント件数
            - critical_count: 重大事案件数
            - unresolved_count: 未解決件数
            - resolution_rate: 解決率（%）
            - verdict: 判定（good/warning/alert）
            - category_stats: カテゴリ別集計（DataFrame）
            - severity_stats: 重篤度別集計（DataFrame）
            - project_stats: プロジェクト別集計（DataFrame）
            - monthly_trend: 月別発生件数（DataFrame）
    """
    df = df.copy()

    # 日付列の変換
    df["date"] = pd.to_datetime(df["date"])

    # resolved を boolean に変換
    if df["resolved"].dtype == "object":
        df["resolved"] = df["resolved"].astype(str).str.lower().isin(["true", "1", "yes"])

    # 全体統計
    total_incidents = len(df)
    critical_count = len(df[df["severity"] == "重大"])
    unresolved_count = len(df[df["resolved"] == False])
    resolution_rate = ((total_incidents - unresolved_count) / total_incidents * 100) if total_incidents > 0 else 0.0

    # ── 判定ロジック ──
    # good: 重大事案=0 かつ 解決率≥90%
    # warning: 重大事案≤2 かつ 解決率≥70%
    # alert: その他
    if critical_count == 0 and resolution_rate >= 90:
        verdict = "good"
    elif critical_count <= 2 and resolution_rate >= 70:
        verdict = "warning"
    else:
        verdict = "alert"

    # ── カテゴリ別集計 ──
    category_stats = df.groupby("category").agg(
        件数=("category", "count"),
        重大=("severity", lambda x: (x == "重大").sum()),
        軽微=("severity", lambda x: (x == "軽微").sum()),
        ヒヤリハット=("severity", lambda x: (x == "ヒヤリハット").sum()),
        未解決=("resolved", lambda x: (~x).sum()),
    ).reset_index()

    # ── 重篤度別集計 ──
    severity_stats = df.groupby("severity").agg(
        件数=("severity", "count"),
        未解決=("resolved", lambda x: (~x).sum()),
    ).reset_index()
    # ソート順序を指定
    severity_order = ["ヒヤリハット", "軽微", "重大"]
    severity_stats["severity"] = pd.Categorical(
        severity_stats["severity"], categories=severity_order, ordered=True
    )
    severity_stats = severity_stats.sort_values("severity").reset_index(drop=True)

    # ── プロジェクト別集計 ──
    project_stats = df.groupby("project_id").agg(
        件数=("project_id", "count"),
        重大=("severity", lambda x: (x == "重大").sum()),
        未解決=("resolved", lambda x: (~x).sum()),
    ).reset_index()
    project_stats["解決率"] = (
        (project_stats["件数"] - project_stats["未解決"]) / project_stats["件数"] * 100
    ).round(1)
    project_stats = project_stats.sort_values("重大", ascending=False).reset_index(drop=True)

    # ── 月別発生トレンド ──
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    monthly_trend = df.groupby("year_month").agg(
        発生件数=("year_month", "count"),
        重大=("severity", lambda x: (x == "重大").sum()),
        軽微=("severity", lambda x: (x == "軽微").sum()),
        ヒヤリハット=("severity", lambda x: (x == "ヒヤリハット").sum()),
    ).reset_index()

    return {
        "df": df,
        "total_incidents": int(total_incidents),
        "critical_count": int(critical_count),
        "unresolved_count": int(unresolved_count),
        "resolution_rate": float(resolution_rate),
        "verdict": verdict,
        "category_stats": category_stats,
        "severity_stats": severity_stats,
        "project_stats": project_stats,
        "monthly_trend": monthly_trend,
    }
