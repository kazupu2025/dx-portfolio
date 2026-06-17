# -*- coding: utf-8 -*-
import os
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
SUMMARY_CSV = os.path.join(OUTPUT_DIR, "property_summary_202401.csv")


def test_report_exists():
    assert os.path.exists(REPORT_PATH)


def test_summary_csv_exists():
    assert os.path.exists(SUMMARY_CSV)


def test_report_has_content():
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    assert len(content) >= 100


def test_report_contains_property_type_section():
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "物件タイプ" in content


def test_report_contains_area_section():
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "エリア" in content


def test_report_contains_staff_section():
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "スタッフ" in content


def test_summary_csv_four_rows():
    df = pd.read_csv(SUMMARY_CSV, encoding="utf-8-sig")
    assert len(df) == 4


def test_summary_csv_has_conversion_rate():
    df = pd.read_csv(SUMMARY_CSV, encoding="utf-8-sig")
    assert "成約率" in df.columns
