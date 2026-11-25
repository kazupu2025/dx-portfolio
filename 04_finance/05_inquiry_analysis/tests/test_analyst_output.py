# -*- coding: utf-8 -*-
"""
C-52: test_analyst_output.py
analysis_report.md と type_summary_202401.csv の品質を検証する (7テスト以上)。
"""
import pytest
import pandas as pd
from pathlib import Path

REPORT = Path("output/analysis_report.md")
TYPE_CSV = Path("output/type_summary_202401.csv")


# 1. analysis_report.md が存在する
def test_report_exists():
    assert REPORT.exists(), f"Report not found: {REPORT}"


# 2. type_summary_202401.csv が存在する
def test_type_csv_exists():
    assert TYPE_CSV.exists(), f"Type summary CSV not found: {TYPE_CSV}"


# 3. レポートに「保険」または「問い合わせ」が含まれる
def test_report_has_insurance_or_inquiry():
    text = REPORT.read_text(encoding="utf-8")
    assert "保険" in text or "問い合わせ" in text, "Report missing insurance/inquiry keywords"


# 4. レポートに「解決率」が含まれる
def test_report_has_resolution_rate():
    text = REPORT.read_text(encoding="utf-8")
    assert "解決率" in text, "Report missing resolution rate"


# 5. レポートにインサイト・まとめがある
def test_report_has_insight():
    text = REPORT.read_text(encoding="utf-8")
    assert any(kw in text for kw in ["インサイト", "まとめ", "改善示唆"]), \
        "Report missing insight/summary section"


# 6. レポートにチャネル別分析がある
def test_report_has_channel_analysis():
    text = REPORT.read_text(encoding="utf-8")
    assert any(kw in text for kw in ["チャネル", "電話", "メール", "窓口"]), \
        "Report missing channel analysis"


@pytest.fixture(scope="module")
def type_df():
    return pd.read_csv(TYPE_CSV, encoding="utf-8-sig")


# 7. type_summary の行数 >= 5
def test_type_summary_row_count(type_df):
    assert len(type_df) >= 5, f"Type summary row count insufficient: {len(type_df)}"
