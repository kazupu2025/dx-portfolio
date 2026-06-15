import pandas as pd
import pytest
from pathlib import Path

REPORT   = Path("output/analysis_report.md")
FORECAST = Path("output/forecast_202401.csv")


@pytest.fixture(scope="module")
def report():
    return REPORT.read_text(encoding="utf-8")


def test_report_exists(): assert REPORT.exists()

def test_forecast_csv_exists(): assert FORECAST.exists()

def test_report_has_stockout(report): assert "欠品" in report

def test_report_has_order(report): assert "発注" in report

def test_report_has_insight(report):
    assert "インサイト" in report or "ビジネス" in report

def test_forecast_product_count():
    df = pd.read_csv(FORECAST, encoding="utf-8-sig")
    assert df.shape[0] == 50
