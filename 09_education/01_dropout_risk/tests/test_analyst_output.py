"""tests/test_analyst_output.py — 6テスト"""
import pytest
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "output"

def test_report_exists():
    assert (OUT / "analysis_report.md").exists()

def test_alert_csv_exists():
    assert (OUT / "alert_students_202401.csv").exists()

def test_report_contains_dropout():
    text = (OUT / "analysis_report.md").read_text(encoding="utf-8")
    assert "退学" in text

def test_report_contains_risk():
    text = (OUT / "analysis_report.md").read_text(encoding="utf-8")
    assert "リスク" in text

def test_report_contains_insight():
    text = (OUT / "analysis_report.md").read_text(encoding="utf-8")
    assert "インサイト" in text

def test_alert_csv_student_id_column():
    p = OUT / "alert_students_202401.csv"
    assert p.exists()
    df = pd.read_csv(p, encoding="utf-8-sig")
    assert "student_id" in df.columns, f"columns: {list(df.columns)}"
