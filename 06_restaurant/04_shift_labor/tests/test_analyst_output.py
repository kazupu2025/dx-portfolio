# -*- coding: utf-8 -*-
"""
C-40: 分析出力テスト（7テスト以上）
"""

import pytest
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
STORE_CSV_FILE = OUTPUT_DIR / "store_summary_202401.csv"


# 1. 分析レポートファイルが存在すること
def test_report_file_exists():
    assert REPORT_FILE.exists(), f"レポートファイルが見つかりません: {REPORT_FILE}"


# 2. 店舗別サマリーCSVが存在すること
def test_store_csv_exists():
    assert STORE_CSV_FILE.exists(), f"サマリーCSVが見つかりません: {STORE_CSV_FILE}"


# 3. レポートが空でないこと
def test_report_not_empty():
    content = REPORT_FILE.read_text(encoding="utf-8")
    assert len(content.strip()) > 100, "レポートが短すぎる"


# 4. レポートに店舗別セクションが含まれる
def test_report_has_store_section():
    content = REPORT_FILE.read_text(encoding="utf-8")
    assert "店舗別" in content, "店舗別セクションが存在しない"


# 5. レポートにスタッフ別セクションが含まれる
def test_report_has_staff_section():
    content = REPORT_FILE.read_text(encoding="utf-8")
    assert "スタッフ別" in content, "スタッフ別セクションが存在しない"


# 6. レポートに改善示唆が含まれる
def test_report_has_insights():
    content = REPORT_FILE.read_text(encoding="utf-8")
    assert "Insights" in content or "改善示唆" in content, "Insightsセクションが存在しない"


# 7. 店舗別サマリーCSVが3行（3店舗）
def test_store_csv_has_3_rows():
    df = pd.read_csv(STORE_CSV_FILE, encoding="utf-8-sig")
    assert len(df) == 3, f"店舗数が不正: {len(df)}"


# 8. 店舗別サマリーに必須列が存在
def test_store_csv_required_columns():
    df = pd.read_csv(STORE_CSV_FILE, encoding="utf-8-sig")
    required = ["store_name", "total_labor_cost", "avg_hourly_rate", "overtime_rate_pct"]
    for col in required:
        assert col in df.columns, f"列が存在しない: {col}"


# 9. 総人件費が正の値
def test_store_csv_positive_labor_cost():
    df = pd.read_csv(STORE_CSV_FILE, encoding="utf-8-sig")
    assert (df["total_labor_cost"] > 0).all(), "total_labor_cost に 0 以下が存在"
