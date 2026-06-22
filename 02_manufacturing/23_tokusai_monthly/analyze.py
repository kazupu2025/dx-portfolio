"""特採件数・理由別集計・月次推移 -- 集計 + verdict logic."""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["month", "reason", "count"]


def _verdict(avg: float) -> str:
    if avg <= 3.0:
        return "good"
    elif avg <= 10.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing: {', '.join(missing)}")

    data = df.copy()
    data["count"] = pd.to_numeric(data["count"], errors="coerce")
    data = data.dropna(subset=["count"])
    data = data[data["count"] >= 0].copy()

    if len(data) < 1:
        raise ValueError("No valid data available")

    total_count = int(data["count"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_count = float(total_count / n_months)

    reason_totals = data.groupby("reason")["count"].sum()
    top_reason = str(reason_totals.idxmax())
    n_reasons = int(data["reason"].nunique())

    return {
        "result_df":         data,
        "total_count":       total_count,
        "avg_monthly_count": avg_monthly_count,
        "top_reason":        top_reason,
        "n_reasons":         n_reasons,
        "verdict":           _verdict(avg_monthly_count),
    }
