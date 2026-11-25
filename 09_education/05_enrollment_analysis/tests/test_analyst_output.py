# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
分析出力のpytestテスト（7テスト以上）
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
DEPT_SUMMARY_FILE = os.path.join(OUTPUT_DIR, "dept_summary_202401.csv")


# Test 1: analysis_report.md が存在する
def test_report_file_exists():
    assert os.path.exists(REPORT_FILE), "analysis_report.md が存在しない"


# Test 2: dept_summary_202401.csv が存在する
def test_dept_summary_file_exists():
    assert os.path.exists(DEPT_SUMMARY_FILE), "dept_summary_202401.csv が存在しない"


# Test 3: レポートに KPIサマリー セクションがある
def test_report_has_kpi():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "KPIサマリー" in content, "レポートに KPIサマリー セクションがない"


# Test 4: レポートに学科別分析がある
def test_report_has_dept_section():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "学科別" in content, "レポートに 学科別 セクションがない"


# Test 5: レポートに選考方法別分析がある
def test_report_has_selection_section():
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    assert "選考方法別" in content, "レポートに 選考方法別 セクションがない"


# Test 6: dept_summary に4行ある（4学科）
def test_dept_summary_row_count():
    df = pd.read_csv(DEPT_SUMMARY_FILE, encoding="utf-8-sig")
    assert len(df) == 4, f"dept_summary の行数が4でない: {len(df)}"


# Test 7: dept_summary に合格率列がある
def test_dept_summary_has_pass_rate_col():
    df = pd.read_csv(DEPT_SUMMARY_FILE, encoding="utf-8-sig")
    has_rate = any("合格率" in str(c) for c in df.columns)
    assert has_rate, f"dept_summary に合格率列がない: {list(df.columns)}"


# Test 8: dept_summary に平均点列がある
def test_dept_summary_has_avg_score_col():
    df = pd.read_csv(DEPT_SUMMARY_FILE, encoding="utf-8-sig")
    has_avg = any("平均点" in str(c) for c in df.columns)
    assert has_avg, f"dept_summary に平均点列がない: {list(df.columns)}"


# Test 9: dept_summary の合格率が 0 以上 100 以下
def test_dept_summary_pass_rate_range():
    df = pd.read_csv(DEPT_SUMMARY_FILE, encoding="utf-8-sig")
    rate_col = next((c for c in df.columns if "合格率" in str(c)), None)
    assert rate_col is not None, "合格率列が見つからない"
    rates = df[rate_col].dropna()
    assert rates.between(0, 100).all(), f"合格率に範囲外の値がある: {rates.tolist()}"
