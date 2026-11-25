# -*- coding: utf-8 -*-
"""
pytest: analyze.py 出力チェック (7テスト以上)
"""

import os
import json
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

MD_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
CSV_FILE = os.path.join(OUTPUT_DIR, "service_summary_202401.csv")
JSON_FILE = os.path.join(OUTPUT_DIR, "result_analysis.json")


def test_md_exists():
    assert os.path.exists(MD_FILE), f"File not found: {MD_FILE}"


def test_csv_exists():
    assert os.path.exists(CSV_FILE), f"File not found: {CSV_FILE}"


def test_json_exists():
    assert os.path.exists(JSON_FILE), f"File not found: {JSON_FILE}"


def test_service_summary_8_rows():
    df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
    assert len(df) == 8, f"Expected 8 rows, got {len(df)}"


def test_service_summary_columns():
    df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
    required = {"service_name", "revenue_total", "cost_total", "gross_profit_total", "gross_margin_mean"}
    missing = required - set(df.columns)
    assert missing == set(), f"Missing columns: {missing}"


def test_json_total_revenue_positive():
    with open(JSON_FILE, encoding="utf-8") as f:
        j = json.load(f)
    assert j.get("total_revenue", 0) > 0, "total_revenue should be positive"


def test_json_service_count():
    with open(JSON_FILE, encoding="utf-8") as f:
        j = json.load(f)
    assert j.get("service_count") == 8, f"Expected service_count=8, got {j.get('service_count')}"


def test_md_contains_kpi():
    with open(MD_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "KPI" in content or "総売上" in content, "MD file should contain KPI summary"


def test_md_contains_service_section():
    with open(MD_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "サービス別" in content, "MD file should contain service analysis section"
