"""
C-31: test_cleaner_output.py
cleaned_contracts_202401.csv の品質を検証する (10テスト以上)。
"""
import re
import pytest
import pandas as pd
from pathlib import Path

CSV = Path("output/cleaned_contracts_202401.csv")
REQUIRED_COLS = {
    "contract_no", "customer_code", "insurance_type",
    "start_date", "end_date", "annual_premium", "agent_name",
    "days_to_expiry", "renewal_status", "source_file",
}
VALID_STATUSES = {"期限切れ", "緊急", "警告", "正常"}
VALID_INSURANCE_TYPES = {"生命保険", "損害保険", "医療保険", "年金保険"}


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CSV, encoding="utf-8-sig")


# 1. CSV が存在する
def test_csv_exists():
    assert CSV.exists(), f"ファイルが存在しません: {CSV}"


# 2. 行数 >= 400
def test_row_count(df):
    assert len(df) >= 400, f"行数不足: {len(df)}"


# 3. 必須列が存在する
def test_required_columns(df):
    missing = REQUIRED_COLS - set(df.columns)
    assert len(missing) == 0, f"欠落列: {missing}"


# 4. contract_no に重複なし
def test_contract_no_unique(df):
    dup = df["contract_no"].duplicated().sum()
    assert dup == 0, f"重複 contract_no: {dup} 件"


# 5. start_date が YYYY-MM-DD フォーマット
def test_start_date_format(df):
    bad = df["start_date"].dropna()[
        ~df["start_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    assert len(bad) == 0, f"不正日付 (start_date): {len(bad)} 件"


# 6. end_date が YYYY-MM-DD フォーマット
def test_end_date_format(df):
    bad = df["end_date"].dropna()[
        ~df["end_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    assert len(bad) == 0, f"不正日付 (end_date): {len(bad)} 件"


# 7. insurance_type が 4 種類（正規化済み）
def test_insurance_type_four_kinds(df):
    actual = set(df["insurance_type"].dropna().unique())
    assert actual == VALID_INSURANCE_TYPES, f"insurance_type 不一致: {actual}"


# 8. agent_name が 5 種類
def test_agent_name_five_kinds(df):
    n = df["agent_name"].nunique()
    assert n >= 5, f"担当者種類不足: {n}"


# 9. annual_premium が正値（> 0）
def test_annual_premium_positive(df):
    non_pos = (pd.to_numeric(df["annual_premium"], errors="coerce") <= 0).sum()
    assert non_pos == 0, f"annual_premium <= 0: {non_pos} 件"


# 10. renewal_status が規定値のみ
def test_renewal_status_valid_values(df):
    invalid = set(df["renewal_status"].dropna().unique()) - VALID_STATUSES
    assert len(invalid) == 0, f"不正ステータス: {invalid}"


# 11. source_file 列が存在し欠損なし
def test_source_file_nonempty(df):
    assert "source_file" in df.columns
    assert df["source_file"].notna().all(), "source_file に欠損値あり"


# 12. source_file が 3 種類以上
def test_source_file_three_kinds(df):
    n = df["source_file"].nunique()
    assert n >= 3, f"source_file 種類不足: {n}"


# 13. customer_code が 50 種類以上
def test_customer_code_variety(df):
    n = df["customer_code"].nunique()
    assert n >= 50, f"顧客種類不足: {n}"


# 14. 期限切れレコードが存在する
def test_expired_exists(df):
    assert (df["renewal_status"] == "期限切れ").sum() >= 1, "期限切れレコードなし"


# 15. 緊急レコードが存在する
def test_urgent_exists(df):
    assert (df["renewal_status"] == "緊急").sum() >= 1, "緊急レコードなし"
