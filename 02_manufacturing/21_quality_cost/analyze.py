"""品質コスト明細集計（4分類）— コスト集計 + 損失コスト比率 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["month", "category", "amount"]
FAILURE_CATEGORIES = ["内部損失コスト", "外部損失コスト"]


def _verdict(ratio: float) -> str:
    if ratio <= 30.0:
        return "good"
    elif ratio <= 50.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    data = data.dropna(subset=["amount"])
    data = data[data["amount"] >= 0].copy()

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    total_cost = int(data["amount"].sum())
    n_months = int(data["month"].nunique())
    avg_monthly_cost = float(total_cost / n_months)

    cat_totals = data.groupby("category")["amount"].sum()
    cost_by_category = {str(k): int(v) for k, v in cat_totals.items()}
    dominant_category = str(cat_totals.idxmax())

    failure_amount = sum(cost_by_category.get(cat, 0) for cat in FAILURE_CATEGORIES)
    failure_ratio = float(failure_amount / total_cost * 100) if total_cost > 0 else 0.0

    return {
        "result_df":         data,
        "total_cost":        total_cost,
        "avg_monthly_cost":  avg_monthly_cost,
        "cost_by_category":  cost_by_category,
        "dominant_category": dominant_category,
        "failure_ratio":     failure_ratio,
        "verdict":           _verdict(failure_ratio),
    }
