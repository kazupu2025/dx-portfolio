import pandas as pd
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

def make_defect_df():
    return pd.DataFrame({
        "日付": ["2024-01-01"] * 4,
        "ライン": ["L1", "L1", "L2", "L2"],
        "製品名": ["製品A", "製品B", "製品A", "製品B"],
        "検査数": [100, 100, 100, 100],
        "不良数": [2, 3, 1, 5],
    })

def test_defect_rate_calculation():
    df = make_defect_df()
    df["不良率"] = df["不良数"] / df["検査数"]
    assert df["不良率"].iloc[0] == pytest.approx(0.02)
    assert df["不良率"].iloc[3] == pytest.approx(0.05)

def test_total_defect_rate():
    df = make_defect_df()
    total_rate = df["不良数"].sum() / df["検査数"].sum()
    assert total_rate == pytest.approx(0.0275)

def test_worst_line():
    df = make_defect_df()
    df["不良率"] = df["不良数"] / df["検査数"]
    worst = df.groupby("ライン")["不良率"].mean().idxmax()
    assert worst == "L2"

def test_required_columns_present():
    df = make_defect_df()
    required = {"日付", "ライン", "製品名", "検査数", "不良数"}
    assert required.issubset(set(df.columns))
