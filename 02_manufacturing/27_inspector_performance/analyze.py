"""検査員別 検査数・不良検出率・精度レポート — 集計 + verdict ロジック。"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLS = ["month", "inspector", "inspected", "defects"]

def _verdict(rate: float) -> str:
    if rate >= 3.0:
        return "good"
    elif rate >= 1.0:
        return "warning"
    return "alert"

def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")
    data = df.copy()
    for col in ["inspected", "defects"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["inspected","defects"])
    data = data[data["inspected"] > 0].copy()
    if len(data) < 1:
        raise ValueError("有効なデータがありません。")
    total_inspected = int(data["inspected"].sum())
    total_defects   = int(data["defects"].sum())
    overall_defect_rate = float(total_defects / total_inspected * 100)
    n_inspectors    = int(data["inspector"].nunique())
    # 検査員ごとの不良検出率で最高を top_inspector とする
    insp_rate = data.groupby("inspector").apply(
        lambda g: g["defects"].sum() / g["inspected"].sum() * 100
    )
    top_inspector = str(insp_rate.idxmax())
    return {
        "result_df":           data,
        "total_inspected":     total_inspected,
        "total_defects":       total_defects,
        "overall_defect_rate": overall_defect_rate,
        "top_inspector":       top_inspector,
        "n_inspectors":        n_inspectors,
        "verdict":             _verdict(overall_defect_rate),
    }
