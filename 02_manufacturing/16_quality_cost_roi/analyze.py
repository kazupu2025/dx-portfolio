"""品質コストROI分析 — PAFモデル月次ROI計算ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["month", "prevention_cost", "appraisal_cost", "failure_cost"]


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["prevention_cost", "appraisal_cost", "failure_cost"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["prevention_cost", "appraisal_cost", "failure_cost"])
    data = data.sort_values("month").reset_index(drop=True)

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    n = len(data)
    total_prevention = float(data["prevention_cost"].sum())
    total_appraisal  = float(data["appraisal_cost"].sum())
    total_failure    = float(data["failure_cost"].sum())

    latest_failure = float(data["failure_cost"].iloc[-1])
    latest_prev    = float(data["prevention_cost"].iloc[-1])
    latest_appr    = float(data["appraisal_cost"].iloc[-1])
    total_qc       = latest_prev + latest_appr + latest_failure
    failure_ratio  = latest_failure / total_qc if total_qc > 0 else 0.0

    roi_series: list[float] = []
    latest_roi: float | None = None

    if n >= 2:
        for i in range(1, n):
            delta  = float(data["failure_cost"].iloc[i - 1]) - float(data["failure_cost"].iloc[i])
            invest = float(data["prevention_cost"].iloc[i]) + float(data["appraisal_cost"].iloc[i])
            roi_series.append(delta / invest if invest > 0 else 0.0)
        latest_roi = roi_series[-1]
        if latest_roi > 1.0:
            verdict = "good"
        elif latest_roi > 0.0:
            verdict = "warning"
        else:
            verdict = "alert"
    else:
        if failure_ratio < 0.3:
            verdict = "good"
        elif failure_ratio < 0.5:
            verdict = "warning"
        else:
            verdict = "alert"

    return {
        "roi_series":       roi_series,
        "latest_roi":       latest_roi,
        "failure_ratio":    failure_ratio,
        "total_prevention": total_prevention,
        "total_appraisal":  total_appraisal,
        "total_failure":    total_failure,
        "n_months":         n,
        "verdict":          verdict,
    }
