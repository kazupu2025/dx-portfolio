"""ゲージR&R（MSA）ANOVA 2要因分析。"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from scipy import stats


def run_analysis(
    df: pd.DataFrame,
    value_col: str,
    part_col: str,
    operator_col: str,
) -> dict:
    """
    2要因（Part × Operator）ANOVA によるゲージR&R 分析。

    Parameters
    ----------
    df : pd.DataFrame
        ロング形式測定データ
    value_col : str
        測定値列名
    part_col : str
        部品識別子列名
    operator_col : str
        作業者列名

    Returns
    -------
    dict
        ev, av, int_, pv, grr, tv, grr_pct, ev_pct, av_pct, int_pct, pv_pct,
        ndc, verdict, anova_table

    Raises
    ------
    ValueError
        作業者数 < 2、部品数 < 2、または繰り返し数 < 2 の場合
    """
    n_ops   = df[operator_col].nunique()
    n_parts = df[part_col].nunique()

    if n_ops < 2:
        raise ValueError(f"Need at least 2 operators, got {n_ops}")
    if n_parts < 2:
        raise ValueError(f"Need at least 2 parts, got {n_parts}")

    n_trials = int(df.groupby([part_col, operator_col])[value_col].count().min())
    if n_trials < 2:
        raise ValueError(f"Need at least 2 trials per cell, got {n_trials}")

    grand_mean = float(df[value_col].mean())
    part_means = df.groupby(part_col)[value_col].mean()
    op_means   = df.groupby(operator_col)[value_col].mean()
    cell_means = df.groupby([part_col, operator_col])[value_col].mean()

    SS_Part  = n_ops   * n_trials * float(((part_means - grand_mean) ** 2).sum())
    SS_Op    = n_parts * n_trials * float(((op_means   - grand_mean) ** 2).sum())
    SS_Cells = n_trials           * float(((cell_means - grand_mean) ** 2).sum())
    SS_Inter = SS_Cells - SS_Part - SS_Op
    SS_Error = float(
        df.groupby([part_col, operator_col])[value_col]
        .apply(lambda g: float(((g - g.mean()) ** 2).sum()))
        .sum()
    )

    df_part  = n_parts - 1
    df_op    = n_ops   - 1
    df_inter = df_part * df_op
    df_error = n_parts * n_ops * (n_trials - 1)

    MS_Part  = SS_Part  / df_part  if df_part  > 0 else 0.0
    MS_Op    = SS_Op    / df_op    if df_op    > 0 else 0.0
    MS_Inter = SS_Inter / df_inter if df_inter > 0 else 0.0
    MS_Error = SS_Error / df_error if df_error > 0 else 0.0

    var_ev  = MS_Error
    var_int = max(0.0, (MS_Inter - MS_Error) / n_trials)
    var_av  = max(0.0, (MS_Op    - MS_Inter) / (n_parts * n_trials))
    var_pv  = max(0.0, (MS_Part  - MS_Inter) / (n_ops   * n_trials))

    grr2 = var_ev + var_av
    tv2  = grr2 + var_pv

    ev   = float(np.sqrt(var_ev))
    av   = float(np.sqrt(var_av))
    int_ = float(np.sqrt(var_int))
    pv   = float(np.sqrt(var_pv))
    grr  = float(np.sqrt(grr2))
    tv   = float(np.sqrt(tv2)) if tv2 > 0 else 0.0

    grr_pct = 100.0 * grr  / tv if tv > 0 else 0.0
    ev_pct  = 100.0 * ev   / tv if tv > 0 else 0.0
    av_pct  = 100.0 * av   / tv if tv > 0 else 0.0
    int_pct = 100.0 * int_ / tv if tv > 0 else 0.0
    pv_pct  = 100.0 * pv   / tv if tv > 0 else 0.0

    ndc = math.floor(1.41 * pv / grr) if grr > 0 else 99

    verdict = "good" if grr_pct < 10 else "warning" if grr_pct < 30 else "alert"

    def _F(ms_num: float, ms_den: float) -> float | None:
        return round(ms_num / ms_den, 4) if ms_den > 0 else None

    def _p(F: float | None, dfn: int, dfd: int) -> float | None:
        if F is None or dfd <= 0:
            return None
        return round(float(1 - stats.f.cdf(F, dfn, dfd)), 4)

    F_part  = _F(MS_Part,  MS_Inter)
    F_op    = _F(MS_Op,    MS_Inter)
    F_inter = _F(MS_Inter, MS_Error)

    anova_table = pd.DataFrame([
        {"変動源": "Part",        "SS": round(SS_Part,  6), "df": df_part,  "MS": round(MS_Part,  6), "F": F_part,  "p値": _p(F_part,  df_part,  df_inter)},
        {"変動源": "Operator",    "SS": round(SS_Op,    6), "df": df_op,    "MS": round(MS_Op,    6), "F": F_op,    "p値": _p(F_op,    df_op,    df_inter)},
        {"変動源": "Interaction", "SS": round(SS_Inter, 6), "df": df_inter, "MS": round(MS_Inter, 6), "F": F_inter, "p値": _p(F_inter, df_inter, df_error)},
        {"変動源": "Error",       "SS": round(SS_Error, 6), "df": df_error, "MS": round(MS_Error, 6), "F": None,    "p値": None},
    ])

    return {
        "ev": ev, "av": av, "int_": int_, "pv": pv, "grr": grr, "tv": tv,
        "grr_pct": grr_pct, "ev_pct": ev_pct, "av_pct": av_pct,
        "int_pct": int_pct, "pv_pct": pv_pct,
        "ndc": ndc, "verdict": verdict,
        "anova_table": anova_table,
    }
