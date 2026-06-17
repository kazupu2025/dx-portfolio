# -*- coding: utf-8 -*-
"""
C-54: 店舗別損益・原価率管理パイプライン
サンプルデータ生成スクリプト
3スタイルのCSVを data/ フォルダに生成（各160行、合計480行）
"""

import random
import csv
import os
from pathlib import Path

random.seed(42)

# ---- 定数定義 ----
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

STORES = ["渋谷店", "新宿店", "池袋店", "銀座店", "品川店"]

ROWS_PER_FILE = 160

# 5店舗 × 96日分 = 480件 → 各スタイル160件
# 2024-01-01 から96日分の日付を生成
import datetime

START_DATE = datetime.date(2024, 1, 1)
DATES_DASH = []
DATES_SLASH = []
for i in range(96):
    d = START_DATE + datetime.timedelta(days=i)
    DATES_DASH.append(d.strftime("%Y-%m-%d"))
    DATES_SLASH.append(d.strftime("%Y/%m/%d"))


def make_record_id(idx):
    return f"REC-{str(idx).zfill(4)}"


def gen_revenue():
    return random.randint(50000, 500000)


def gen_costs(revenue):
    food_cost_rate = random.uniform(0.25, 0.40)
    labor_cost_rate = random.uniform(0.25, 0.35)
    food_cost = int(revenue * food_cost_rate)
    labor_cost = int(revenue * labor_cost_rate)
    other_cost = random.randint(10000, 50000)
    return food_cost, labor_cost, other_cost


def generate_base_records(count, start_id=1):
    """共通ランダムレコードを生成（record_id付き）"""
    records = []
    # 5店舗 × 日付を順番に割り当て
    date_store_pairs = []
    for date_dash in DATES_DASH:
        for store in STORES:
            date_store_pairs.append((date_dash, store))
    # 必要な件数だけ使う（160件）
    random.shuffle(date_store_pairs)
    used_pairs = date_store_pairs[:count]

    for i, (date_dash, store) in enumerate(used_pairs):
        revenue = gen_revenue()
        food_cost, labor_cost, other_cost = gen_costs(revenue)
        records.append({
            "date_dash": date_dash,
            "date_slash": date_dash.replace("-", "/"),
            "record_id": make_record_id(start_id + i),
            "store": store,
            "revenue": revenue,
            "food_cost": food_cost,
            "labor_cost": labor_cost,
            "other_cost": other_cost,
        })
    return records


# ---- スタイルA: 標準日本語列名（日付: YYYY/MM/DD）----
def generate_style_a(records):
    rows = []
    for r in records:
        rows.append({
            "記録日": r["date_slash"],
            "記録ID": r["record_id"],
            "店舗名": r["store"],
            "売上": r["revenue"],
            "食材費": r["food_cost"],
            "人件費": r["labor_cost"],
            "その他経費": r["other_cost"],
        })
    return rows


# ---- スタイルB: 英語列名（日付: YYYY-MM-DD）----
def generate_style_b(records):
    rows = []
    for r in records:
        rows.append({
            "RecordDate": r["date_dash"],
            "RecordID": r["record_id"],
            "StoreName": r["store"],
            "Revenue": r["revenue"],
            "FoodCost": r["food_cost"],
            "LaborCost": r["labor_cost"],
            "OtherCost": r["other_cost"],
        })
    return rows


# ---- スタイルC: バリアント日本語（日付: YYYY/MM/DD）----
def generate_style_c(records):
    rows = []
    for r in records:
        rows.append({
            "日付": r["date_slash"],
            "管理番号": r["record_id"],
            "店舗": r["store"],
            "売上高": r["revenue"],
            "原材料費": r["food_cost"],
            "労務費": r["labor_cost"],
            "諸経費": r["other_cost"],
        })
    return rows


def write_csv(rows, filepath, encoding="utf-8-sig"):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    # 各スタイル独立したレコードを生成（record_idが重複しないよう開始IDをずらす）
    records_a = generate_base_records(ROWS_PER_FILE, start_id=1)
    records_b = generate_base_records(ROWS_PER_FILE, start_id=161)
    records_c = generate_base_records(ROWS_PER_FILE, start_id=321)

    style_a = generate_style_a(records_a)
    style_b = generate_style_b(records_b)
    style_c = generate_style_c(records_c)

    write_csv(style_a, DATA_DIR / "pl_styleA_202401.csv")
    write_csv(style_b, DATA_DIR / "pl_styleB_202401.csv")
    write_csv(style_c, DATA_DIR / "pl_styleC_202401.csv")

    print(f"[OK] StyleA: {len(style_a)} lines -> data/pl_styleA_202401.csv")
    print(f"[OK] StyleB: {len(style_b)} lines -> data/pl_styleB_202401.csv")
    print(f"[OK] StyleC: {len(style_c)} lines -> data/pl_styleC_202401.csv")
    print(f"[OK] Total: {len(style_a) + len(style_b) + len(style_c)} lines")


if __name__ == "__main__":
    main()
