"""不良モード別パレート × 時系列複合分析ロジック（純粋関数モジュール）。"""
from __future__ import annotations
import pandas as pd


def run_analysis(
    df: pd.DataFrame,
    date_col: str,
    mode_col: str,
    count_col: str,
) -> dict:
    """
    月次集計済み不良モードデータをパレート分析・時系列推移・verdict に変換する。

    Returns
    -------
    dict
        pareto_df, trend_df, top_mode, top_mode_pct, total_count,
        vital_few, latest_month, latest_total, prev_total, verdict
    """
    df = df.copy()
    df[count_col] = pd.to_numeric(df[count_col], errors="coerce")
    df = df.dropna(subset=[count_col])
    df[count_col] = df[count_col].astype(int)

    n_modes  = df[mode_col].nunique()
    n_months = df[date_col].nunique()
    if n_modes < 2:
        raise ValueError(f"不良モードは最低 2 種類必要です。検出: {n_modes}")
    if n_months < 2:
        raise ValueError(f"月数は最低 2 ヶ月必要です。検出: {n_months}")

    # ── パレート集計（全期間合計）
    mode_totals  = df.groupby(mode_col)[count_col].sum().sort_values(ascending=False)
    total_count  = int(mode_totals.sum())
    top_mode     = str(mode_totals.index[0])
    top_mode_pct = float(mode_totals.iloc[0] / total_count * 100)

    cum_counts = mode_totals.cumsum()
    cum_pct    = cum_counts / total_count * 100

    pareto_df = pd.DataFrame({
        mode_col:         mode_totals.index.tolist(),
        "count":          mode_totals.values.tolist(),
        "cumulative_pct": cum_pct.values.tolist(),
    }).reset_index(drop=True)

    # ── vital few（累積 80% 以内、最低 1 件）
    vital_few: list[str] = []
    for _, row in pareto_df.iterrows():
        vital_few.append(str(row[mode_col]))
        if row["cumulative_pct"] >= 80.0:
            break

    # ── 月別推移ピボット（列順: パレート降順）
    trend_df = df.pivot_table(
        index=date_col, columns=mode_col,
        values=count_col, aggfunc="sum", fill_value=0,
    )
    col_order = [c for c in mode_totals.index if c in trend_df.columns]
    trend_df  = trend_df[col_order]
    trend_df  = trend_df.reindex(sorted(trend_df.index.tolist()))

    # ── verdict（直近月 vs 前月 合計件数）
    sorted_months = sorted(df[date_col].unique().tolist())
    month_totals  = df.groupby(date_col)[count_col].sum()

    latest_month = sorted_months[-1]
    latest_total = int(month_totals.get(latest_month, 0))

    if len(sorted_months) >= 2:
        prev_month = sorted_months[-2]
        prev_total = int(month_totals.get(prev_month, 0))
    else:
        prev_total = latest_total

    if prev_total == 0:
        verdict = "warning"
    elif latest_total < prev_total * 0.9:
        verdict = "good"
    elif latest_total <= prev_total * 1.1:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "pareto_df":    pareto_df,
        "trend_df":     trend_df,
        "top_mode":     top_mode,
        "top_mode_pct": top_mode_pct,
        "total_count":  total_count,
        "vital_few":    vital_few,
        "latest_month": latest_month,
        "latest_total": latest_total,
        "prev_total":   prev_total,
        "verdict":      verdict,
    }
