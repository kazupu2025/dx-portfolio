import pytest
from pathlib import Path

BASE = Path(__file__).parent.parent
CHARTS = BASE / "output" / "charts"


def test_charts_dir_exists():
    assert CHARTS.exists(), "output/charts ディレクトリが存在しない"


def test_bar_course_completion_exists():
    assert (CHARTS / "bar_course_completion.png").exists(), \
        "bar_course_completion.png が存在しない"


def test_bar_score_grade_exists():
    assert (CHARTS / "bar_score_grade.png").exists(), \
        "bar_score_grade.png が存在しない"


def test_bar_learnertype_completion_exists():
    assert (CHARTS / "bar_learnertype_completion.png").exists(), \
        "bar_learnertype_completion.png が存在しない"
