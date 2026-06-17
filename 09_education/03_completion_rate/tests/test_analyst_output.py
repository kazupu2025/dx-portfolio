import re
import pytest
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent
REPORT = BASE / "output" / "analysis_report.md"
SUMMARY_CSV = BASE / "output" / "course_summary_202401.csv"


@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def summary_df():
    return pd.read_csv(SUMMARY_CSV, encoding="utf-8-sig")


def test_report_exists():
    assert REPORT.exists(), "analysis_report.md が存在しない"


def test_summary_csv_exists():
    assert SUMMARY_CSV.exists(), "course_summary_202401.csv が存在しない"


def test_report_contains_completion_rate(report):
    assert "修了率" in report, "レポートに「修了率」が含まれない"


def test_report_contains_course(report):
    assert "講座" in report, "レポートに「講座」が含まれない"


def test_report_contains_learner_type(report):
    assert "受講者タイプ" in report, "レポートに「受講者タイプ」が含まれない"


def test_report_has_insight(report):
    assert "インサイト" in report or "改善" in report or "ビジネス" in report, \
        "レポートにインサイト/改善セクションがない"


def test_report_has_numeric(report):
    assert re.search(r"\d+\.\d+", report), "レポートに数値が含まれない"


def test_summary_csv_row_count(summary_df):
    assert len(summary_df) >= 1, "course_summary_202401.csv の行数が 0"


def test_summary_csv_has_course_name(summary_df):
    assert "course_name" in summary_df.columns, "course_summary に course_name 列なし"
