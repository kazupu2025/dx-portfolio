"""4M変更台帳 集計・変更種別推移 — 集計 + verdict ロジック。"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLS = ["month", "change_type", "count"]

def _verdict(avg: float) -> str:
    if avg <= 5.0:
        return "good"
    elif avg <= 15.0:
        return "warning"
    return "alert"

def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")
    data = df.copy()
    data["count"] = pd.to_numeric(data["count"], errors="coerce")
    data = data.dropna(subset=["count"])
    data = data[data["count"] >= 0].copy()
    if len(data) < 1:
        raise ValueError("有効なデータがありません。")
    total_count = int(data["count"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_count = float(total_count / n_months)
    ct_totals = data.groupby("change_type")["count"].sum()
    top_change_type = str(ct_totals.idxmax())
    n_types = int(data["change_type"].nunique())
    return {
        "result_df":         data,
        "total_count":       total_count,
        "avg_monthly_count": avg_monthly_count,
        "top_change_type":   top_change_type,
        "n_types":           n_types,
        "verdict":           _verdict(avg_monthly_count),
    }
