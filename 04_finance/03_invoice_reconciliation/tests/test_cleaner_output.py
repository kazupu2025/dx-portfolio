"""
C-26: test_cleaner_output.py
cleaned_invoice_202401.csv の品質を検証する (10テスト以上)。
"""
import re
import pytest
import pandas as pd
from pathlib import Path

CSV = Path("output/cleaned_invoice_202401.csv")
REQUIRED_COLS = {
    "invoice_no", "invoice_date", "client_code",
    "invoice_amount", "received_amount", "payment_type",
    "variance_amount", "match_status", "source_file",
}
VALID_STATUSES = {"一致", "差異", "過払", "未入金"}


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


# 4. invoice_no に重複なし
def test_invoice_no_unique(df):
    dup = df["invoice_no"].duplicated().sum()
    assert dup == 0, f"重複 invoice_no: {dup} 件"


# 5. invoice_date が YYYY-MM-DD フォーマット
def test_invoice_date_format(df):
    bad = df["invoice_date"].dropna()[
        ~df["invoice_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    assert len(bad) == 0, f"不正日付: {len(bad)} 件"


# 6. invoice_amount が正値（> 0）
def test_invoice_amount_positive(df):
    non_pos = (pd.to_numeric(df["invoice_amount"], errors="coerce") <= 0).sum()
    assert non_pos == 0, f"invoice_amount <= 0: {non_pos} 件"


# 7. received_amount が非負（>= 0）
def test_received_amount_nonneg(df):
    neg = (pd.to_numeric(df["received_amount"], errors="coerce") < 0).sum()
    assert neg == 0, f"received_amount < 0: {neg} 件"


# 8. match_status が規定値のみ
def test_match_status_valid_values(df):
    invalid = set(df["match_status"].dropna().unique()) - VALID_STATUSES
    assert len(invalid) == 0, f"不正ステータス: {invalid}"


# 9. source_file 列が存在し欠損なし
def test_source_file_nonempty(df):
    assert "source_file" in df.columns
    assert df["source_file"].notna().all(), "source_file に欠損値あり"


# 10. client_code が 20 種類以上
def test_client_code_variety(df):
    n = df["client_code"].nunique()
    assert n >= 20, f"得意先種類不足: {n}"


# 11. variance_amount の整合性（received - invoice、許容誤差1円）
def test_variance_amount_consistency(df):
    inv = pd.to_numeric(df["invoice_amount"], errors="coerce")
    rec = pd.to_numeric(df["received_amount"], errors="coerce")
    var = pd.to_numeric(df["variance_amount"], errors="coerce")
    calc = rec - inv
    inconsistent = (var - calc).abs() > 1
    assert inconsistent.sum() == 0, f"variance_amount 不整合: {inconsistent.sum()} 件"


# 12. source_file が 3 種類以上
def test_source_file_three_kinds(df):
    n = df["source_file"].nunique()
    assert n >= 3, f"source_file 種類不足: {n}"


# 13. 一致率が 70% 以上
def test_match_rate(df):
    rate = (df["match_status"] == "一致").sum() / len(df)
    assert rate >= 0.70, f"一致率が低すぎる: {rate:.1%}"


# 14. 未入金レコードが存在する
def test_unpaid_exists(df):
    assert (df["match_status"] == "未入金").sum() >= 1, "未入金レコードなし"


# 15. 過払レコードが存在する
def test_overpaid_exists(df):
    assert (df["match_status"] == "過払").sum() >= 1, "過払レコードなし"
