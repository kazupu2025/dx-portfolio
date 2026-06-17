"""
C-39: 分析出力テスト（7テスト以上）
"""

import json
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
PROPERTY_CSV = OUTPUT_DIR / "property_summary_202401.csv"
JSON_PATH = OUTPUT_DIR / "result_analysis.json"


# 1. analysis_report.md が存在する
def test_report_exists():
    assert REPORT_MD.exists(), f"analysis_report.md not found: {REPORT_MD}"


# 2. property_summary_202401.csv が存在する
def test_property_summary_exists():
    assert PROPERTY_CSV.exists(), f"property_summary_202401.csv not found: {PROPERTY_CSV}"


# 3. result_analysis.json が存在する
def test_json_exists():
    assert JSON_PATH.exists(), f"result_analysis.json not found: {JSON_PATH}"


# 4. レポートに必須セクションが含まれる
def test_report_sections():
    if not REPORT_MD.exists():
        pytest.skip("analysis_report.md not found")
    content = REPORT_MD.read_text(encoding="utf-8")
    required_sections = ["物件別クレーム状況", "クレーム区分別発生件数", "緊急対応", "月別トレンド", "改善示唆"]
    missing = [s for s in required_sections if s not in content]
    assert not missing, f"Missing sections in report: {missing}"


# 5. property_summary の列が正しい
def test_property_summary_columns():
    if not PROPERTY_CSV.exists():
        pytest.skip("property_summary_202401.csv not found")
    df = pd.read_csv(PROPERTY_CSV, encoding="utf-8-sig")
    expected_cols = [
        "property_name", "claim_count", "resolved_count",
        "avg_response_days", "total_work_hours", "total_cost_estimate", "resolution_rate_pct"
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


# 6. property_summary に 5 物件が揃っている
def test_property_summary_row_count():
    if not PROPERTY_CSV.exists():
        pytest.skip("property_summary_202401.csv not found")
    df = pd.read_csv(PROPERTY_CSV, encoding="utf-8-sig")
    assert len(df) == 5, f"Expected 5 properties, got {len(df)}"


# 7. resolution_rate_pct が 0〜100 の範囲内
def test_resolution_rate_range():
    if not PROPERTY_CSV.exists():
        pytest.skip("property_summary_202401.csv not found")
    df = pd.read_csv(PROPERTY_CSV, encoding="utf-8-sig")
    bad = ((df["resolution_rate_pct"] < 0) | (df["resolution_rate_pct"] > 100)).sum()
    assert bad == 0, f"{bad} rows have resolution_rate_pct out of range"


# 8. result_analysis.json の内容確認
def test_json_content():
    if not JSON_PATH.exists():
        pytest.skip("result_analysis.json not found")
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    required_keys = ["total_claims", "resolved_count", "unresolved_count",
                     "in_progress_count", "avg_response_days", "total_cost_estimate"]
    missing = [k for k in required_keys if k not in data]
    assert not missing, f"Missing keys in JSON: {missing}"
    assert data["total_claims"] >= 420, f"total_claims too small: {data['total_claims']}"
