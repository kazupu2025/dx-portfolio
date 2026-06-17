"""
C-39: クレンジング出力テスト（10テスト以上）
"""

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
OUTPUT_CSV = BASE_DIR / "output" / "cleaned_claims_202401.csv"


@pytest.fixture(scope="module")
def df():
    if not OUTPUT_CSV.exists():
        pytest.skip(f"Cleaned CSV not found: {OUTPUT_CSV}. Run cleanse.py first.")
    return pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")


# 1. ファイルが存在する
def test_output_file_exists():
    assert OUTPUT_CSV.exists(), f"Cleaned CSV not found: {OUTPUT_CSV}"


# 2. 行数 >= 420
def test_row_count(df):
    assert len(df) >= 420, f"Expected >= 420 rows, got {len(df)}"


# 3. 必須列が存在する
def test_required_columns(df):
    required = [
        "receipt_date", "case_no", "property_name", "room_no",
        "claim_type", "status", "response_days", "work_hours",
        "source_file", "is_resolved", "urgency", "cost_estimate",
    ]
    missing = [c for c in required if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


# 4. case_no がユニーク
def test_case_no_unique(df):
    duplicates = df["case_no"].duplicated().sum()
    assert duplicates == 0, f"{duplicates} duplicate case_no values found"


# 5. 日付フォーマットが YYYY-MM-DD
def test_date_format(df):
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    bad = df["receipt_date"].dropna().apply(lambda x: not pattern.match(str(x))).sum()
    assert bad == 0, f"{bad} dates do not match YYYY-MM-DD format"


# 6. property_name が 5 種類
def test_property_name_count(df):
    expected = {"サンシャインA棟", "グリーンB棟", "ブルーC棟", "ホワイトD棟", "シルバーE棟"}
    actual = set(df["property_name"].dropna().unique())
    assert actual == expected, f"property_name mismatch. Got: {sorted(actual)}"


# 7. claim_type が 6 種類
def test_claim_type_count(df):
    expected = {"設備故障", "騒音", "水漏れ", "害虫", "駐車", "その他"}
    actual = set(df["claim_type"].dropna().unique())
    assert actual == expected, f"claim_type mismatch. Got: {sorted(actual)}"


# 8. status が想定 3 値のみ
def test_status_values(df):
    expected = {"解決済", "対応中", "未対応"}
    actual = set(df["status"].dropna().unique())
    unexpected = actual - expected
    assert not unexpected, f"Unexpected status values: {unexpected}"


# 9. response_days >= 1
def test_response_days_positive(df):
    series = pd.to_numeric(df["response_days"], errors="coerce").dropna()
    bad = (series < 1).sum()
    assert bad == 0, f"{bad} rows have response_days < 1"


# 10. work_hours > 0
def test_work_hours_positive(df):
    series = pd.to_numeric(df["work_hours"], errors="coerce").dropna()
    bad = (series <= 0).sum()
    assert bad == 0, f"{bad} rows have work_hours <= 0"


# 11. is_resolved が 0 または 1 のみ
def test_is_resolved_binary(df):
    invalid = (~df["is_resolved"].isin([0, 1])).sum()
    assert invalid == 0, f"{invalid} rows have invalid is_resolved value"


# 12. urgency が 3 種類のみ
def test_urgency_values(df):
    expected = {"緊急", "通常", "遅延"}
    actual = set(df["urgency"].dropna().unique())
    unexpected = actual - expected
    assert not unexpected, f"Unexpected urgency values: {unexpected}"


# 13. cost_estimate > 0
def test_cost_estimate_positive(df):
    series = pd.to_numeric(df["cost_estimate"], errors="coerce").dropna()
    bad = (series <= 0).sum()
    assert bad == 0, f"{bad} rows have cost_estimate <= 0"


# 14. source_file が 3 種類
def test_source_file_count(df):
    n = df["source_file"].nunique()
    assert n == 3, f"Expected 3 source files, got {n}"


# 15. 欠損率 <= 15%
def test_missing_rate(df):
    max_missing = df.isnull().mean().max()
    assert max_missing <= 0.15, f"Max missing rate {max_missing:.1%} exceeds 15%"
