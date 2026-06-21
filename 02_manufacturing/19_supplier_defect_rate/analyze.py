"""協力会社別受入不良率月報 — 不良率計算 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["supplier", "month", "incoming_qty", "defect_qty"]


def _verdict(avg: float) -> str:
    if avg <= 1.0:
        return "good"
    elif avg <= 3.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["incoming_qty", "defect_qty"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["incoming_qty", "defect_qty"])
    data = data[data["incoming_qty"] > 0].copy()

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    data["defect_rate"] = data["defect_qty"] / data["incoming_qty"] * 100.0

    total_incoming = data["incoming_qty"].sum()
    total_defect   = data["defect_qty"].sum()
    avg_defect_rate = float(total_defect / total_incoming * 100.0)

    supplier_stats = data.groupby("supplier")[["defect_qty", "incoming_qty"]].sum()
    supplier_rates = supplier_stats["defect_qty"] / supplier_stats["incoming_qty"] * 100.0
    worst_supplier = str(supplier_rates.idxmax())
    best_supplier  = str(supplier_rates.idxmin())

    return {
        "result_df":       data,
        "avg_defect_rate": avg_defect_rate,
        "worst_supplier":  worst_supplier,
        "best_supplier":   best_supplier,
        "n_suppliers":     int(data["supplier"].nunique()),
        "verdict":         _verdict(avg_defect_rate),
    }
