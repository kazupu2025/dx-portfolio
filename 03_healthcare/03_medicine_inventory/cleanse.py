# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
クレンジングスクリプト: 3スタイルのCSVを統一正規化して output/cleaned_medicine_202401.csv に出力する
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# 列名マッピング（スタイルA / B / C -> 正規名）
# ============================================================
COLUMN_MAP = [
    # スタイルA: 標準日本語
    {
        "集計日": "date",
        "薬品コード": "med_code",
        "薬品名": "med_name",
        "カテゴリ": "category",
        "病棟": "ward",
        "在庫数量": "stock_qty",
        "最低在庫数": "min_stock",
        "1日平均使用量": "daily_usage",
        "単価": "unit_price",
    },
    # スタイルB: 英語
    {
        "Date": "date",
        "MedCode": "med_code",
        "MedName": "med_name",
        "Category": "category",
        "Ward": "ward",
        "StockQty": "stock_qty",
        "MinStock": "min_stock",
        "DailyUsage": "daily_usage",
        "UnitPrice": "unit_price",
    },
    # スタイルC: バリアント日本語
    {
        "記録日": "date",
        "品目コード": "med_code",
        "品目名": "med_name",
        "薬品区分": "category",
        "使用病棟": "ward",
        "現在庫": "stock_qty",
        "安全在庫": "min_stock",
        "日次使用量": "daily_usage",
        "薬価": "unit_price",
    },
]

REQUIRED_COLS = ["date", "med_code", "med_name", "category", "ward",
                 "stock_qty", "min_stock", "daily_usage", "unit_price"]


def detect_and_rename(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """列名を検出してリネームし、source_file 列を付与する"""
    for mapping in COLUMN_MAP:
        if set(mapping.keys()).issubset(set(df.columns)):
            df = df.rename(columns=mapping)
            df["source_file"] = source_file
            return df
    raise ValueError(f"Unknown column format in {source_file}. Columns: {list(df.columns)}")


def parse_date(series: pd.Series) -> pd.Series:
    """YYYY/MM/DD または YYYY-MM-DD を YYYY-MM-DD に統一"""
    return pd.to_datetime(series, format="mixed", dayfirst=False).dt.strftime("%Y-%m-%d")


def compute_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """計算列を追加する"""
    df = df.copy()

    # days_until_stockout = stock_qty / daily_usage (0除算はNaN)
    df["days_until_stockout"] = np.where(
        df["daily_usage"] > 0,
        (df["stock_qty"] / df["daily_usage"]).round(1),
        np.nan,
    )

    # stock_value = stock_qty * unit_price
    df["stock_value"] = df["stock_qty"] * df["unit_price"]

    # alert_level
    def alert(row):
        if row["stock_qty"] < row["min_stock"]:
            return "欠品"
        if pd.notna(row["days_until_stockout"]) and row["days_until_stockout"] < 3:
            return "警告"
        return "正常"

    df["alert_level"] = df.apply(alert, axis=1)
    return df


def load_all_csvs() -> pd.DataFrame:
    """data/ フォルダ内のすべての CSV を読み込んで結合する"""
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    frames = []
    for path in csv_files:
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
        df = detect_and_rename(df, path.name)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    return combined


def cleanse() -> pd.DataFrame:
    df = load_all_csvs()

    # 日付正規化
    df["date"] = parse_date(df["date"])

    # 数値列変換
    for col in ["stock_qty", "min_stock", "daily_usage", "unit_price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 重複除去
    df = df.drop_duplicates()

    # 計算列
    df = compute_derived_columns(df)

    # 列順
    output_cols = REQUIRED_COLS + ["source_file", "days_until_stockout", "stock_value", "alert_level"]
    df = df[output_cols]

    # 出力
    out_path = OUTPUT_DIR / "cleaned_medicine_202401.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] クレンジング完了: {len(df)} 件 -> {out_path}")
    return df


if __name__ == "__main__":
    cleanse()
