# tests/test_analyst_output.py — 分析出力のテスト（C-36 顧客満足度）
# encoding: utf-8

import pytest
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
SERVICE_SUMMARY_FILE = OUTPUT_DIR / "service_summary_202401.csv"


# 1. analysis_report.md が存在する
def test_report_file_exists():
    assert REPORT_FILE.exists(), f"Report not found: {REPORT_FILE}"


# 2. service_summary_202401.csv が存在する
def test_service_summary_exists():
    assert SERVICE_SUMMARY_FILE.exists(), f"Service summary not found: {SERVICE_SUMMARY_FILE}"


# 3. レポートが空でない（500文字以上）
def test_report_not_empty():
    if not REPORT_FILE.exists():
        pytest.skip("Report file missing")
    content = REPORT_FILE.read_text(encoding="utf-8")
    assert len(content) >= 500, f"Report too short: {len(content)} chars"


# 4. レポートに NPS スコアが記載されている
def test_report_contains_nps():
    if not REPORT_FILE.exists():
        pytest.skip("Report file missing")
    content = REPORT_FILE.read_text(encoding="utf-8")
    assert "NPS" in content, "NPS not found in report"


# 5. レポートにサービス区分別セクションが存在する
def test_report_contains_service_section():
    if not REPORT_FILE.exists():
        pytest.skip("Report file missing")
    content = REPORT_FILE.read_text(encoding="utf-8")
    assert "サービス区分" in content, "Service section not found in report"


# 6. レポートにインサイト・改善示唆セクションが存在する
def test_report_contains_insights():
    if not REPORT_FILE.exists():
        pytest.skip("Report file missing")
    content = REPORT_FILE.read_text(encoding="utf-8")
    assert "インサイト" in content or "改善" in content, "Insights section not found"


# 7. サービスサマリーに必要な列が存在する
def test_service_summary_columns():
    if not SERVICE_SUMMARY_FILE.exists():
        pytest.skip("Service summary file missing")
    df = pd.read_csv(SERVICE_SUMMARY_FILE, encoding="utf-8-sig")
    required = ["service_type", "response_count", "avg_csat", "nps_score"]
    missing = [c for c in required if c not in df.columns]
    assert not missing, f"Missing columns in service summary: {missing}"


# 8. サービスサマリーが5行（5サービス区分）
def test_service_summary_row_count():
    if not SERVICE_SUMMARY_FILE.exists():
        pytest.skip("Service summary file missing")
    df = pd.read_csv(SERVICE_SUMMARY_FILE, encoding="utf-8-sig")
    assert len(df) == 5, f"Expected 5 service types, got {len(df)}"


# 9. avg_csat が 1.0-5.0 の範囲内
def test_service_summary_avg_csat_range():
    if not SERVICE_SUMMARY_FILE.exists():
        pytest.skip("Service summary file missing")
    df = pd.read_csv(SERVICE_SUMMARY_FILE, encoding="utf-8-sig")
    assert df["avg_csat"].between(1.0, 5.0).all(), "avg_csat out of valid range"


# 10. response_count が正の整数
def test_service_summary_response_count_positive():
    if not SERVICE_SUMMARY_FILE.exists():
        pytest.skip("Service summary file missing")
    df = pd.read_csv(SERVICE_SUMMARY_FILE, encoding="utf-8-sig")
    assert (df["response_count"] > 0).all(), "response_count has non-positive values"
