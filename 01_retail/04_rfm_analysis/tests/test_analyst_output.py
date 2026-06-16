# -*- coding: utf-8 -*-
"""
test_analyst_output.py
分析アウトプット（analysis_report.md / customer_rfm_202401.csv）のテスト（7テスト以上）
"""

import pytest
import pandas as pd
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
RFM_CSV = OUTPUT_DIR / "customer_rfm_202401.csv"


@pytest.fixture(scope="module")
def report_text():
    if not REPORT_FILE.exists():
        pytest.skip(f"analysis_report.md が存在しません: {REPORT_FILE}")
    return REPORT_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rfm_df():
    if not RFM_CSV.exists():
        pytest.skip(f"customer_rfm_202401.csv が存在しません: {RFM_CSV}")
    return pd.read_csv(RFM_CSV, encoding="utf-8-sig")


# 1. analysis_report.md 存在確認
def test_report_exists():
    assert REPORT_FILE.exists(), f"analysis_report.md が存在しません: {REPORT_FILE}"


# 2. customer_rfm_202401.csv 存在確認
def test_rfm_csv_exists():
    assert RFM_CSV.exists(), f"customer_rfm_202401.csv が存在しません: {RFM_CSV}"


# 3. レポートに「RFM」含む
def test_report_contains_rfm(report_text):
    assert "RFM" in report_text, "レポートに 'RFM' が含まれていません"


# 4. レポートに「セグメント」含む
def test_report_contains_segment(report_text):
    assert "セグメント" in report_text, "レポートに 'セグメント' が含まれていません"


# 5. レポートにインサイト・まとめがある
def test_report_has_insight(report_text):
    has_insight = "インサイト" in report_text or "まとめ" in report_text
    assert has_insight, "レポートに 'インサイト' または 'まとめ' が含まれていません"


# 6. レポートに数値がある
def test_report_has_numbers(report_text):
    assert re.search(r"\d+", report_text), "レポートに数値が含まれていません"


# 7. customer_rfm_202401.csv の行数 >= 50
def test_rfm_csv_row_count(rfm_df):
    assert len(rfm_df) >= 50, f"RFM CSV の行数が不足しています: {len(rfm_df)} < 50"


# 8. レポートに Recency / Frequency / Monetary 分析がある
def test_report_has_rfm_analysis(report_text):
    assert "Recency" in report_text, "レポートに 'Recency' が含まれていません"
    assert "Frequency" in report_text, "レポートに 'Frequency' が含まれていません"
    assert "Monetary" in report_text, "レポートに 'Monetary' が含まれていません"


# 9. レポートに改善示唆がある
def test_report_has_suggestion(report_text):
    has_suggestion = "改善示唆" in report_text or "改善" in report_text
    assert has_suggestion, "レポートに '改善示唆' または '改善' が含まれていません"


# 10. RFM CSV に必須列がある
def test_rfm_csv_columns(rfm_df):
    required = ["customer_code", "recency", "frequency", "monetary", "r_score", "f_score", "m_score", "rfm_total", "segment"]
    missing = [c for c in required if c not in rfm_df.columns]
    assert not missing, f"RFM CSV に必須列が不足しています: {missing}"


# 11. セグメントが4種類の有効値のみ
def test_rfm_segment_values(rfm_df):
    valid = {"優良顧客", "成長顧客", "離反リスク", "休眠顧客"}
    invalid = set(rfm_df["segment"].unique()) - valid
    assert not invalid, f"無効なセグメント値が含まれています: {invalid}"
