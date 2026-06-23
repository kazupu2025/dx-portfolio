import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze, REQUIRED_COLUMNS

def make_df(dominant_pct=0.25):
    rows = []
    total = 100
    dom = int(total * dominant_pct)
    for i in range(dom):
        rows.append({"date":"2024-01-01","process":"切断","defect_code":"D001","count":1})
    for code in ["D002","D003","D004","D005"]:
        share = (total - dom) // 4
        for i in range(share):
            rows.append({"date":"2024-01-15","process":"溶接","defect_code":code,"count":1})
    return pd.DataFrame(rows)

def test_returns_dict(): assert isinstance(analyze(make_df()), dict)
def test_required_keys():
    r = analyze(make_df())
    for k in ["code_df","process_df","trend_df","total_defects","top_code","top_code_pct","verdict"]:
        assert k in r
def test_verdict_good(): assert analyze(make_df(0.25))["verdict"] == "good"
def test_verdict_warning(): assert analyze(make_df(0.45))["verdict"] == "warning"
def test_verdict_alert(): assert analyze(make_df(0.60))["verdict"] == "alert"
def test_top_code_is_d001(): assert analyze(make_df(0.60))["top_code"] == "D001"
def test_pct_sums_to_100():
    r = analyze(make_df())
    assert abs(r["code_df"]["pct"].sum() - 100) < 0.1
def test_total_positive(): assert analyze(make_df())["total_defects"] > 0
