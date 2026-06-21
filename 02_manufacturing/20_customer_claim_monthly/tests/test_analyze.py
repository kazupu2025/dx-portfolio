"""C-74 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(customers, months, categories, counts):
    return pd.DataFrame({
        "customer": customers,
        "month":    months,
        "category": categories,
        "count":    counts,
    })


def test_verdict_good():
    # 1ヶ月 total=5 → avg=5.0 → good（境界値）
    df = _make_df(["A社"], ["2024-01"], ["寸法不良"], [5])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_monthly_claims"] == pytest.approx(5.0)


def test_verdict_warning():
    # 1ヶ月 total=10 → avg=10.0 → warning
    df = _make_df(["A社"], ["2024-01"], ["寸法不良"], [10])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 5.0 < result["avg_monthly_claims"] <= 15.0


def test_verdict_alert():
    # 1ヶ月 total=20 → avg=20.0 → alert
    df = _make_df(["A社"], ["2024-01"], ["寸法不良"], [20])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_monthly_claims"] > 15.0


def test_verdict_warning_upper_boundary():
    # 1ヶ月 total=15 → avg=15.0 → warning（上限境界値、alertではない）
    df = _make_df(["A社"], ["2024-01"], ["寸法不良"], [15])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["avg_monthly_claims"] == pytest.approx(15.0)


def test_total_claims():
    # 3行 count合計 = 2+3+5 = 10
    df = _make_df(
        ["A社", "B社", "A社"],
        ["2024-01", "2024-01", "2024-01"],
        ["寸法不良", "寸法不良", "外観不良"],
        [2, 3, 5],
    )
    result = analyze.run_analysis(df)
    assert result["total_claims"] == 10


def test_top_category():
    # 寸法不良: 8件, 外観不良: 3件 → top = 寸法不良
    df = _make_df(
        ["A社", "A社", "B社"],
        ["2024-01", "2024-01", "2024-01"],
        ["寸法不良", "外観不良", "寸法不良"],
        [5, 3, 3],
    )
    result = analyze.run_analysis(df)
    assert result["top_category"] == "寸法不良"


def test_worst_customer():
    # A社: 8件, B社: 3件, C社: 1件 → worst = A社
    df = _make_df(
        ["A社", "A社", "B社", "C社"],
        ["2024-01", "2024-01", "2024-01", "2024-01"],
        ["寸法不良", "外観不良", "寸法不良", "寸法不良"],
        [5, 3, 3, 1],
    )
    result = analyze.run_analysis(df)
    assert result["worst_customer"] == "A社"


def test_missing_column_raises():
    df = pd.DataFrame({"customer": ["A社"], "month": ["2024-01"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
