"""CAPA 完了率・期限遵守率レポート — 完了率集計 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["month", "total", "completed", "on_time_completed"]


def _verdict(rate: float) -> str:
    if rate >= 90.0:
        return "good"
    elif rate >= 70.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["total", "completed", "on_time_completed"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["total", "completed", "on_time_completed"])
    data = data[data["total"] > 0].copy()

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    total_capas = int(data["total"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_capas = float(total_capas / n_months)

    total_completed = data["completed"].sum()
    total_ontime = data["on_time_completed"].sum()

    completion_rate = float(total_completed / total_capas * 100)
    ontime_rate = float(total_ontime / total_capas * 100)
    open_count = int(total_capas - total_completed)

    return {
        "result_df":         data,
        "total_capas":       total_capas,
        "avg_monthly_capas": avg_monthly_capas,
        "completion_rate":   completion_rate,
        "ontime_rate":       ontime_rate,
        "open_count":        open_count,
        "verdict":           _verdict(completion_rate),
    }
