"""analyze.run_analysis の集計・パレートロジック ユニットテスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["year_month", "defect_mode", "count"])


def _sample_df() -> pd.DataFrame:
    """5モード × 2ヶ月（バリが最多）"""
    return _make_df([
        ("2024-01", "バリ",     50),
        ("2024-01", "寸法不良", 20),
        ("2024-01", "表面傷",   15),
        ("2024-01", "欠け",     10),
        ("2024-01", "異物混入",  5),
        ("2024-02", "バリ",     45),
        ("2024-02", "寸法不良", 22),
        ("2024-02", "表面傷",   14),
        ("2024-02", "欠け",      9),
        ("2024-02", "異物混入",  4),
    ])


def _alert_df() -> pd.DataFrame:
    """直近月が前月比 +30% → alert"""
    return _make_df([
        ("2024-01", "バリ",     40),
        ("2024-01", "寸法不良", 20),
        ("2024-02", "バリ",     55),
        ("2024-02", "寸法不良", 27),
    ])


def _good_df() -> pd.DataFrame:
    """直近月が前月比 -20% → good"""
    return _make_df([
        ("2024-01", "バリ",     50),
        ("2024-01", "寸法不良", 20),
        ("2024-02", "バリ",     37),
        ("2024-02", "寸法不良", 16),
    ])


def _warning_df() -> pd.DataFrame:
    """直近月が前月と同数 → warning"""
    return _make_df([
        ("2024-01", "バリ",     50),
        ("2024-01", "寸法不良", 20),
        ("2024-02", "バリ",     50),
        ("2024-02", "寸法不良", 20),
    ])


def test_pareto_sorted_descending():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    counts = result["pareto_df"]["count"].tolist()
    assert counts == sorted(counts, reverse=True), "pareto_df は件数降順であること"


def test_cumulative_pct_reaches_100():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    last = result["pareto_df"]["cumulative_pct"].iloc[-1]
    assert abs(last - 100.0) < 1e-6, f"累積%の最終値が 100.0 であること: {last}"


def test_vital_few_contains_top_mode():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    assert result["top_mode"] in result["vital_few"]
    assert result["vital_few"][0] == result["top_mode"], "vital_few の先頭が top_mode であること"


def test_vital_few_threshold():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    pareto_df = result["pareto_df"]
    vital_few = result["vital_few"]
    last_vital = vital_few[-1]
    cum_at_last = pareto_df.loc[
        pareto_df["defect_mode"] == last_vital, "cumulative_pct"
    ].iloc[0]
    assert cum_at_last >= 80.0, f"vital_few の累積% が 80% 以上であること: {cum_at_last}"


def test_verdict_good():
    result = analyze.run_analysis(_good_df(), "year_month", "defect_mode", "count")
    assert result["verdict"] == "good", f"前月比 -20% は 'good' であること: {result['verdict']}"


def test_verdict_warning():
    result = analyze.run_analysis(_warning_df(), "year_month", "defect_mode", "count")
    assert result["verdict"] == "warning", f"前月と同数は 'warning' であること: {result['verdict']}"


def test_verdict_alert():
    result = analyze.run_analysis(_alert_df(), "year_month", "defect_mode", "count")
    assert result["verdict"] == "alert", f"前月比 +30% は 'alert' であること: {result['verdict']}"


def test_output_keys():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    required = {
        "pareto_df", "trend_df", "top_mode", "top_mode_pct",
        "total_count", "vital_few", "latest_month",
        "latest_total", "prev_total", "verdict",
    }
    missing = required - set(result.keys())
    assert not missing, f"出力 dict にキーが不足: {missing}"
