import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(occ=0.75, n_months=12):
    """Create test DataFrame with configurable occupancy rate."""
    room_types = [
        ("シングル", 30, 10000),
        ("ダブル", 20, 18000),
        ("ツイン", 25, 15000),
        ("スイート", 5, 50000),
    ]
    rows = []
    rng = np.random.default_rng(42)

    for m in range(n_months):
        for rtype, total, adr in room_types:
            sold = int(total * occ + rng.normal(0, 1))
            sold = max(0, min(sold, total))
            rows.append({
                "month": f"2024-{m+1:02d}",
                "room_type": rtype,
                "total_rooms": total,
                "sold_rooms": sold,
                "adr": adr,
                "revenue": sold * adr,
            })

    return pd.DataFrame(rows)


def test_returns_dict():
    """Test that analyze returns a dictionary."""
    result = analyze(make_df())
    assert isinstance(result, dict)


def test_required_keys():
    """Test that all required keys are present in result."""
    result = analyze(make_df())
    required_keys = ["monthly_df", "room_df", "avg_occ", "avg_revpar", "avg_adr", "total_revenue", "verdict"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def test_verdict_good():
    """Test that high occupancy (80%) results in 'good' verdict."""
    result = analyze(make_df(occ=0.80))
    assert result["verdict"] == "good"


def test_verdict_warning():
    """Test that medium occupancy (60%) results in 'warning' verdict."""
    result = analyze(make_df(occ=0.60))
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """Test that low occupancy (40%) results in 'alert' verdict."""
    result = analyze(make_df(occ=0.40))
    assert result["verdict"] == "alert"


def test_occ_range():
    """Test that occupancy is within valid range [0, 100]."""
    result = analyze(make_df())
    assert 0 <= result["avg_occ"] <= 100


def test_room_df_length():
    """Test that room_df has 4 room types."""
    result = analyze(make_df())
    assert len(result["room_df"]) == 4


def test_revenue_positive():
    """Test that total revenue is positive."""
    result = analyze(make_df())
    assert result["total_revenue"] > 0
