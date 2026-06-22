"""不良モード別パレート × 時系列複合分析 — パレート計算 + verdict。"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLS = ["month", "defect_mode", "count"]
PARETO_THRESHOLD = 80.0


def _verdict(top_count: int) -> str:
    if top_count <= 2:
        return "good"
    elif top_count <= 4:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    data["count"] = pd.to_numeric(data["count"], errors="coerce")
    data = data.dropna(subset=["count"])
    data = data[data["count"] >= 0].copy()
    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    mode_totals = data.groupby("defect_mode")["count"].sum().sort_values(ascending=False)
    grand_total = float(mode_totals.sum())

    pct        = (mode_totals / grand_total * 100).round(2)
    cumulative = pct.cumsum().round(2)

    pareto_df = pd.DataFrame({
        "defect_mode":    mode_totals.index.tolist(),
        "total":          mode_totals.values.astype(int).tolist(),
        "pct":            pct.values.tolist(),
        "cumulative_pct": cumulative.values.tolist(),
    })

    # 累積が threshold を超える最初のモードまでを pareto_flag=True にする
    pareto_df["pareto_flag"] = False
    for i in range(len(pareto_df)):
        pareto_df.at[i, "pareto_flag"] = True
        if pareto_df.at[i, "cumulative_pct"] >= PARETO_THRESHOLD:
            break

    trend_df = (
        data.groupby(["month", "defect_mode"])["count"].sum()
        .reset_index()
        .pivot(index="month", columns="defect_mode", values="count")
        .fillna(0)
        .sort_index()
    )
    trend_df.columns.name = None

    top_mode             = str(mode_totals.index[0])
    top_pareto_count     = int(pareto_df["pareto_flag"].sum())
    pareto_coverage_pct  = float(pareto_df[pareto_df["pareto_flag"]]["pct"].sum())

    return {
        "pareto_df":          pareto_df,
        "trend_df":           trend_df,
        "top_mode":           top_mode,
        "top_pareto_count":   top_pareto_count,
        "pareto_coverage_pct": pareto_coverage_pct,
        "verdict":            _verdict(top_pareto_count),
    }
