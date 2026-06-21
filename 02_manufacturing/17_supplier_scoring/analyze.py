"""仕入先品質複合スコアリング — 重み付き合成スコア計算ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["supplier_id", "defect_rate", "delivery_rate", "price_variance"]
WEIGHTS = {"defect_rate": 0.5, "delivery_rate": 0.3, "price_variance": 0.2}


def _score_defect(v: float) -> float:
    return max(0.0, 100.0 - v * 10.0)


def _score_delivery(v: float) -> float:
    return float(min(100.0, v))


def _score_price(v: float) -> float:
    return max(0.0, 100.0 - v * 5.0)


def _verdict(score: float) -> str:
    if score >= 80:
        return "good"
    elif score >= 60:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["defect_rate", "delivery_rate", "price_variance"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["defect_rate", "delivery_rate", "price_variance"])

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    data = data.copy()
    data["defect_score"]    = data["defect_rate"].apply(_score_defect)
    data["delivery_score"]  = data["delivery_rate"].apply(_score_delivery)
    data["price_score"]     = data["price_variance"].apply(_score_price)
    data["composite_score"] = (
        data["defect_score"]   * WEIGHTS["defect_rate"]
        + data["delivery_score"] * WEIGHTS["delivery_rate"]
        + data["price_score"]    * WEIGHTS["price_variance"]
    )
    data["verdict"] = data["composite_score"].apply(_verdict)

    avg_score      = float(data["composite_score"].mean())
    best_supplier  = str(data.loc[data["composite_score"].idxmax(), "supplier_id"])
    worst_supplier = str(data.loc[data["composite_score"].idxmin(), "supplier_id"])

    return {
        "scored_df":      data,
        "avg_score":      avg_score,
        "best_supplier":  best_supplier,
        "worst_supplier": worst_supplier,
        "n_suppliers":    len(data),
        "verdict":        _verdict(avg_score),
    }
