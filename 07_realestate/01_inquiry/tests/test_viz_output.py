import pytest
from pathlib import Path

CHARTS = Path(__file__).parent.parent / "output" / "charts"

def test_charts_dir_exists(): assert CHARTS.exists()
def test_bar_funnel_exists(): assert (CHARTS / "bar_funnel.png").exists()
def test_bar_agent_exists(): assert (CHARTS / "bar_agent_conversion.png").exists()
def test_bar_area_exists(): assert (CHARTS / "bar_area_inquiry.png").exists()
