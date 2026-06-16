"""
C-20: 分析出力の品質テスト
"""

from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"
CSV_PATH = BASE_DIR / "output" / "labor_summary_202401.csv"


def test_report_exists():
    assert REPORT_PATH.exists(), f"レポートが存在しない: {REPORT_PATH}"


def test_report_contains_labor_cost_keyword():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "人件費" in text, "レポートに「人件費」が含まれない"


def test_report_contains_store_keyword():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "店舗" in text, "レポートに「店舗」が含まれない"


def test_report_contains_insight():
    text = REPORT_PATH.read_text(encoding="utf-8")
    has_insight = any(kw in text for kw in ("インサイト", "まとめ", "推奨"))
    assert has_insight, "レポートにインサイト・まとめが含まれない"


def test_summary_csv_exists():
    assert CSV_PATH.exists(), f"サマリーCSVが存在しない: {CSV_PATH}"


def test_summary_csv_row_count():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    assert len(df) >= 1, f"サマリーCSVの行数が0: {len(df)}"


def test_summary_csv_has_required_columns():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    required = {"store_id", "employment_type", "total_wage"}
    missing = required - set(df.columns)
    assert not missing, f"サマリーCSVに必須列が不足: {missing}"
