import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
CHARTS = BASE / "output" / "charts"


def test_charts_dir_exists():
    assert CHARTS.exists(), "output/charts ディレクトリが存在しない"


def test_bar_instructor_lessons_top10_exists():
    assert (CHARTS / "bar_instructor_lessons_top10.png").exists(), \
        "bar_instructor_lessons_top10.png が存在しない"


def test_bar_specialty_cost_exists():
    assert (CHARTS / "bar_specialty_cost.png").exists(), \
        "bar_specialty_cost.png が存在しない"


def test_pie_employment_cost_share_exists():
    assert (CHARTS / "pie_employment_cost_share.png").exists(), \
        "pie_employment_cost_share.png が存在しない"
