"""
C-21: 分析出力テスト
レポート存在・キーワード・CSV行数
"""
import pytest
import csv
from pathlib import Path

BASE = Path(__file__).parent.parent
REPORT_PATH = BASE / "output" / "analysis_report.md"
SUMMARY_CSV = BASE / "output" / "service_summary_202401.csv"


def test_report_exists():
    assert REPORT_PATH.exists(), f"レポートが存在しません: {REPORT_PATH}"


def test_report_contains_profit():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert ("粗利" in text) or ("利益" in text), "レポートに利益関連キーワードがありません"


def test_report_contains_service():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "サービス" in text, "レポートに「サービス」が含まれていません"


def test_report_contains_insight():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert ("インサイト" in text) or ("考察" in text), "レポートにインサイト/考察セクションがありません"


def test_report_contains_numbers():
    import re
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert bool(re.search(r"[0-9]", text)), "レポートに数値が含まれていません"


def test_summary_csv_exists():
    assert SUMMARY_CSV.exists(), f"サマリーCSVが存在しません: {SUMMARY_CSV}"


def test_summary_csv_rows():
    with open(SUMMARY_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    data_rows = len(rows) - 1 if len(rows) > 0 else 0
    assert data_rows >= 1, f"サマリーCSVのデータ行数が0: {data_rows}"
