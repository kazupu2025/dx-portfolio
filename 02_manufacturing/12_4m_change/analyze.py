"""4M変更前後 統計的有意差検定ロジック（純粋関数モジュール）。"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from scipy import stats


def run_analysis(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    before_label: str,
    after_label: str,
) -> dict:
    """
    前後2グループの測定値を t検定 + Mann-Whitney U検定で比較する。

    Parameters
    ----------
    df : pd.DataFrame
        group_col に before_label/after_label を持つ long 形式データ
    group_col : str
        グループ列名
    value_col : str
        測定値列名
    before_label : str
        変更前グループの値
    after_label : str
        変更後グループの値

    Returns
    -------
    dict
        n_before, n_after, mean_before, mean_after, std_before, std_after,
        shapiro_before_p, shapiro_after_p, normal_before, normal_after,
        t_stat, t_pvalue, cohens_d,
        mw_stat, mw_pvalue, rank_biserial_r,
        recommended, p_value, effect_size, verdict

    Raises
    ------
    ValueError
        いずれかのグループの n < 3 のとき
    """
    before = pd.to_numeric(
        df.loc[df[group_col] == before_label, value_col], errors="coerce"
    ).dropna().to_numpy(dtype=float)

    after = pd.to_numeric(
        df.loc[df[group_col] == after_label, value_col], errors="coerce"
    ).dropna().to_numpy(dtype=float)

    if len(before) < 3 or len(after) < 3:
        raise ValueError(
            f"各グループは最低 3 サンプル必要です。before={len(before)}, after={len(after)}"
        )

    # ── 記述統計 ────────────────────────────────────────────────
    n_before = len(before)
    n_after  = len(after)
    mean_before = float(before.mean())
    mean_after  = float(after.mean())
    std_before  = float(before.std(ddof=1))
    std_after   = float(after.std(ddof=1))

    # ── 正規性検定（Shapiro-Wilk）────────────────────────────────
    shapiro_before_p = float(stats.shapiro(before).pvalue)
    shapiro_after_p  = float(stats.shapiro(after).pvalue)
    normal_before    = shapiro_before_p >= 0.05
    normal_after     = shapiro_after_p  >= 0.05

    # ── t検定（Welch の t検定）──────────────────────────────────
    t_stat, t_pvalue = stats.ttest_ind(before, after, equal_var=False)
    t_stat   = float(t_stat)
    t_pvalue = float(t_pvalue)

    # Cohen's d（プールド標準偏差）
    pooled_std = math.sqrt(
        ((n_before - 1) * std_before ** 2 + (n_after - 1) * std_after ** 2)
        / (n_before + n_after - 2)
    )
    cohens_d = abs(mean_after - mean_before) / pooled_std if pooled_std > 0 else 0.0

    # ── Mann-Whitney U検定 ────────────────────────────────────────
    mw_result = stats.mannwhitneyu(before, after, alternative="two-sided")
    mw_stat   = float(mw_result.statistic)
    mw_pvalue = float(mw_result.pvalue)

    # rank-biserial r（効果量）
    rank_biserial_r = float(1.0 - (2.0 * mw_stat) / (n_before * n_after))

    # ── 推奨検定の選択 ────────────────────────────────────────────
    recommended: str
    if normal_before and normal_after:
        recommended  = "t"
        p_value      = t_pvalue
        effect_size  = cohens_d
    else:
        recommended  = "mw"
        p_value      = mw_pvalue
        effect_size  = abs(rank_biserial_r)

    # ── verdict 判定 ──────────────────────────────────────────────
    if p_value >= 0.05:
        verdict = "good"
    elif effect_size < 0.5:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "n_before": n_before,
        "n_after":  n_after,
        "mean_before": mean_before,
        "mean_after":  mean_after,
        "std_before":  std_before,
        "std_after":   std_after,
        "shapiro_before_p": shapiro_before_p,
        "shapiro_after_p":  shapiro_after_p,
        "normal_before": normal_before,
        "normal_after":  normal_after,
        "t_stat":   t_stat,
        "t_pvalue": t_pvalue,
        "cohens_d": cohens_d,
        "mw_stat":          mw_stat,
        "mw_pvalue":        mw_pvalue,
        "rank_biserial_r":  rank_biserial_r,
        "recommended": recommended,
        "p_value":     p_value,
        "effect_size": effect_size,
        "verdict":     verdict,
    }
