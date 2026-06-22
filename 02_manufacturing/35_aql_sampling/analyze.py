"""AQL/受入サンプリング計画最適化 — OC曲線 + AQL合格確率 + verdict。"""
from __future__ import annotations
import pandas as pd
import numpy as np
from scipy.stats import binom

REQUIRED_COLS = ["lot_size", "sample_size", "acceptance_number", "aql_pct"]
OC_POINTS = 50


def _verdict(avg_pa: float) -> str:
    if avg_pa >= 0.95:
        return "good"
    elif avg_pa >= 0.90:
        return "warning"
    return "alert"


def _oc_curve(n: int, c: int, aql_pct: float) -> dict:
    """OC曲線データ（p_range × Pa）を返す。"""
    p_max = min(1.0, aql_pct * 20 / 100)
    p_range = np.linspace(0, p_max, OC_POINTS)
    pa_vals = [float(binom.cdf(c, n, p)) for p in p_range]
    return {"p_range": p_range.tolist(), "pa_values": pa_vals}


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["lot_size", "sample_size", "acceptance_number"]:
        data[col] = pd.to_numeric(data[col], errors="coerce").astype("Int64")
    data["aql_pct"] = pd.to_numeric(data["aql_pct"], errors="coerce")
    data = data.dropna(subset=REQUIRED_COLS)

    rows = []
    oc_curves = []
    for _, row in data.iterrows():
        n   = int(row["sample_size"])
        c   = int(row["acceptance_number"])
        aql = float(row["aql_pct"])
        rql = aql * 10

        pa_at_aql = float(binom.cdf(c, n, aql / 100))
        pa_at_rql = float(binom.cdf(c, n, rql / 100))
        protection_score = pa_at_aql - pa_at_rql

        rows.append({
            "lot_size":          int(row["lot_size"]),
            "sample_size":       n,
            "acceptance_number": c,
            "aql_pct":           aql,
            "pa_at_aql":         round(pa_at_aql, 6),
            "pa_at_rql":         round(pa_at_rql, 6),
            "protection_score":  round(protection_score, 6),
        })
        oc_curves.append(_oc_curve(n, c, aql))

    result_df = pd.DataFrame(rows)
    avg_pa_at_aql       = float(result_df["pa_at_aql"].mean())
    avg_protection_score = float(result_df["protection_score"].mean())
    n_plans             = len(result_df)

    best_plan = int(result_df.loc[result_df["protection_score"].idxmax(), "lot_size"])

    return {
        "result_df":           result_df,
        "avg_pa_at_aql":       round(avg_pa_at_aql, 6),
        "avg_protection_score": round(avg_protection_score, 6),
        "best_plan":           best_plan,
        "n_plans":             n_plans,
        "verdict":             _verdict(avg_pa_at_aql),
        "oc_curves":           oc_curves,
    }
