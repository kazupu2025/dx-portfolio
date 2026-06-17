# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_PATH = os.path.join(BASE_DIR, "output", "analysis_report.md")
SHOP_CSV_PATH = os.path.join(BASE_DIR, "output", "shop_summary_202401.csv")

@pytest.fixture(scope="module")
def report_content():
    with open(REPORT_PATH, encoding="utf-8") as f:
        return f.read()

@pytest.fixture(scope="module")
def shop_df():
    return pd.read_csv(SHOP_CSV_PATH, encoding="utf-8-sig")

def test_report_exists():
    assert os.path.exists(REPORT_PATH), "analysis_report.md does not exist"

def test_shop_csv_exists():
    assert os.path.exists(SHOP_CSV_PATH), "shop_summary_202401.csv does not exist"

def test_report_has_shop_section(report_content):
    assert "店舗別" in report_content

def test_report_has_worktype_section(report_content):
    assert "作業区分" in report_content

def test_report_has_tech_section(report_content):
    assert "技術者" in report_content

def test_report_has_kpi(report_content):
    assert "完了率" in report_content or "KPI" in report_content

def test_shop_summary_3_rows(shop_df):
    assert len(shop_df) == 3, f"Expected 3 shop rows, got {len(shop_df)}"

def test_shop_summary_has_revenue(shop_df):
    assert "売上合計" in shop_df.columns

def test_shop_summary_revenue_positive(shop_df):
    assert (shop_df["売上合計"] > 0).all()
