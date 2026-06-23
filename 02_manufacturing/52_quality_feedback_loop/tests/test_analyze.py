import pytest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(improvement=60.0, n=10):
    """
    Create a test dataframe with specified improvement rate.

    Args:
        improvement: improvement rate as percentage (0-100)
        n: number of rows

    Returns:
        pd.DataFrame with test data
    """
    before = 3.0
    after = before * (1 - improvement / 100)
    rows = []
    for i in range(n):
        rows.append(
            {
                "date": f"2024-01-{i+1:02d}",
                "product": f"製品{chr(65+i%4)}",
                "claim_type": ["寸法不良", "外観不良", "機能不良"][i % 3],
                "root_process": ["切断", "溶接", "塗装", "組立"][i % 4],
                "action_taken": ["治具交換", "作業手順改訂", "材料変更"][i % 3],
                "before_rate": before,
                "after_rate": after,
                "action_date": f"2024-01-{i+16:02d}",
            }
        )
    return pd.DataFrame(rows)


def test_returns_dict():
    """Test that analyze returns a dictionary."""
    result = analyze(make_df())
    assert isinstance(result, dict)


def test_required_keys():
    """Test that all required keys are present in result."""
    result = analyze(make_df())
    required_keys = [
        "df",
        "process_df",
        "action_df",
        "product_df",
        "avg_improvement",
        "avg_lead_time",
        "total_cases",
        "verdict",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def test_verdict_good():
    """Test verdict is 'good' when improvement >= 50%."""
    result = analyze(make_df(60))
    assert result["verdict"] == "good"


def test_verdict_warning():
    """Test verdict is 'warning' when 25% <= improvement < 50%."""
    result = analyze(make_df(35))
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """Test verdict is 'alert' when improvement < 25%."""
    result = analyze(make_df(10))
    assert result["verdict"] == "alert"


def test_improvement_rate_positive():
    """Test that improvement rate is calculated and positive."""
    result = analyze(make_df(50))
    assert result["avg_improvement"] > 0


def test_total_cases():
    """Test that total_cases matches number of rows."""
    result = analyze(make_df(n=10))
    assert result["total_cases"] == 10


def test_process_df_not_empty():
    """Test that process_df is not empty after groupby."""
    result = analyze(make_df())
    assert len(result["process_df"]) > 0
