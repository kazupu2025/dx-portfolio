# -*- coding: utf-8 -*-
"""
分析出力ファイルのテスト (7テスト以上)
"""
import re
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
ROUTE_SUMMARY_CSV = OUTPUT_DIR / "route_summary_202401.csv"


@pytest.fixture(scope="module")
def report_text():
    if not REPORT_MD.exists():
        pytest.skip("analysis_report.md が存在しません。先にanalyze.pyを実行してください。")
    return REPORT_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def route_summary():
    if not ROUTE_SUMMARY_CSV.exists():
        pytest.skip("route_summary_202401.csv が存在しません。先にanalyze.pyを実行してください。")
    return pd.read_csv(ROUTE_SUMMARY_CSV, encoding="utf-8-sig")


def test_report_exists():
    """analysis_report.md が存在する"""
    assert REPORT_MD.exists(), f"ファイルが見つかりません: {REPORT_MD}"


def test_route_summary_csv_exists():
    """route_summary_202401.csv が存在する"""
    assert ROUTE_SUMMARY_CSV.exists(), f"ファイルが見つかりません: {ROUTE_SUMMARY_CSV}"


def test_report_contains_route_or_delivery(report_text):
    """レポートに「ルート」または「配送」が含まれる"""
    assert "ルート" in report_text or "配送" in report_text, \
        "レポートに「ルート」「配送」が含まれていません"


def test_report_contains_efficiency_or_cost(report_text):
    """レポートに「効率」または「コスト」が含まれる"""
    assert "効率" in report_text or "コスト" in report_text, \
        "レポートに「効率」「コスト」が含まれていません"


def test_report_has_insights(report_text):
    """レポートにインサイトまたはまとめが含まれる"""
    assert "インサイト" in report_text or "まとめ" in report_text, \
        "レポートにインサイト・まとめが含まれていません"


def test_report_has_numbers(report_text):
    """レポートに数値が含まれる"""
    assert re.search(r"\d+", report_text), "レポートに数値が含まれていません"


def test_route_summary_row_count(route_summary):
    """route_summary_202401.csv の行数が 1 以上である"""
    assert len(route_summary) >= 1, f"route_summary 行数: {len(route_summary)}"


def test_report_contains_area_analysis(report_text):
    """レポートにエリア別分析が含まれる"""
    assert "エリア" in report_text, "レポートにエリア別分析が含まれていません"


def test_report_contains_delay_analysis(report_text):
    """レポートに遅延分析が含まれる"""
    assert "遅延" in report_text, "レポートに遅延分析が含まれていません"
