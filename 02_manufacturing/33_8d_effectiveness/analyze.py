"""是正処置（8D）効果検証 — Welch t検定 + Cohen's d + verdict。"""
from __future__ import annotations
import pandas as pd
import numpy as np
from scipy import stats

REQUIRED_COLS = ["action_id", "action_name", "group", "value"]
GROUP_BEFORE  = "処置前"
GROUP_AFTER   = "処置後"
ALPHA = 0.05


def _cohen_d(before: np.ndarray, after: np.ndarray) -> float:
    n1, n2 = len(before), len(after)
    pooled_std = np.sqrt(
        ((n1 - 1) * np.std(before, ddof=1) ** 2 + (n2 - 1) * np.std(after, ddof=1) ** 2)
        / (n1 + n2 - 2)
    )
    return float((np.mean(before) - np.mean(after)) / pooled_std) if pooled_std > 0 else 0.0


def _verdict(ratio: float) -> str:
    if ratio >= 80.0:
        return "good"
    elif ratio >= 50.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["value"])

    rows = []
    for action_id, grp in data.groupby("action_id", sort=False):
        action_name = grp["action_name"].iloc[0]
        before_vals = grp[grp["group"] == GROUP_BEFORE]["value"].values
        after_vals  = grp[grp["group"] == GROUP_AFTER]["value"].values

        if len(before_vals) < 2 or len(after_vals) < 2:
            continue

        mean_before = float(np.mean(before_vals))
        mean_after  = float(np.mean(after_vals))

        # Welch t検定
        _, p_value = stats.ttest_ind(before_vals, after_vals, equal_var=False)
        significant = bool(p_value < ALPHA)

        # 改善率（処置後が処置前より小さい方向を「改善」とする）
        improvement_rate = float((mean_before - mean_after) / mean_before * 100) if mean_before != 0 else 0.0

        cd = _cohen_d(before_vals, after_vals)

        # 有意差あり AND 改善方向（improvement_rate > 0）で有効と判定
        effective = significant and improvement_rate > 0

        rows.append({
            "action_id":       action_id,
            "action_name":     action_name,
            "n_before":        len(before_vals),
            "n_after":         len(after_vals),
            "mean_before":     round(mean_before, 4),
            "mean_after":      round(mean_after,  4),
            "improvement_rate": round(improvement_rate, 2),
            "cohen_d":         round(cd, 4),
            "p_value":         round(float(p_value), 6),
            "significant":     significant,
            "effective":       effective,
        })

    result_summary = pd.DataFrame(rows)
    total_actions   = len(result_summary)
    effective_count = int(result_summary["effective"].sum()) if total_actions > 0 else 0
    effective_ratio = effective_count / total_actions * 100 if total_actions > 0 else 0.0

    best_action = (
        result_summary.loc[result_summary["improvement_rate"].idxmax(), "action_id"]
        if total_actions > 0 else None
    )

    return {
        "result_summary":  result_summary,
        "total_actions":   total_actions,
        "effective_count": effective_count,
        "effective_ratio": round(effective_ratio, 1),
        "best_action":     best_action,
        "verdict":         _verdict(effective_ratio),
    }
