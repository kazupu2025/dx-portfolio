"""FMEA RPN 集計分析。"""
from __future__ import annotations
import pandas as pd

HIGH_RISK_THRESHOLD = 200

def _verdict(avg_rpn: float) -> str:
    if avg_rpn <= 100: return "good"
    elif avg_rpn <= 200: return "warning"
    return "alert"

def run_analysis(df: pd.DataFrame) -> dict:
    """df: fmea_items テーブルの DataFrame。"""
    if df is None or len(df) == 0:
        return {"df": pd.DataFrame(), "avg_rpn": 0.0, "max_rpn": 0,
                "high_risk_count": 0, "n_items": 0, "verdict": "good"}

    avg_rpn        = float(df["rpn"].mean())
    max_rpn        = int(df["rpn"].max())
    high_risk_count = int((df["rpn"] > HIGH_RISK_THRESHOLD).sum())

    return {
        "df":             df,
        "avg_rpn":        avg_rpn,
        "max_rpn":        max_rpn,
        "high_risk_count": high_risk_count,
        "n_items":        len(df),
        "verdict":        _verdict(avg_rpn),
    }
