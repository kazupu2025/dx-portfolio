# -*- coding: utf-8 -*-
"""
C-59 分析出力テスト (7テスト以上)
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
CROP_CSV = os.path.join(BASE_DIR, "output", "crop_summary_202401.csv")


def test_report_exists():
    assert os.path.exists(REPORT_FILE)


def test_crop_csv_exists():
    assert os.path.exists(CROP_CSV)


def test_report_contains_all_crops():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for crop in ["トマト", "キュウリ", "レタス", "イチゴ", "ホウレンソウ"]:
        assert crop in content, f"Crop not in report: {crop}"


def test_report_contains_all_work_types():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for wt in ["播種", "施肥", "収穫", "管理作業"]:
        assert wt in content, f"Work type not in report: {wt}"


def test_report_contains_efficiency_grades():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for grade in ["高効率", "中効率", "低効率"]:
        assert grade in content


def test_crop_csv_columns():
    df = pd.read_csv(CROP_CSV, encoding="utf-8-sig")
    required = ["crop", "achievement_rate_mean", "productivity_mean", "work_hours_sum", "record_count"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"


def test_crop_csv_row_count():
    df = pd.read_csv(CROP_CSV, encoding="utf-8-sig")
    assert len(df) == 5, f"Expected 5 crops, got {len(df)}"


def test_crop_csv_productivity_positive():
    df = pd.read_csv(CROP_CSV, encoding="utf-8-sig")
    assert (df["productivity_mean"] > 0).all()


def test_report_contains_total_record_count():
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "総記録数" in content
