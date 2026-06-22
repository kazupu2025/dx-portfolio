"""仕入先品質複合スコアリング — 重み付きスコアカード方式。"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLS = ["supplier", "defect_rate", "cpk", "claim_count"]

# スコアリング重み
W_DEFECT = 0.4
W_CPK    = 0.4
W_CLAIM  = 0.2

# スコアリング基準
DEFECT_MAX_PCT = 10.0   # これ以上で0点
CPK_TARGET     = 1.67   # これで100点
CLAIM_MAX      = 20     # これ以上で0点


def _defect_score(rate: float) -> float:
    return max(0.0, 100.0 - rate * (100.0 / DEFECT_MAX_PCT))


def _cpk_score(cpk: float) -> float:
    return min(100.0, max(0.0, cpk / CPK_TARGET * 100.0))


def _claim_score(count: float) -> float:
    return max(0.0, 100.0 - count * (100.0 / CLAIM_MAX))


def _verdict(avg_score: float) -> str:
    if avg_score >= 80.0:
        return "good"
    elif avg_score >= 60.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["defect_rate", "cpk", "claim_count"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["defect_rate", "cpk", "claim_count"])

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    data["defect_score"] = data["defect_rate"].apply(_defect_score).round(2)
    data["cpk_score"]    = data["cpk"].apply(_cpk_score).round(2)
    data["claim_score"]  = data["claim_count"].apply(_claim_score).round(2)
    data["total_score"]  = (
        data["defect_score"] * W_DEFECT +
        data["cpk_score"]    * W_CPK    +
        data["claim_score"]  * W_CLAIM
    ).round(2)

    avg_total_score = float(data["total_score"].mean())
    best_supplier   = str(data.loc[data["total_score"].idxmax(), "supplier"])
    worst_supplier  = str(data.loc[data["total_score"].idxmin(), "supplier"])
    n_suppliers     = int(len(data))

    return {
        "result_df":       data,
        "avg_total_score": avg_total_score,
        "best_supplier":   best_supplier,
        "worst_supplier":  worst_supplier,
        "n_suppliers":     n_suppliers,
        "verdict":         _verdict(avg_total_score),
    }
