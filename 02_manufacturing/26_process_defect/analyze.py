"""工程別不良コード頻度・月次トレンド — 集計 + verdict ロジック。"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLS = ["month", "process", "defect_code", "count"]

def _verdict(avg: float) -> str:
    if avg <= 10.0:
        return "good"
    elif avg <= 30.0:
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
    n_months    = int(data["month"].nunique())
    avg_monthly_count = float(total_count / n_months)
    top_process    = str(data.groupby("process")["count"].sum().idxmax())
    top_defect_code = str(data.groupby("defect_code")["count"].sum().idxmax())
    return {
        "result_df":          data,
        "total_count":        total_count,
        "avg_monthly_count":  avg_monthly_count,
        "top_process":        top_process,
        "top_defect_code":    top_defect_code,
        "verdict":            _verdict(avg_monthly_count),
    }
