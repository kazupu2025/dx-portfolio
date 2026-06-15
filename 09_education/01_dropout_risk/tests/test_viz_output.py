"""tests/test_viz_output.py — 4テスト"""
import pytest
from pathlib import Path

BASE   = Path(__file__).resolve().parent.parent
CHARTS = BASE / "output" / "charts"

def test_charts_dir_exists():
    assert CHARTS.exists()

def test_bar_risk_distribution():
    assert (CHARTS / "bar_risk_distribution.png").exists()

def test_bar_subject_avg_score():
    assert (CHARTS / "bar_subject_avg_score.png").exists()

def test_scatter_attendance_score():
    assert (CHARTS / "scatter_attendance_score.png").exists()
