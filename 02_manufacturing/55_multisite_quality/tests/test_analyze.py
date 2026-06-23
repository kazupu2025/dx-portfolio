import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS


def make_df(n_months=6, defect_base=1.0, seed=42):
    """Create a test DataFrame with n_months months across 4 sites."""
    sites = ["東京工場", "大阪工場", "名古屋工場", "福岡工場"]
    rows = []
    rng = np.random.default_rng(seed)

    for m in range(n_months):
        for i, site in enumerate(sites):
            rows.append({
                "month": f"2024-{m+1:02d}",
                "site": site,
                "defect_rate": max(0.01, defect_base + i * 0.3 + rng.normal(0, 0.1)),
                "cpk": max(0.5, 1.5 - i * 0.1 + rng.normal(0, 0.05)),
                "claim_count": max(0, int(i * 2 + rng.integers(0, 3))),
                "yield_rate": max(90.0, 99.0 - i * 0.5 + rng.normal(0, 0.2)),
            })

    return pd.DataFrame(rows)


def test_returns_dict():
    """Test that analyze() returns a dictionary."""
    result = analyze(make_df())
    assert isinstance(result, dict)


def test_required_keys():
    """Test that all required keys are present in the result."""
    result = analyze(make_df())
    required_keys = [
        "site_df", "trend_df", "best_site", "worst_site",
        "avg_defect", "n_sites", "verdict"
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


def test_verdict_good():
    """Test that low defect_rate yields 'good' verdict."""
    result = analyze(make_df(defect_base=0.05))
    assert result["verdict"] == "good"


def test_verdict_warning():
    """Test that moderate defect_rate yields 'warning' verdict."""
    result = analyze(make_df(defect_base=1.0))
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """Test that high defect_rate yields 'alert' verdict."""
    result = analyze(make_df(defect_base=2.0))
    assert result["verdict"] == "alert"


def test_n_sites():
    """Test that n_sites matches expected count (4 sites)."""
    result = analyze(make_df())
    assert result["n_sites"] == 4


def test_site_df_sorted():
    """Test that site_df is sorted by score in descending order."""
    result = analyze(make_df())
    scores = result["site_df"]["score"].tolist()
    assert scores == sorted(scores, reverse=True), "site_df must be sorted by score (descending)"


def test_trend_df_not_empty():
    """Test that trend_df contains data."""
    result = analyze(make_df())
    assert len(result["trend_df"]) > 0, "trend_df must not be empty"
