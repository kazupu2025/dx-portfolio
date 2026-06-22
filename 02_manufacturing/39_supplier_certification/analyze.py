"""サプライヤー品質認定 — 集計分析。"""
from __future__ import annotations
import pandas as pd


def _verdict(avg: float) -> str:
    """avg_total_scoreから verdict を決定（高いほどgood）。"""
    if avg >= 80:
        return "good"
    elif avg >= 60:
        return "warning"
    return "alert"


def run_analysis(latest_df: pd.DataFrame, all_assessments_df: pd.DataFrame) -> dict:
    """
    最新評価DataFrameを分析し、7キーの結果を返す。

    Returns:
        {
            "suppliers_df": pd.DataFrame,
            "avg_total_score": float,
            "certified_count": int,
            "n_suppliers": int,
            "n_assessments": int,
            "top_supplier": str,
            "verdict": str,
        }
    """
    # 空チェック
    if latest_df is None or len(latest_df) == 0:
        return {
            "suppliers_df": pd.DataFrame(),
            "avg_total_score": 0.0,
            "certified_count": 0,
            "n_suppliers": 0,
            "n_assessments": 0,
            "top_supplier": "",
            "verdict": "good",
        }

    df = latest_df.copy()
    df["total_score"] = pd.to_numeric(df["total_score"], errors="coerce").fillna(0)

    # 集計
    avg_total = float(df["total_score"].mean())
    certified_count = int((df["certification"] == "認定").sum())
    n_suppliers = len(df)
    n_assessments = len(all_assessments_df) if all_assessments_df is not None else 0

    # top_supplier
    if len(df) > 0:
        top_idx = df["total_score"].idxmax()
        top_row = df.loc[top_idx]
        top_supplier = str(top_row["name"])
    else:
        top_supplier = ""

    return {
        "suppliers_df": df,
        "avg_total_score": avg_total,
        "certified_count": certified_count,
        "n_suppliers": n_suppliers,
        "n_assessments": n_assessments,
        "top_supplier": top_supplier,
        "verdict": _verdict(avg_total),
    }
