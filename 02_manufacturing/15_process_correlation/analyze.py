"""工程間品質相関分析 Pearson 相関行列計算ロジック（純粋関数モジュール）。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import pearsonr


def run_analysis(
    df: pd.DataFrame,
    process_cols: list[str],
) -> dict:
    """
    複数工程の測定値から Pearson 相関行列と工程間の品質影響強度を計算する。

    verdict 基準（最強相関ペアの絶対値で判定）:
    - max |r| ≥ 0.7 → "good"    （強い相関: 工程間影響が明確）
    - max |r| ≥ 0.4 → "warning" （中程度の相関: 要監視）
    - max |r| < 0.4 → "alert"   （相関弱: 工程間に関係なし）

    Parameters
    ----------
    df : pd.DataFrame
    process_cols : list[str]  工程列名リスト（最低2列）

    Returns
    -------
    dict
        corr_df, pvalue_df, top_pair, top_r, top_pvalue,
        max_abs_r, n_samples, n_processes, verdict

    Raises
    ------
    ValueError
        工程列 < 2 のとき、または有効サンプル数 n < 3 のとき
    """
    if len(process_cols) < 2:
        raise ValueError(
            f"工程列は最低 2 列必要です。現在 {len(process_cols)} 列が指定されています。"
        )

    data = df[process_cols].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(data)

    if n < 3:
        raise ValueError(
            f"有効サンプル数が不足しています（n={n}、最低 3 必要）。"
        )

    # ── 相関行列（Pearson）────────────────────────────────────────
    corr_df = data.corr(method="pearson")

    # ── p値行列 ───────────────────────────────────────────────────
    pvalue_dict: dict[str, dict[str, float]] = {col: {} for col in process_cols}
    for col1 in process_cols:
        for col2 in process_cols:
            if col1 == col2:
                pvalue_dict[col1][col2] = 0.0
            else:
                _, p = pearsonr(data[col1].to_numpy(), data[col2].to_numpy())
                pvalue_dict[col1][col2] = float(p)
    pvalue_df = pd.DataFrame(pvalue_dict, index=process_cols)

    # ── 最強相関ペアを特定（対角を除く |r| 最大）────────────────
    corr_abs = corr_df.abs().copy()
    arr = corr_abs.to_numpy(copy=True)
    np.fill_diagonal(arr, 0.0)
    corr_abs = pd.DataFrame(arr, index=corr_abs.index, columns=corr_abs.columns)
    max_idx = corr_abs.stack().idxmax()
    top_pair: tuple[str, str] = (str(max_idx[0]), str(max_idx[1]))
    top_r      = float(corr_df.loc[top_pair[0], top_pair[1]])
    top_pvalue = float(pvalue_df.loc[top_pair[0], top_pair[1]])
    max_abs_r  = float(abs(top_r))

    # ── verdict 判定 ──────────────────────────────────────────────
    if max_abs_r >= 0.7:
        verdict = "good"
    elif max_abs_r >= 0.4:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "corr_df":     corr_df,
        "pvalue_df":   pvalue_df,
        "top_pair":    top_pair,
        "top_r":       top_r,
        "top_pvalue":  top_pvalue,
        "max_abs_r":   max_abs_r,
        "n_samples":   n,
        "n_processes": len(process_cols),
        "verdict":     verdict,
    }
