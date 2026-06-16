# -*- coding: utf-8 -*-
"""
cleanse.py
3スタイルのCSVを読み込み、統一正規化して output/cleaned_purchases_202401.csv に出力する。
RFMスコアの計算はこのステップでは行わない。
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "cleaned_purchases_202401.csv"

# 各スタイルの列名を正規名にマッピング
COLUMN_MAP = {
    # スタイルA (日本語標準)
    "注文日": "order_date",
    "顧客コード": "customer_code",
    "商品カテゴリ": "category",
    "購入金額": "amount",
    "店舗名": "store_name",
    # スタイルB (英語)
    "OrderDate": "order_date",
    "CustomerCode": "customer_code",
    "Category": "category",
    "Amount": "amount",
    "StoreName": "store_name",
    # スタイルC (バリアント日本語)
    "購買日": "order_date",
    "会員番号": "customer_code",
    "品目区分": "category",
    "売上金額": "amount",
    "店名": "store_name",
}

REQUIRED_COLS = ["order_date", "customer_code", "category", "amount", "store_name"]


def normalize_date(date_str: str) -> str:
    """YYYY/MM/DD または YYYY-MM-DD を YYYY-MM-DD に統一"""
    if pd.isna(date_str):
        return None
    s = str(date_str).strip()
    if "/" in s:
        parts = s.split("/")
        return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
    return s


def load_and_rename(filepath: Path) -> pd.DataFrame:
    """CSVを読み込み、列名を正規名に変換する"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    rename_map = {col: COLUMN_MAP[col] for col in df.columns if col in COLUMN_MAP}
    df = df.rename(columns=rename_map)
    df["source_file"] = filepath.name
    return df


def cleanse():
    csv_files = sorted(DATA_DIR.glob("purchases_style*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"[FAIL] data/ に purchases_style*.csv が見つかりません: {DATA_DIR}")

    dfs = []
    for fp in csv_files:
        df = load_and_rename(fp)
        print(f"[OK] 読み込み: {fp.name} ({len(df)}行)")
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)

    # 必須列のみ保持
    missing = [c for c in REQUIRED_COLS if c not in combined.columns]
    if missing:
        raise ValueError(f"[FAIL] 正規化後に不足している列: {missing}")

    combined = combined[REQUIRED_COLS + ["source_file"]]

    # 日付正規化
    combined["order_date"] = combined["order_date"].apply(normalize_date)

    # amount を数値に変換、変換できない行は除去
    combined["amount"] = pd.to_numeric(combined["amount"], errors="coerce")
    before = len(combined)
    combined = combined.dropna(subset=["order_date", "customer_code", "amount"])
    combined["amount"] = combined["amount"].astype(int)
    after = len(combined)

    if before != after:
        print(f"[OK] 欠損・変換不可行を除去: {before - after}行")

    # 出力
    combined.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"[OK] クレンジング完了: {after}行 -> {OUTPUT_FILE}")

    return combined


if __name__ == "__main__":
    cleanse()
