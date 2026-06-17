# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
PLAN_SUMMARY_FILE = os.path.join(OUTPUT_DIR, "plan_summary_202401.csv")


def test_report_file_exists():
    assert os.path.exists(REPORT_FILE), f"Report file not found: {REPORT_FILE}"


def test_plan_summary_file_exists():
    assert os.path.exists(PLAN_SUMMARY_FILE), f"Plan summary file not found: {PLAN_SUMMARY_FILE}"


def test_report_contains_plan_section():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "プラン別分析" in content


def test_report_contains_industry_section():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "業種別分析" in content


def test_report_contains_cohort_section():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "コホート分析" in content


def test_plan_summary_has_three_rows():
    df = pd.read_csv(PLAN_SUMMARY_FILE, encoding="utf-8-sig")
    assert len(df) == 3, f"Expected 3 rows, got {len(df)}"


def test_plan_summary_churn_rate_in_range():
    df = pd.read_csv(PLAN_SUMMARY_FILE, encoding="utf-8-sig")
    assert "churn_rate" in df.columns
    assert df["churn_rate"].between(0, 1).all(), "churn_rate values out of [0, 1]"


def test_plan_summary_avg_ltv_positive():
    df = pd.read_csv(PLAN_SUMMARY_FILE, encoding="utf-8-sig")
    assert "avg_ltv" in df.columns
    assert (df["avg_ltv"] > 0).all(), "avg_ltv has non-positive values"


def test_report_contains_ltv_info():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "LTV" in content
