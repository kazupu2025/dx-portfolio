# -*- coding: utf-8 -*-
import os
import json
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
STAFF_CSV_FILE = os.path.join(OUTPUT_DIR, "staff_summary_202401.csv")
RESULT_JSON_FILE = os.path.join(OUTPUT_DIR, "result_analysis.json")


def test_analysis_report_exists():
    assert os.path.exists(REPORT_FILE), "analysis_report.md must exist"


def test_staff_summary_csv_exists():
    assert os.path.exists(STAFF_CSV_FILE), "staff_summary_202401.csv must exist"


def test_result_json_exists():
    assert os.path.exists(RESULT_JSON_FILE), "result_analysis.json must exist"


def test_report_contains_staff_type():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "スタッフ種別" in content, "Report must contain staff type section"


def test_report_contains_department():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "診療科" in content, "Report must contain department section"


def test_report_contains_attendance_rate():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "出勤率" in content, "Report must contain attendance rate"


def test_staff_summary_columns():
    df = pd.read_csv(STAFF_CSV_FILE, encoding="utf-8-sig")
    required = ["staff_type", "total_records", "absent_count",
                "avg_overtime_hours", "avg_utilization_rate", "attendance_rate"]
    missing = [c for c in required if c not in df.columns]
    assert missing == [], "Missing columns in staff_summary: {}".format(missing)


def test_staff_summary_four_rows():
    df = pd.read_csv(STAFF_CSV_FILE, encoding="utf-8-sig")
    assert len(df) == 4, "staff_summary must have 4 rows (one per staff type)"


def test_result_json_keys():
    with open(RESULT_JSON_FILE, encoding="utf-8") as f:
        result = json.load(f)
    required_keys = [
        "total_records", "attendance_count", "absent_count",
        "overall_attendance_rate", "avg_utilization_rate",
        "avg_overtime_hours", "overtime_count"
    ]
    missing = [k for k in required_keys if k not in result]
    assert missing == [], "Missing keys in result_analysis.json: {}".format(missing)


def test_result_total_records():
    with open(RESULT_JSON_FILE, encoding="utf-8") as f:
        result = json.load(f)
    assert result["total_records"] >= 420, \
        "total_records must be >= 420, got {}".format(result["total_records"])
