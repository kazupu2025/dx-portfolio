"""工程間品質相関分析 — Pearson相関 + 有意検定。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats

REQUIRED_COLS = ["month", "defect_rate"]
TARGET_COL    = "defect_rate"


def _verdict(max_abs_corr: float) -> str:
    if max_abs_corr >= 0.7:
        return "good"
    elif max_abs_corr >= 0.4:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    param_cols = [c for c in df.columns if c not in ("month", TARGET_COL)]
    if not param_cols:
        raise ValueError("工程パラメータ列が見つかりません（defect_rate以外の数値列が必要です）。")

    data = df.copy()
    for col in param_cols + [TARGET_COL]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=param_cols + [TARGET_COL])

    if len(data) < 3:
        raise ValueError("相関計算には最低3行のデータが必要です。")

    n_months = int(data["month"].nunique())
    corr_df  = data[param_cols + [TARGET_COL]].corr()

    rows = []
    for col in param_cols:
        r, p = stats.pearsonr(data[col], data[TARGET_COL])
        rows.append({"parameter": col, "correlation": round(float(r), 4), "p_value": round(float(p), 4)})

    target_corr = pd.DataFrame(rows).set_index("parameter")
    abs_corrs   = target_corr["correlation"].abs()
    max_abs_corr  = float(abs_corrs.max())
    strongest_param = str(abs_corrs.idxmax())

    return {
        "corr_df":       corr_df,
        "target_corr":   target_corr.reset_index(),
        "max_abs_corr":  max_abs_corr,
        "strongest_param": strongest_param,
        "n_months":      n_months,
        "verdict":       _verdict(max_abs_corr),
    }
