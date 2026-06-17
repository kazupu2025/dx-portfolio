# -*- coding: utf-8 -*-
"""
C-49 分析出力テスト (7テスト以上)
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
FARM_CSV = os.path.join(BASE_DIR, "output", "farm_summary_202401.csv")


def test_report_exists():
    assert os.path.exists(REPORT_FILE)


def test_farm_csv_exists():
    assert os.path.exists(FARM_CSV)


def test_report_contains_all_farms():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for farm in ["農場A", "農場B", "農場C", "農場D"]:
        assert farm in content, f"Farm not in report: {farm}"


def test_report_contains_all_crops():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for crop in ["トマト", "キュウリ", "ピーマン", "レタス", "ほうれん草"]:
        assert crop in content, f"Crop not in report: {crop}"


def test_report_contains_quality_flags():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for flag in ["優良", "合格", "要改善"]:
        assert flag in content


def test_farm_csv_columns():
    df = pd.read_csv(FARM_CSV, encoding="utf-8-sig")
    required = ["farm_name", "total_harvest", "mean_grade_a_rate", "mean_defect_rate", "record_count"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"


def test_farm_csv_row_count():
    df = pd.read_csv(FARM_CSV, encoding="utf-8-sig")
    assert len(df) == 4, f"Expected 4 farms, got {len(df)}"


def test_farm_csv_total_harvest_positive():
    df = pd.read_csv(FARM_CSV, encoding="utf-8-sig")
    assert (df["total_harvest"] > 0).all()


def test_report_contains_record_count():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "総レコード数" in content
