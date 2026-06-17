# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

FPATH = os.path.join(os.path.dirname(__file__), "..", "output", "cleaned_progress_202401.csv")

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(FPATH, encoding="utf-8-sig")

def test_file_exists():
    assert os.path.exists(FPATH), "cleaned_progress_202401.csv が存在しない"

def test_row_count(df):
    assert len(df) >= 380, f"行数が少ない: {len(df)}"

def test_required_columns(df):
    required = [
        "work_date", "site_id", "site_name", "process", "worker_id",
        "planned_hours", "actual_hours", "progress_pct", "defect_count",
        "efficiency", "is_delayed", "kpi_flag", "source_file"
    ]
    missing = [c for c in required if c not in df.columns]
    assert len(missing) == 0, f"欠損列: {missing}"

def test_work_date_format(df):
    dates = pd.to_datetime(df["work_date"], format="%Y-%m-%d", errors="coerce")
    assert dates.notna().all(), "work_date に変換できない値がある"

def test_site_name_count(df):
    assert df["site_name"].nunique() == 5, f"site_name の種類数: {df['site_name'].nunique()}"

def test_process_count(df):
    assert df["process"].nunique() == 4, f"process の種類数: {df['process'].nunique()}"

def test_planned_hours_positive(df):
    assert (df["planned_hours"] > 0).all(), "planned_hours に0以下の値がある"

def test_actual_hours_positive(df):
    assert (df["actual_hours"] > 0).all(), "actual_hours に0以下の値がある"

def test_progress_pct_range(df):
    assert df["progress_pct"].between(0, 100).all(), "progress_pct が [0,100] 範囲外"

def test_defect_count_non_negative(df):
    assert (df["defect_count"] >= 0).all(), "defect_count に負の値がある"

def test_efficiency_positive(df):
    eff = df["efficiency"].dropna()
    assert (eff > 0).all(), "efficiency に0以下の値がある"

def test_is_delayed_binary(df):
    assert set(df["is_delayed"].unique()).issubset({0, 1}), "is_delayed に 0/1 以外の値がある"

def test_kpi_flag_categories(df):
    cats = set(df["kpi_flag"].unique())
    assert cats == {"正常", "問題あり"}, f"kpi_flag の値: {cats}"

def test_source_file_count(df):
    assert df["source_file"].nunique() == 3, f"source_file 種類数: {df['source_file'].nunique()}"

def test_worker_count(df):
    assert df["worker_id"].nunique() >= 15, f"作業員数が少ない: {df['worker_id'].nunique()}"
