import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(grade_a=75, n_months=6):
    """Create a sample DataFrame for testing."""
    crops = ["トマト", "キャベツ", "ほうれん草", "じゃがいも"]
    rows = []
    rng = np.random.default_rng(42)
    for m in range(n_months):
        for crop in crops:
            ga = grade_a + rng.normal(0, 3)
            gb = 15 + rng.normal(0, 2)
            gc = max(0, 100 - ga - gb)
            rows.append(
                {
                    "month": f"2024-{m+1:02d}",
                    "crop": crop,
                    "field_area_ha": 1.5,
                    "yield_kg": 3000 + rng.normal(0, 200),
                    "grade_a_rate": ga,
                    "grade_b_rate": gb,
                    "grade_c_rate": gc,
                    "avg_brix": 8.0 + rng.normal(0, 0.5),
                    "moisture_pct": 85 + rng.normal(0, 2),
                }
            )
    return pd.DataFrame(rows)


def test_returns_dict():
    """Test that analyze returns a dictionary."""
    assert isinstance(analyze(make_df()), dict)


def test_required_keys():
    """Test that analyze result contains all required keys."""
    r = analyze(make_df())
    for k in [
        "df",
        "crop_df",
        "monthly_df",
        "total_yield",
        "avg_grade_a",
        "avg_brix",
        "verdict",
    ]:
        assert k in r


def test_verdict_good():
    """Test verdict is 'good' when grade_a >= 75%."""
    assert analyze(make_df(grade_a=80))["verdict"] == "good"


def test_verdict_warning():
    """Test verdict is 'warning' when 60% <= grade_a < 75%."""
    assert analyze(make_df(grade_a=65))["verdict"] == "warning"


def test_verdict_alert():
    """Test verdict is 'alert' when grade_a < 60%."""
    assert analyze(make_df(grade_a=50))["verdict"] == "alert"


def test_total_yield_positive():
    """Test that total_yield is positive."""
    assert analyze(make_df())["total_yield"] > 0


def test_crop_df_length():
    """Test that crop_df has exactly 4 crops."""
    assert len(analyze(make_df())["crop_df"]) == 4


def test_monthly_df_not_empty():
    """Test that monthly_df is not empty."""
    assert len(analyze(make_df())["monthly_df"]) > 0
