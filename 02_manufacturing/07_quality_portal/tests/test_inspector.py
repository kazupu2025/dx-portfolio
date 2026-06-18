import pandas as pd
import pytest

def make_inspector_df():
    return pd.DataFrame({
        "日付": ["2024-01-01"] * 6,
        "検査員名": ["田中", "田中", "佐藤", "佐藤", "鈴木", "鈴木"],
        "シフト": ["昼", "夜", "昼", "夜", "昼", "夜"],
        "検査数": [100, 80, 120, 90, 110, 95],
        "合格数": [98, 77, 115, 86, 108, 91],
    })

def test_pass_rate_calculation():
    df = make_inspector_df()
    df["pass_rate"] = df["合格数"] / df["検査数"]
    assert df["pass_rate"].iloc[0] == pytest.approx(0.98)

def test_best_inspector():
    df = make_inspector_df()
    df["pass_rate"] = df["合格数"] / df["検査数"]
    best = df.groupby("検査員名")["pass_rate"].mean().idxmax()
    assert best == "田中"

def test_total_inspected():
    df = make_inspector_df()
    total = df["検査数"].sum()
    assert total == 595

def test_required_columns_present():
    df = make_inspector_df()
    required = {"日付", "検査員名", "シフト", "検査数", "合格数"}
    assert required.issubset(set(df.columns))
