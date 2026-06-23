import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, compute_health_score, REQUIRED_COLUMNS


def make_df(n=20, login=20, feature=0.7, tickets=2, onboarding=True):
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n):
        rows.append({
            "customer_id": f"CS{i+1:03d}",
            "company": f"会社{i+1}",
            "plan": ["Basic", "Standard", "Premium"][i % 3],
            "contract_start": "2024-01-01",
            "nps_score": float(rng.integers(-50, 80)),
            "login_days_30": login + rng.integers(-3, 3),
            "feature_usage_rate": feature,
            "support_tickets": tickets,
            "onboarding_complete": onboarding,
            "arr": 500000,
        })
    return pd.DataFrame(rows)


def test_returns_dict():
    assert isinstance(analyze(make_df()), dict)


def test_required_keys():
    r = analyze(make_df())
    for k in ["df", "plan_df", "nps", "avg_health", "risk_count", "healthy_count", "at_risk_arr", "onboarding_rate", "verdict"]:
        assert k in r


def test_verdict_good():
    assert analyze(make_df(login=25, feature=0.9, tickets=0))["verdict"] == "good"


def test_verdict_alert():
    assert analyze(make_df(login=2, feature=0.1, tickets=10, onboarding=False))["verdict"] == "alert"


def test_health_score_range():
    row = {"login_days_30": 20, "feature_usage_rate": 0.8, "support_tickets": 2, "onboarding_complete": True}
    s = compute_health_score(row)
    assert 0 <= s <= 100


def test_onboarding_rate_range():
    r = analyze(make_df())
    assert 0 <= r["onboarding_rate"] <= 100


def test_plan_df_not_empty():
    assert len(analyze(make_df())["plan_df"]) > 0


def test_at_risk_arr_nonneg():
    assert analyze(make_df())["at_risk_arr"] >= 0
