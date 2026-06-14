import pytest
from pathlib import Path

CHARTS = Path("output/charts")

def test_charts_dir_exists(): assert CHARTS.exists()
def test_bar_dept_expense_exists(): assert (CHARTS / "bar_dept_expense.png").exists()
def test_bar_expense_type_exists(): assert (CHARTS / "bar_expense_type.png").exists()
def test_bar_budget_vs_actual_exists(): assert (CHARTS / "bar_budget_vs_actual.png").exists()
