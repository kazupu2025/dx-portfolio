import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, compute_control_limits, detect_violations

def make_df(n_subgroups=20, subgroup_size=5, noise=0.5, shift=0.0):
    rng = np.random.default_rng(42)
    rows = []
    for sg in range(n_subgroups):
        for _ in range(subgroup_size):
            rows.append({"subgroup_id": sg, "value": 50.0 + shift + rng.normal(0, noise)})
    return pd.DataFrame(rows)

def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)

def test_required_keys():
    r = analyze(make_df())
    for k in ["sg_df","xbar_bar","r_bar","ucl_x","lcl_x","ucl_r","lcl_r","violations","n_violations","verdict"]:
        assert k in r

def test_verdict_good():
    r = analyze(make_df(noise=0.1))
    assert r["verdict"] == "good"

def test_verdict_alert():
    # Create stable baseline, then add out-of-control data
    rng = np.random.default_rng(42)
    rows = []
    # 20 subgroups of stable data
    for sg in range(20):
        for _ in range(5):
            rows.append({"subgroup_id": sg, "value": 50.0 + rng.normal(0, 0.5)})
    # 5 subgroups of out-of-control data (shifted up by 3 sigma)
    for sg in range(20, 25):
        for _ in range(5):
            rows.append({"subgroup_id": sg, "value": 53.0 + rng.normal(0, 0.5)})
    df = pd.DataFrame(rows)
    r = analyze(df, 5)
    assert r["verdict"] in ["warning","alert"]

def test_ucl_above_mean():
    r = analyze(make_df())
    assert r["ucl_x"] > r["xbar_bar"]

def test_lcl_below_mean():
    r = analyze(make_df())
    assert r["lcl_x"] < r["xbar_bar"]

def test_no_violations_stable():
    r = analyze(make_df(noise=0.05))
    assert r["n_violations"] == 0

def test_sg_df_length():
    r = analyze(make_df(n_subgroups=10))
    assert len(r["sg_df"]) == 10
