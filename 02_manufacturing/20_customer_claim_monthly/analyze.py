"""顧客クレーム件数・原因分類 月次集計 — クレーム集計 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["customer", "month", "category", "count"]


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

    total_claims = int(data["count"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_claims = float(total_claims / n_months)

    category_totals = data.groupby("category")["count"].sum()
    top_category = str(category_totals.idxmax())

    customer_totals = data.groupby("customer")["count"].sum()
    worst_customer = str(customer_totals.idxmax())

    return {
        "result_df":          data,
        "total_claims":       total_claims,
        "avg_monthly_claims": avg_monthly_claims,
        "top_category":       top_category,
        "worst_customer":     worst_customer,
        "n_customers":        int(data["customer"].nunique()),
        "verdict":            _verdict(avg_monthly_claims),
    }
