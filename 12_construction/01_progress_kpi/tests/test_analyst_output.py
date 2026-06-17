# -*- coding: utf-8 -*-
import os
import pytest
import pandas as pd

REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "analysis_report.md")
SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "site_summary_202401.csv")

def test_report_exists():
    assert os.path.exists(REPORT_PATH), "analysis_report.md が存在しない"

def test_report_has_content():
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    assert len(content) > 100, "レポートが短すぎる"

def test_report_contains_site_section():
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "現場別" in content

def test_report_contains_process_section():
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "工程別" in content

def test_report_contains_worker_section():
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    assert "作業員別" in content

def test_site_summary_exists():
    assert os.path.exists(SUMMARY_PATH), "site_summary_202401.csv が存在しない"

@pytest.fixture(scope="module")
def ss():
    return pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")

def test_site_summary_rows(ss):
    assert len(ss) >= 5, f"site_summary 行数: {len(ss)}"

def test_site_summary_avg_progress_col(ss):
    assert "avg_progress" in ss.columns

def test_site_summary_total_defects_col(ss):
    assert "total_defects" in ss.columns

def test_site_summary_delayed_count_col(ss):
    assert "delayed_count" in ss.columns
