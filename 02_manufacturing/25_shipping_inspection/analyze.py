"""出荷検査合否率・保留件数レポート — 合格率集計 + verdict ロジック。"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLS = ["month", "inspected", "passed", "hold_count"]

def _verdict(rate: float) -> str:
    if rate >= 99.0:
        return "good"
    elif rate >= 95.0:
        return "warning"
    return "alert"

def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")
    data = df.copy()
    for col in ["inspected","passed","hold_count"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["inspected","passed","hold_count"])
    data = data[data["inspected"] > 0].copy()
    if len(data) < 1:
        raise ValueError("有効なデータがありません。")
    total_inspected = int(data["inspected"].sum())
    total_passed    = int(data["passed"].sum())
    total_hold      = int(data["hold_count"].sum())
    n_months        = int(data["month"].nunique())
    pass_rate       = float(total_passed / total_inspected * 100)
    hold_rate       = float(total_hold / total_inspected * 100)
    avg_monthly_inspected = float(total_inspected / n_months)
    return {
        "result_df":              data,
        "total_inspected":        total_inspected,
        "avg_monthly_inspected":  avg_monthly_inspected,
        "pass_rate":              pass_rate,
        "hold_rate":              hold_rate,
        "total_hold":             total_hold,
        "verdict":                _verdict(pass_rate),
    }
