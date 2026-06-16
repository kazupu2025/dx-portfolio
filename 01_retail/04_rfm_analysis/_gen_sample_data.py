# -*- coding: utf-8 -*-
"""
_gen_sample_data.py
顧客購買履歴サンプルデータ生成スクリプト
3スタイルのCSVを data/ フォルダに生成する（合計400行以上）
"""

import random
import csv
import os
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CUSTOMERS = [f"CUST-{i:03d}" for i in range(1, 101)]
CATEGORIES = ["食料品", "日用品", "衣料品", "家電", "雑貨"]
STORES = ["渋谷店", "新宿店", "池袋店"]

DATES_YMD_SLASH = []
DATES_YMD_HYPHEN = []
for month in range(1, 3):
    days_in_month = 31 if month == 1 else 28
    for day in range(1, days_in_month + 1):
        DATES_YMD_SLASH.append(f"2024/{month:02d}/{day:02d}")
        DATES_YMD_HYPHEN.append(f"2024-{month:02d}-{day:02d}")


def random_amount():
    return random.randint(500, 50000)


def gen_style_a(n_rows=150):
    """スタイルA: 標準日本語列名, 日付YYYY/MM/DD"""
    rows = []
    for _ in range(n_rows):
        rows.append({
            "注文日": random.choice(DATES_YMD_SLASH),
            "顧客コード": random.choice(CUSTOMERS),
            "商品カテゴリ": random.choice(CATEGORIES),
            "購入金額": random_amount(),
            "店舗名": random.choice(STORES),
        })
    return rows


def gen_style_b(n_rows=150):
    """スタイルB: 英語列名, 日付YYYY-MM-DD"""
    rows = []
    for _ in range(n_rows):
        rows.append({
            "OrderDate": random.choice(DATES_YMD_HYPHEN),
            "CustomerCode": random.choice(CUSTOMERS),
            "Category": random.choice(CATEGORIES),
            "Amount": random_amount(),
            "StoreName": random.choice(STORES),
        })
    return rows


def gen_style_c(n_rows=150):
    """スタイルC: バリアント日本語列名, 日付YYYY/MM/DD"""
    rows = []
    for _ in range(n_rows):
        rows.append({
            "購買日": random.choice(DATES_YMD_SLASH),
            "会員番号": random.choice(CUSTOMERS),
            "品目区分": random.choice(CATEGORIES),
            "売上金額": random_amount(),
            "店名": random.choice(STORES),
        })
    return rows


def write_csv(filepath, fieldnames, rows):
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows_a = gen_style_a(150)
    rows_b = gen_style_b(150)
    rows_c = gen_style_c(150)

    write_csv(
        DATA_DIR / "purchases_styleA.csv",
        ["注文日", "顧客コード", "商品カテゴリ", "購入金額", "店舗名"],
        rows_a,
    )
    write_csv(
        DATA_DIR / "purchases_styleB.csv",
        ["OrderDate", "CustomerCode", "Category", "Amount", "StoreName"],
        rows_b,
    )
    write_csv(
        DATA_DIR / "purchases_styleC.csv",
        ["購買日", "会員番号", "品目区分", "売上金額", "店名"],
        rows_c,
    )

    total = len(rows_a) + len(rows_b) + len(rows_c)
    print(f"[OK] サンプルデータ生成完了: styleA={len(rows_a)}行, styleB={len(rows_b)}行, styleC={len(rows_c)}行, 合計={total}行")
    print(f"[OK] 出力先: {DATA_DIR}")


if __name__ == "__main__":
    main()
