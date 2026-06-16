import re
import pandas as pd
import pytest
from pathlib import Path

REPORT = Path("output/analysis_report.md")
SUMMARY_CSV = Path("output/material_summary_202401.csv")


@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")


def test_report_exists():
    assert REPORT.exists(), "analysis_report.md が存在しない"


def test_summary_csv_exists():
    assert SUMMARY_CSV.exists(), "material_summary_202401.csv が存在しない"


def test_report_has_material_keyword(report):
    assert "原材料" in report or "コスト" in report, "「原材料」「コスト」がレポートに含まれない"


def test_report_has_hendo_keyword(report):
    assert "変動" in report, "「変動」がレポートに含まれない"


def test_report_has_insight(report):
    assert "インサイト" in report or "まとめ" in report or "ビジネス" in report, \
        "インサイト・まとめセクションがない"


def test_report_has_numeric(report):
    assert bool(re.search(r"\d{3,}", report)), "レポートに数値が含まれない"


def test_summary_csv_rows():
    df = pd.read_csv(SUMMARY_CSV, encoding="utf-8-sig")
    assert len(df) >= 1, f"summary CSV 行数 {len(df)} < 1"
