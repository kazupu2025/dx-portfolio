import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(attendance=90, score=70, n_months=3):
    """Generate test dataframe with configurable parameters"""
    classes = ["A組", "B組", "C組", "D組"]
    subjects = ["数学", "英語", "理科"]
    rows = []
    rng = np.random.default_rng(42)

    for m in range(n_months):
        for cls in classes:
            for subj in subjects:
                rows.append({
                    "month": f"2024-{m+4:02d}",
                    "class_name": cls,
                    "subject": subj,
                    "attendance_rate": attendance + rng.normal(0, 2),
                    "avg_score": score + rng.normal(0, 5),
                    "student_count": 30,
                    "failing_count": 2,
                })
    return pd.DataFrame(rows)


def test_returns_dict():
    """Test that analyze returns a dictionary"""
    result = analyze(make_df())
    assert isinstance(result, dict)


def test_required_keys():
    """Test that all required keys are in result"""
    result = analyze(make_df())
    required_keys = ["df", "class_df", "subject_df", "trend_df", "overall_attendance",
                     "overall_score", "overall_failing_rate", "correlation", "alert_classes", "verdict"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def test_verdict_good():
    """Test that high attendance results in 'good' verdict"""
    result = analyze(make_df(attendance=92))
    assert result["verdict"] == "good"


def test_verdict_warning():
    """Test that mid-range attendance results in 'warning' verdict"""
    result = analyze(make_df(attendance=83))
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """Test that low attendance results in 'alert' verdict"""
    result = analyze(make_df(attendance=75))
    assert result["verdict"] == "alert"


def test_correlation_range():
    """Test that correlation is within valid range"""
    result = analyze(make_df())
    assert -1 <= result["correlation"] <= 1, "Correlation must be between -1 and 1"


def test_class_df_length():
    """Test that class aggregation includes all 4 classes"""
    result = analyze(make_df())
    assert len(result["class_df"]) == 4, f"Expected 4 classes, got {len(result['class_df'])}"


def test_trend_df_not_empty():
    """Test that trend dataframe is not empty"""
    result = analyze(make_df())
    assert len(result["trend_df"]) > 0, "Trend dataframe should not be empty"
