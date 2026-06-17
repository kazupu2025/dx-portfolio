# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
DEPT_CSV_PATH = os.path.join(OUTPUT_DIR, "dept_summary_202401.csv")


def test_report_exists():
    assert os.path.exists(REPORT_PATH)


def test_dept_csv_exists():
    assert os.path.exists(DEPT_CSV_PATH)


def test_report_has_overview():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "## 1. Overview" in content


def test_report_has_dept_section():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "## 2. By Department" in content


def test_report_has_insurance_section():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "## 3. By Insurance Type" in content


def test_report_has_trend_section():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "## 4. Daily Revenue Trend" in content


def test_dept_summary_5_rows():
    df = pd.read_csv(DEPT_CSV_PATH, encoding="utf-8-sig")
    assert len(df) == 5


def test_dept_summary_has_collection_rate():
    df = pd.read_csv(DEPT_CSV_PATH, encoding="utf-8-sig")
    assert "collection_rate" in df.columns


def test_dept_summary_total_claim_positive():
    df = pd.read_csv(DEPT_CSV_PATH, encoding="utf-8-sig")
    assert (df["total_claim_amount"] > 0).all()
