import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(defect_rate_pct=2.0, n=10):
    import numpy as np
    rng = np.random.default_rng(42)
    inspection = rng.integers(100, 200, n)
    defects = (inspection * defect_rate_pct / 100).astype(int)
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "supplier": [f"S{i%3+1}" for i in range(n)],
        "inspection_count": inspection,
        "defect_count": defects,
    })

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["supplier_df","trend_df","avg_defect_rate","worst_supplier","verdict"]:
        assert k in r

def test_verdict_good():
    assert analyze(make_df(0.5))["verdict"] == "good"

def test_verdict_warning():
    assert analyze(make_df(2.0))["verdict"] == "warning"

def test_verdict_alert():
    assert analyze(make_df(5.0))["verdict"] == "alert"

def test_supplier_df_columns():
    r = analyze(make_df())
    assert "defect_rate" in r["supplier_df"].columns

def test_trend_df_not_empty():
    r = analyze(make_df())
    assert len(r["trend_df"]) > 0

def test_defect_rate_positive():
    r = analyze(make_df(2.0))
    assert r["avg_defect_rate"] > 0
