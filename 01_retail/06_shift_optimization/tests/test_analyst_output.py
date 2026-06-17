# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "store_summary_202401.csv")

EXPECTED_STORES = {"新宿店", "渋谷店", "池袋店", "銀座店", "品川店"}


@pytest.fixture(scope="module")
def report_text():
    assert os.path.exists(REPORT_PATH), f"Report not found: {REPORT_PATH}"
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def summary_df():
    assert os.path.exists(SUMMARY_PATH), f"Summary not found: {SUMMARY_PATH}"
    return pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")


def test_report_exists():
    assert os.path.exists(REPORT_PATH)


def test_summary_exists():
    assert os.path.exists(SUMMARY_PATH)


def test_report_has_title(report_text):
    assert "シフト充足率" in report_text


def test_report_has_store_section(report_text):
    assert "店舗別" in report_text


def test_report_has_role_section(report_text):
    assert "役割別" in report_text


def test_summary_has_five_stores(summary_df):
    assert len(summary_df) == 5


def test_summary_store_names(summary_df):
    assert set(summary_df["store_name"].unique()) == EXPECTED_STORES


def test_summary_total_labor_cost_positive(summary_df):
    assert (summary_df["total_labor_cost"] > 0).all()
