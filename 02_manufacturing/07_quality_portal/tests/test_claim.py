import pandas as pd
import pytest

def make_claim_df():
    return pd.DataFrame({
        "日付": ["2024-01-01"] * 5,
        "仕入先名": ["A社", "A社", "B社", "B社", "C社"],
        "不良カテゴリ": ["寸法不良", "外観不良", "寸法不良", "外観不良", "機能不良"],
        "対応状況": ["未対応", "完了", "対応中", "完了", "未対応"],
    })

def test_total_claim_count():
    df = make_claim_df()
    assert len(df) == 5

def test_unresponded_count():
    df = make_claim_df()
    unresponded = len(df[df["対応状況"] == "未対応"])
    assert unresponded == 2

def test_top_supplier():
    df = make_claim_df()
    top = df["仕入先名"].value_counts().index[0]
    assert top == "A社"

def test_category_counts():
    df = make_claim_df()
    counts = df["不良カテゴリ"].value_counts()
    assert counts["寸法不良"] == 2
    assert counts["外観不良"] == 2
