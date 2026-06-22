"""品質コストROI分析 — 予防投資額 vs 失敗コスト削減額 + verdict。"""
from __future__ import annotations
import pandas as pd

REQUIRED_COLS = ["month", "prevention_cost", "appraisal_cost", "internal_failure", "external_failure"]


def _verdict(roi: float) -> str:
    if roi >= 100.0:
        return "good"
    elif roi >= 0.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in REQUIRED_COLS[1:]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=REQUIRED_COLS[1:])

    # 計算列を追加
    data["total_prevention"] = data["prevention_cost"] + data["appraisal_cost"]
    data["total_failure"]    = data["internal_failure"] + data["external_failure"]
    data["total_cost"]       = data["total_prevention"] + data["total_failure"]
    data["failure_ratio"]    = data["total_failure"] / data["total_cost"] * 100

    total_prevention = float(data["total_prevention"].sum())

    # ROI: 最初の月の失敗コストを baseline として最終月との差分
    first_failure = float(data["total_failure"].iloc[0])
    last_failure  = float(data["total_failure"].iloc[-1])
    roi = (first_failure - last_failure) / total_prevention * 100 if total_prevention > 0 else 0.0

    avg_failure_ratio = float(data["failure_ratio"].mean())

    # トレンド判定: 失敗コストが減少傾向か（最終月 < 最初の月）
    trend_verdict = last_failure < first_failure

    # 最低 failure_ratio 月
    best_month = str(data.loc[data["failure_ratio"].idxmin(), "month"])

    n_months = len(data)

    return {
        "result_df":        data.reset_index(drop=True),
        "avg_failure_ratio": round(avg_failure_ratio, 2),
        "roi":              round(roi, 2),
        "trend_verdict":    trend_verdict,
        "best_month":       best_month,
        "n_months":         n_months,
        "verdict":          _verdict(roi),
    }
