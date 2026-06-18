import pandas as pd
import pytest

def make_lot_df():
    return pd.DataFrame({
        "ロットID": ["L001", "L001", "L002", "L002", "L003"],
        "製品名": ["製品A", "製品A", "製品B", "製品B", "製品A"],
        "検査日": ["2024-01-05", "2024-01-05", "2024-01-10", "2024-01-10", "2024-01-15"],
        "検査項目": ["寸法", "外観", "寸法", "外観", "寸法"],
        "判定": ["合格", "合格", "不合格", "合格", "合格"],
    })

def test_pass_rate():
    df = make_lot_df()
    pass_rate = len(df[df["判定"] == "合格"]) / len(df)
    assert pass_rate == pytest.approx(0.8)

def test_failed_lot_count():
    df = make_lot_df()
    # ロット単位で1件でも不合格があれば不合格ロット
    failed_lots = df[df["判定"] == "不合格"]["ロットID"].nunique()
    assert failed_lots == 1

def test_review_required_count():
    df = make_lot_df()
    # 要確認 = 不合格を含むロットの全検査数
    failed_lot_ids = df[df["判定"] == "不合格"]["ロットID"].unique()
    review_count = len(df[df["ロットID"].isin(failed_lot_ids)])
    assert review_count == 2

def test_required_columns_present():
    df = make_lot_df()
    required = {"ロットID", "製品名", "検査日", "検査項目", "判定"}
    assert required.issubset(set(df.columns))
