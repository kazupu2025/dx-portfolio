import pandas as pd
import pytest

def make_yield_df():
    return pd.DataFrame({
        "日付": ["2024-01-01"] * 6,
        "工程名": ["溶接", "溶接", "塗装", "塗装", "組立", "組立"],
        "投入数": [100, 100, 80, 80, 60, 60],
        "合格数": [95, 92, 76, 74, 57, 56],
    })

def test_yield_rate_calculation():
    df = make_yield_df()
    df["yield_rate"] = df["合格数"] / df["投入数"]
    assert df["yield_rate"].iloc[0] == pytest.approx(0.95)
    assert df["yield_rate"].iloc[2] == pytest.approx(0.95)

def test_average_yield_rate():
    df = make_yield_df()
    avg = df["合格数"].sum() / df["投入数"].sum()
    expected = (95+92+76+74+57+56) / (100+100+80+80+60+60)
    assert avg == pytest.approx(expected)

def test_worst_process():
    df = make_yield_df()
    df["yield_rate"] = df["合格数"] / df["投入数"]
    worst = df.groupby("工程名")["yield_rate"].mean().idxmin()
    assert worst == "溶接"

def test_required_columns_present():
    df = make_yield_df()
    required = {"日付", "工程名", "投入数", "合格数"}
    assert required.issubset(set(df.columns))
