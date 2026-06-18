# -*- coding: utf-8 -*-
"""分析出力テスト (7テスト以上)"""
import re
import pandas as pd
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_PATH = OUTPUT_DIR / "delivery_summary_202401.csv"


def test_report_exists():
    assert REPORT_PATH.exists(), f"analysis_report.md が存在しない: {REPORT_PATH}"


def test_summary_csv_exists():
    assert SUMMARY_PATH.exists(), f"delivery_summary_202401.csv が存在しない: {SUMMARY_PATH}"


def test_report_contains_profit_margin():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "利益率" in text, "レポートに「利益率」が含まれていない"


def test_report_contains_delivery_type():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "配送区分" in text, "レポートに「配送区分」が含まれていない"


def test_report_contains_area():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "エリア" in text, "レポートに「エリア」が含まれていない"


def test_report_contains_numbers():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert re.search(r"\d{2,}", text), "レポートに数値が含まれていない"


def test_summary_row_count():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")
    assert len(df) >= 1, f"サマリCSVの行数不足: {len(df)}"


def test_summary_has_delivery_type_column():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")
    assert "delivery_type" in df.columns, "delivery_type 列が存在しない"


def test_report_contains_insight():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert ("インサイト" in text or "改善示唆" in text or "推奨" in text or "改善" in text), \
        "レポートにインサイト・改善示唆が含まれていない"
