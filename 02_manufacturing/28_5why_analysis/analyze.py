"""なぜなぜ分析 原因カテゴリ別集計・再発率トレンド — 集計 + verdict ロジック。"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLS = ["month", "cause_category", "count", "recurrence"]

def _verdict(rate: float) -> str:
    if rate <= 10.0:
        return "good"
    elif rate <= 30.0:
        return "warning"
    return "alert"

def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")
    data = df.copy()
    for col in ["count", "recurrence"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["count","recurrence"])
    data = data[data["count"] >= 0].copy()
    if len(data) < 1:
        raise ValueError("有効なデータがありません。")
    total_count       = int(data["count"].sum())
    total_recurrence  = int(data["recurrence"].sum())
    n_months          = int(data["month"].nunique())
    avg_monthly_count = float(total_count / n_months)
    recurrence_rate   = float(total_recurrence / total_count * 100) if total_count > 0 else 0.0
    n_categories      = int(data["cause_category"].nunique())
    top_cause_category = str(data.groupby("cause_category")["count"].sum().idxmax())
    return {
        "result_df":          data,
        "total_count":        total_count,
        "avg_monthly_count":  avg_monthly_count,
        "recurrence_rate":    recurrence_rate,
        "top_cause_category": top_cause_category,
        "n_categories":       n_categories,
        "verdict":            _verdict(recurrence_rate),
    }
