"""
C-26: test_analyst_output.py
analysis_report.md と client_summary_202401.csv を検証する (7テスト以上)。
"""
import re
import pytest
import pandas as pd
from pathlib import Path

REPORT = Path("output/analysis_report.md")
CLIENT_CSV = Path("output/client_summary_202401.csv")


@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")


# 1. analysis_report.md が存在する
def test_report_exists():
    assert REPORT.exists(), "analysis_report.md が存在しない"


# 2. client_summary_202401.csv が存在する
def test_client_csv_exists():
    assert CLIENT_CSV.exists(), "client_summary_202401.csv が存在しない"


# 3. レポートに「請求」が含まれる
def test_report_has_invoice_keyword(report):
    assert "請求" in report, "レポートに「請求」が含まれない"


# 4. レポートに「差異」が含まれる
def test_report_has_variance_keyword(report):
    assert "差異" in report, "レポートに「差異」が含まれない"


# 5. レポートにインサイト・まとめがある
def test_report_has_insight(report):
    assert (
        "インサイト" in report or "まとめ" in report or "改善示唆" in report
    ), "レポートにインサイト/まとめが含まれない"


# 6. レポートに数値（カンマ区切り）がある
def test_report_has_numbers(report):
    assert re.search(r"\d{1,3}(,\d{3})+", report), "レポートに数値が含まれない"


# 7. client_summary_202401.csv の行数 >= 1
def test_client_csv_row_count():
    df = pd.read_csv(CLIENT_CSV, encoding="utf-8-sig")
    assert len(df) >= 1, f"client_summary の行数不足: {len(df)}"


# 8. レポートに得意先別分析がある
def test_report_has_client_analysis(report):
    assert "得意先" in report or "CLI-" in report, "得意先別分析が含まれない"


# 9. レポートに支払区分分析がある
def test_report_has_payment_type_analysis(report):
    has_payment = (
        "支払区分" in report
        or "銀行振込" in report
        or "口座振替" in report
        or "手形" in report
    )
    assert has_payment, "支払区分分析が含まれない"
