"""分析出力テスト (7テスト以上)"""
import re
import pandas as pd
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"
SUMMARY_PATH = BASE_DIR / "output" / "worker_summary_202401.csv"


def test_report_exists():
    assert REPORT_PATH.exists(), f"レポートが存在しない: {REPORT_PATH}"


def test_summary_exists():
    assert SUMMARY_PATH.exists(), f"サマリCSVが存在しない: {SUMMARY_PATH}"


def test_report_contains_productivity():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "生産性" in text


def test_report_contains_defect_rate():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "不良率" in text


def test_report_contains_ojt():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "OJT" in text or "改善示唆" in text or "推奨" in text


def test_report_contains_worker_id():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert bool(re.search(r"WRK-\d{3}", text)), "作業員IDがレポートに含まれない"


def test_report_contains_numbers():
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert bool(re.search(r"\d{2,}", text)), "数値がレポートに含まれない"


def test_summary_row_count():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")
    assert len(df) >= 1, f"サマリ行数不足: {len(df)}"


def test_summary_has_worker_id_column():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")
    assert "worker_id" in df.columns


def test_summary_has_productivity_column():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")
    assert "avg_productivity" in df.columns
