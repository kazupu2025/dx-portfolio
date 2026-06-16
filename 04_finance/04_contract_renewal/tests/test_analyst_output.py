"""
C-31: test_analyst_output.py
analysis_report.md / contract_summary_202401.csv の品質を検証する (7テスト以上)。
"""
import re
import pytest
import pandas as pd
from pathlib import Path

REPORT = Path("output/analysis_report.md")
SUMMARY_CSV = Path("output/contract_summary_202401.csv")


# 1. analysis_report.md が存在する
def test_report_exists():
    assert REPORT.exists(), f"ファイルが存在しません: {REPORT}"


# 2. contract_summary_202401.csv が存在する
def test_summary_csv_exists():
    assert SUMMARY_CSV.exists(), f"ファイルが存在しません: {SUMMARY_CSV}"


# 3. レポートに「契約」または「更新」が含まれる
def test_report_has_contract_keyword():
    text = REPORT.read_text(encoding="utf-8")
    assert "契約" in text or "更新" in text, "レポートに「契約」または「更新」が含まれない"


# 4. レポートに「期限」または「アラート」が含まれる
def test_report_has_expiry_keyword():
    text = REPORT.read_text(encoding="utf-8")
    assert "期限" in text or "アラート" in text, "レポートに「期限」または「アラート」が含まれない"


# 5. レポートにインサイト・まとめセクションがある
def test_report_has_insight_section():
    text = REPORT.read_text(encoding="utf-8")
    assert "インサイト" in text or "まとめ" in text or "改善示唆" in text, \
        "レポートにインサイト/まとめセクションがない"


# 6. レポートに数値（カンマ区切り整数）がある
def test_report_has_numbers():
    text = REPORT.read_text(encoding="utf-8")
    assert re.search(r"\d{1,3}(,\d{3})+", text), "レポートに数値が含まれない"


# 7. contract_summary_202401.csv の行数 >= 1
def test_summary_csv_row_count():
    df = pd.read_csv(SUMMARY_CSV, encoding="utf-8-sig")
    assert len(df) >= 1, f"contract_summary 行数不足: {len(df)}"


# 8. レポートに担当者別分析がある
def test_report_has_agent_analysis():
    text = REPORT.read_text(encoding="utf-8")
    assert "担当者" in text or "田中" in text or "佐藤" in text, \
        "レポートに担当者別分析が含まれない"


# 9. レポートに保険種別分析がある
def test_report_has_insurance_type_analysis():
    text = REPORT.read_text(encoding="utf-8")
    assert ("保険種別" in text or "生命保険" in text or "損害保険" in text
            or "医療保険" in text or "年金保険" in text), \
        "レポートに保険種別分析が含まれない"
