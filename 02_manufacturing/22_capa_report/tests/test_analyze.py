"""C-76 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(months, totals, completed, on_time):
    return pd.DataFrame({
        "month":             months,
        "total":             totals,
        "completed":         completed,
        "on_time_completed": on_time,
    })


def test_verdict_good():
    # completed=9/total=10 → rate=90.0% → good（境界値）
    df = _make_df(["2024-01"], [10], [9], [8])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["completion_rate"] == pytest.approx(90.0)


def test_verdict_warning():
    # completed=8/total=10 → rate=80.0% → warning
    df = _make_df(["2024-01"], [10], [8], [7])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 70.0 <= result["completion_rate"] < 90.0


def test_verdict_alert():
    # completed=6/total=10 → rate=60.0% → alert
    df = _make_df(["2024-01"], [10], [6], [5])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["completion_rate"] < 70.0


def test_verdict_warning_lower_boundary():
    # completed=7/total=10 → rate=70.0% → warning（下限境界値、alertではない）
    df = _make_df(["2024-01"], [10], [7], [6])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["completion_rate"] == pytest.approx(70.0)


def test_total_capas():
    # 2ヶ月合計: 10 + 15 = 25
    df = _make_df(["2024-01", "2024-02"], [10, 15], [8, 12], [7, 10])
    result = analyze.run_analysis(df)
    assert result["total_capas"] == 25


def test_completion_rate():
    # completed=18 / total=25 = 72.0%
    df = _make_df(["2024-01", "2024-02"], [10, 15], [8, 10], [7, 8])
    result = analyze.run_analysis(df)
    assert result["completion_rate"] == pytest.approx(72.0)


def test_open_count():
    # total=25 - completed=18 = 7
    df = _make_df(["2024-01", "2024-02"], [10, 15], [8, 10], [7, 8])
    result = analyze.run_analysis(df)
    assert result["open_count"] == 7


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "total": [10]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
