"""C-77 analyze.py TDD -- 8tests."""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(months, reasons, counts):
    return pd.DataFrame({"month": months, "reason": reasons, "count": counts})


def test_verdict_good():
    df = _make_df(["2024-01"], ["reason_a"], [3])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_monthly_count"] == pytest.approx(3.0)


def test_verdict_warning():
    df = _make_df(["2024-01"], ["reason_a"], [7])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 3.0 < result["avg_monthly_count"] <= 10.0


def test_verdict_alert():
    df = _make_df(["2024-01"], ["reason_a"], [15])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_monthly_count"] > 10.0


def test_verdict_warning_upper_boundary():
    df = _make_df(["2024-01"], ["reason_a"], [10])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert result["avg_monthly_count"] == pytest.approx(10.0)


def test_total_count():
    df = _make_df(
        ["2024-01", "2024-01", "2024-01"],
        ["reason_a", "reason_b", "reason_c"],
        [2, 3, 5],
    )
    result = analyze.run_analysis(df)
    assert result["total_count"] == 10


def test_top_reason():
    df = _make_df(
        ["2024-01", "2024-01", "2024-01"],
        ["reason_a", "reason_b", "reason_a"],
        [5, 3, 3],
    )
    result = analyze.run_analysis(df)
    assert result["top_reason"] == "reason_a"


def test_n_reasons():
    df = _make_df(
        ["2024-01", "2024-01", "2024-01"],
        ["reason_a", "reason_b", "reason_c"],
        [2, 3, 1],
    )
    result = analyze.run_analysis(df)
    assert result["n_reasons"] == 3


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "reason": ["reason_a"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
