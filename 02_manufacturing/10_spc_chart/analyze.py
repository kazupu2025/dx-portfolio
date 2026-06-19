"""X-bar/R 管理図の制御限界計算。df は事前に1工程にフィルタ済みで渡す。"""
from __future__ import annotations
from collections import Counter
import pandas as pd

CONSTANTS: dict[int, dict[str, float]] = {
    2:  {"A2": 1.880, "D3": 0,     "D4": 3.267, "d2": 1.128},
    3:  {"A2": 1.023, "D3": 0,     "D4": 2.575, "d2": 1.693},
    4:  {"A2": 0.729, "D3": 0,     "D4": 2.282, "d2": 2.059},
    5:  {"A2": 0.577, "D3": 0,     "D4": 2.115, "d2": 2.326},
    6:  {"A2": 0.483, "D3": 0,     "D4": 2.004, "d2": 2.534},
    7:  {"A2": 0.419, "D3": 0.076, "D4": 1.924, "d2": 2.704},
    8:  {"A2": 0.373, "D3": 0.136, "D4": 1.864, "d2": 2.847},
    9:  {"A2": 0.337, "D3": 0.184, "D4": 1.816, "d2": 2.970},
    10: {"A2": 0.308, "D3": 0.223, "D4": 1.777, "d2": 3.078},
}


def run_analysis(df: pd.DataFrame, value_col: str, subgroup_col: str) -> dict:
    """
    X-bar/R 管理図の制御限界を計算する。

    Parameters
    ----------
    df : pd.DataFrame
        1工程分にフィルタ済みのデータフレーム
    value_col : str
        測定値の列名
    subgroup_col : str
        サブグループ識別子の列名（lot_no 等）

    Returns
    -------
    dict
        n, xbar_cl, xbar_ucl, xbar_lcl, r_cl, r_ucl, r_lcl, sigma,
        subgroups: list[{"label": str, "xbar": float, "r": float}]

    Raises
    ------
    ValueError
        サブグループ数 < 2 またはサブグループサイズ n が 2〜10 の範囲外
    """
    grouped = df.groupby(subgroup_col, sort=False)[value_col]
    xbar_s  = grouped.mean()
    r_s     = grouped.max() - grouped.min()
    count_s = grouped.count()

    if len(xbar_s) < 2:
        raise ValueError(
            f"Need at least 2 subgroups to calculate control limits, got {len(xbar_s)}"
        )

    n = Counter(count_s.tolist()).most_common(1)[0][0]
    if n not in CONSTANTS:
        raise ValueError(f"Subgroup size n={n} not supported (supported: 2-10)")

    c        = CONSTANTS[n]
    xbar_bar = float(xbar_s.mean())
    r_bar    = float(r_s.mean())

    return {
        "n":         n,
        "xbar_cl":   xbar_bar,
        "xbar_ucl":  xbar_bar + c["A2"] * r_bar,
        "xbar_lcl":  xbar_bar - c["A2"] * r_bar,
        "r_cl":      r_bar,
        "r_ucl":     c["D4"] * r_bar,
        "r_lcl":     c["D3"] * r_bar,
        "sigma":     r_bar / c["d2"] if r_bar > 0 else 0.0,
        "subgroups": [
            {"label": str(lbl), "xbar": float(xbar), "r": float(r)}
            for lbl, xbar, r in zip(xbar_s.index, xbar_s, r_s)
        ],
    }
