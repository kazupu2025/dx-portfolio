# -*- coding: utf-8 -*-
"""
C-54: 店舗別損益・原価率管理パイプライン
データクレンジングスクリプト
3スタイルのCSVを読み込み、統一正規化して output/cleaned_pl_202401.csv に出力
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ---- パス定義 ----
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "cleaned_pl_202401.csv"

# ---- 列名マッピング ----
COLUMN_MAP = {
    # スタイルA（標準日本語）
    "記録日": "record_date",
    "記録ID": "record_id",
    "店舗名": "store_name",
    "売上": "revenue",
    "食材費": "food_cost",
    "人件費": "labor_cost",
    "その他経費": "other_cost",
    # スタイルB（英語）
    "RecordDate": "record_date",
    "RecordID": "record_id",
    "StoreName": "store_name",
    "Revenue": "revenue",
    "FoodCost": "food_cost",
    "LaborCost": "labor_cost",
    "OtherCost": "other_cost",
    # スタイルC（バリアント日本語）
    "日付": "record_date",
    "管理番号": "record_id",
    "店舗": "store_name",
    "売上高": "revenue",
    "原材料費": "food_cost",
    "労務費": "labor_cost",
    "諸経費": "other_cost",
}

CANONICAL_COLS = [
    "record_date",
    "record_id",
    "store_name",
    "revenue",
    "food_cost",
    "labor_cost",
    "other_cost",
    "total_cost",
    "gross_profit",
    "food_cost_rate",
    "labor_cost_rate",
    "profit_margin",
    "pl_flag",
    "source_file",
]


def load_and_rename(filepath: Path) -> pd.DataFrame:
    """CSVを読み込み、列名を正規名にリネームして source_file 列を付与"""
    df = pd.read_csv(filepath, encoding="utf-8-sig", dtype=str)
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = filepath.name
    return df


def normalize_date(series: pd.Series) -> pd.Series:
    """日付を YYYY-MM-DD に統一（スラッシュをダッシュに先に変換）"""
    normalized = series.str.replace("/", "-", regex=False)
    return pd.to_datetime(normalized, format="%Y-%m-%d", errors="coerce").dt.strftime("%Y-%m-%d")


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """派生列を追加"""
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["food_cost"] = pd.to_numeric(df["food_cost"], errors="coerce")
    df["labor_cost"] = pd.to_numeric(df["labor_cost"], errors="coerce")
    df["other_cost"] = pd.to_numeric(df["other_cost"], errors="coerce")

    df["total_cost"] = df["food_cost"] + df["labor_cost"] + df["other_cost"]
    df["gross_profit"] = df["revenue"] - df["total_cost"]

    # 比率計算（revenue > 0 の場合のみ）
    revenue_pos = df["revenue"] > 0
    df["food_cost_rate"] = np.where(revenue_pos, df["food_cost"] / df["revenue"], np.nan)
    df["labor_cost_rate"] = np.where(revenue_pos, df["labor_cost"] / df["revenue"], np.nan)
    df["profit_margin"] = np.where(revenue_pos, df["gross_profit"] / df["revenue"], np.nan)

    df["pl_flag"] = df["gross_profit"].apply(lambda x: "黒字" if x > 0 else "赤字")

    return df


def cleanse() -> pd.DataFrame:
    """全CSVを読み込み、クレンジングして返す"""
    csv_files = sorted(DATA_DIR.glob("pl_style*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"CSVが見つかりません: {DATA_DIR}")

    frames = []
    for filepath in csv_files:
        df = load_and_rename(filepath)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    # 日付正規化
    combined["record_date"] = normalize_date(combined["record_date"])

    # 派生列追加
    combined = add_derived_columns(combined)

    # CANONICAL_COLSのみ出力
    combined = combined[CANONICAL_COLS]

    # 必須列の欠損行を除去
    required = ["record_date", "record_id", "store_name", "revenue"]
    combined = combined.dropna(subset=required)

    return combined


def main():
    print("[INFO] Cleansing start ...")
    df = cleanse()
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"[OK] Cleansing complete: {len(df)} rows -> {OUTPUT_FILE}")
    black = (df["pl_flag"] == "黒字").sum()
    red = (df["pl_flag"] == "赤字").sum()
    print(f"[INFO] 黒字: {black} / 赤字: {red}")


if __name__ == "__main__":
    main()
