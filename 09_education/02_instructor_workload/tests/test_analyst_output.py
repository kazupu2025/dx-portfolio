import pytest
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent
REPORT = BASE / "output" / "analysis_report.md"
SUMMARY_CSV = BASE / "output" / "instructor_summary_202401.csv"


@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def summary_df():
    return pd.read_csv(SUMMARY_CSV, encoding="utf-8-sig")


def test_report_exists():
    assert REPORT.exists(), "analysis_report.md が存在しない"


def test_summary_csv_exists():
    assert SUMMARY_CSV.exists(), "instructor_summary_202401.csv が存在しない"


def test_report_contains_instructor(report):
    assert "講師" in report, "レポートに「講師」が含まれない"


def test_report_contains_lesson_or_workload(report):
    assert "コマ" in report or "稼働" in report, "レポートに「コマ」または「稼働」が含まれない"


def test_report_contains_specialty(report):
    assert "専門分野" in report, "レポートに「専門分野」が含まれない"


def test_report_has_insight(report):
    assert "インサイト" in report or "ビジネス" in report or "改善提案" in report, \
        "レポートにインサイト/改善提案セクションがない"


def test_report_has_numeric(report):
    import re
    assert re.search(r"\d{1,3}(,\d{3})*", report), "レポートに数値が含まれない"


def test_summary_csv_row_count(summary_df):
    assert len(summary_df) >= 1, "instructor_summary_202401.csv の行数が 0"


def test_summary_csv_has_instructor_id(summary_df):
    assert "instructor_id" in summary_df.columns, "instructor_summary に instructor_id 列なし"
