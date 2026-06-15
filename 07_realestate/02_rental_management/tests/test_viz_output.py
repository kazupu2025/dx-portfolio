import pytest
from pathlib import Path

CHARTS = Path(__file__).parent.parent / "output" / "charts"

def test_charts_dir(): assert CHARTS.exists()
def test_bar_area_vacancy(): assert (CHARTS / "bar_area_vacancy_rate.png").exists()
def test_bar_type_income(): assert (CHARTS / "bar_type_net_income.png").exists()
def test_bar_area_revenue(): assert (CHARTS / "bar_area_revenue.png").exists()
