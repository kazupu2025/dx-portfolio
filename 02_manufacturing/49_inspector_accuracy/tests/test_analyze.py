import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(detection_rate=0.95, n=10):
    import numpy as np
    rows = []
    for i in range(n):
        true_d = 20
        found = int(true_d * detection_rate)
        rows.append({
            "date": f"2024-01-{i+1:02d}",
            "inspector": f"検査員{chr(65+i%5)}",
            "inspected": 200,
            "defects_found": found,
            "true_defects": true_d,
        })
    return pd.DataFrame(rows)

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["inspector_df","avg_detection_rate","worst_inspector","total_miss","verdict"]:
        assert k in r

def test_verdict_good():
    assert analyze(make_df(0.97))["verdict"] == "good"

def test_verdict_warning():
    assert analyze(make_df(0.90))["verdict"] == "warning"

def test_verdict_alert():
    assert analyze(make_df(0.80))["verdict"] == "alert"

def test_detection_rate_range():
    r = analyze(make_df(0.95))
    assert 0 <= r["avg_detection_rate"] <= 100

def test_total_miss_nonneg():
    assert analyze(make_df())["total_miss"] >= 0

def test_inspector_df_not_empty():
    assert len(analyze(make_df())["inspector_df"]) > 0
