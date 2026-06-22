"""4M変更前後品質比較 — t検定/Mann-Whitney 有意差検定。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats

REQUIRED_COLS = ["change_id", "change_name", "group", "value"]
GROUP_BEFORE  = "変更前"
GROUP_AFTER   = "変更後"
ALPHA         = 0.05


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

    if len(data) < 2:
        raise ValueError("有効なデータがありません。")

    rows = []
    for (cid, cname), grp in data.groupby(["change_id", "change_name"]):
        before = grp[grp["group"] == GROUP_BEFORE]["value"].values
        after  = grp[grp["group"] == GROUP_AFTER]["value"].values
        if len(before) < 2 or len(after) < 2:
            continue

        _, p_t  = stats.ttest_ind(before, after, equal_var=False)
        _, p_mw = stats.mannwhitneyu(before, after, alternative="two-sided")
        mean_b  = float(np.mean(before))
        mean_a  = float(np.mean(after))
        improvement_rate = float((mean_b - mean_a) / mean_b * 100) if mean_b != 0 else 0.0
        significant = bool(p_t < ALPHA)

        rows.append({
            "change_id":       cid,
            "change_name":     cname,
            "n_before":        int(len(before)),
            "n_after":         int(len(after)),
            "mean_before":     round(mean_b, 4),
            "mean_after":      round(mean_a, 4),
            "improvement_rate": round(improvement_rate, 2),
            "p_value_t":       round(float(p_t), 4),
            "p_value_mw":      round(float(p_mw), 4),
            "significant":     significant,
        })

    if not rows:
        raise ValueError("有効な変更前後ペアがありません。")

    result_summary   = pd.DataFrame(rows)
    total_changes    = int(len(result_summary))
    significant_count = int(result_summary["significant"].sum())
    significant_ratio = float(significant_count / total_changes * 100)

    sig_df = result_summary[result_summary["significant"]]
    if len(sig_df) > 0:
        best_change = str(sig_df.loc[sig_df["improvement_rate"].idxmax(), "change_name"])
    else:
        best_change = str(result_summary.loc[result_summary["improvement_rate"].idxmax(), "change_name"])

    return {
        "result_summary":   result_summary,
        "total_changes":    total_changes,
        "significant_count": significant_count,
        "significant_ratio": significant_ratio,
        "best_change":      best_change,
        "verdict":          _verdict(significant_ratio),
    }
