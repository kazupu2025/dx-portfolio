# tests/test_cleaner_output.py — クレンジング出力のテスト（C-36 顧客満足度）
# encoding: utf-8

import pytest
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
CLEANED_FILE = OUTPUT_DIR / "cleaned_satisfaction_202401.csv"

REQUIRED_COLS = [
    "response_date", "customer_code", "service_type", "agent",
    "overall_sat", "response_speed", "quality", "cost_perf", "nps",
    "csat_score", "nps_category", "satisfaction_flag", "source_file",
]


@pytest.fixture(scope="module")
def df():
    if not CLEANED_FILE.exists():
        pytest.skip(f"Cleaned file not found: {CLEANED_FILE}")
    return pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")


# 1. ファイルが存在する
def test_file_exists():
    assert CLEANED_FILE.exists(), f"Cleaned CSV not found: {CLEANED_FILE}"


# 2. 行数が400以上
def test_row_count(df):
    assert len(df) >= 400, f"Expected >= 400 rows, got {len(df)}"


# 3. 必須列が全て存在する
def test_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


# 4. 日付フォーマットが YYYY-MM-DD
def test_date_format(df):
    bad = df["response_date"].dropna()[
        ~df["response_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$")
    ]
    assert bad.empty, f"Invalid date formats found:\n{bad.head()}"


# 5. service_type が期待する5種類のみ
def test_service_type_values(df):
    expected = {"ITサポート", "コンサルティング", "保守", "導入支援", "研修"}
    actual = set(df["service_type"].dropna().unique())
    assert actual == expected, f"service_type mismatch: got {actual}"


# 6. agent が期待する5人のみ
def test_agent_values(df):
    expected = {"田中", "佐藤", "鈴木", "高橋", "伊藤"}
    actual = set(df["agent"].dropna().unique())
    assert actual == expected, f"agent mismatch: got {actual}"


# 7. overall_sat の範囲 1-5
def test_overall_sat_range(df):
    col = df["overall_sat"].dropna()
    assert col.between(1, 5).all(), f"overall_sat out of range: min={col.min()}, max={col.max()}"


# 8. response_speed の範囲 1-5
def test_response_speed_range(df):
    col = df["response_speed"].dropna()
    assert col.between(1, 5).all(), f"response_speed out of range"


# 9. quality の範囲 1-5
def test_quality_range(df):
    col = df["quality"].dropna()
    assert col.between(1, 5).all(), f"quality out of range"


# 10. cost_perf の範囲 1-5
def test_cost_perf_range(df):
    col = df["cost_perf"].dropna()
    assert col.between(1, 5).all(), f"cost_perf out of range"


# 11. nps の範囲 0-10
def test_nps_range(df):
    col = df["nps"].dropna()
    assert col.between(0, 10).all(), f"nps out of range: min={col.min()}, max={col.max()}"


# 12. csat_score の範囲 1.0-5.0
def test_csat_score_range(df):
    col = df["csat_score"].dropna()
    assert col.between(1.0, 5.0).all(), f"csat_score out of range"


# 13. csat_score の計算が正しい
def test_csat_score_calculation(df):
    expected = (
        df["overall_sat"] + df["response_speed"] + df["quality"] + df["cost_perf"]
    ) / 4
    diff = (df["csat_score"] - expected).abs().max()
    assert diff < 0.01, f"csat_score calculation mismatch: max diff={diff}"


# 14. nps_category の値域
def test_nps_category_values(df):
    valid = {"推奨者", "中立者", "批判者"}
    actual = set(df["nps_category"].dropna().unique())
    assert actual.issubset(valid), f"Unexpected nps_category values: {actual - valid}"


# 15. satisfaction_flag の値域
def test_satisfaction_flag_values(df):
    valid = {"満足", "普通", "不満"}
    actual = set(df["satisfaction_flag"].dropna().unique())
    assert actual.issubset(valid), f"Unexpected satisfaction_flag values: {actual - valid}"


# 16. source_file が3種類存在する
def test_source_file_count(df):
    count = df["source_file"].nunique()
    assert count >= 3, f"Expected >= 3 source files, got {count}"


# 17. 欠損率が15%以下
def test_missing_ratio(df):
    max_ratio = df.isnull().mean().max()
    assert max_ratio <= 0.15, f"Missing ratio too high: {max_ratio:.2%}"


# 18. 推奨者が1件以上存在する
def test_promoters_exist(df):
    count = (df["nps_category"] == "推奨者").sum()
    assert count >= 1, f"No promoters found"


# 19. nps_category と nps の整合性（推奨者は nps >= 9）
def test_nps_category_promoter_consistency(df):
    promoters = df[df["nps_category"] == "推奨者"]
    assert (promoters["nps"] >= 9).all(), "Some promoters have nps < 9"


# 20. satisfaction_flag と csat_score の整合性
def test_satisfaction_flag_consistency(df):
    satisfied = df[df["satisfaction_flag"] == "満足"]
    assert (satisfied["csat_score"] >= 4.0).all(), "Some satisfied rows have csat_score < 4.0"
