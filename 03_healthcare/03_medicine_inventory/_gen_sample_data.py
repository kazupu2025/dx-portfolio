# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
サンプルデータ生成スクリプト
3スタイルのCSVを data/ フォルダに生成する
"""

import random
import os
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

# ============================================================
# 定数定義
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CATEGORIES = ["内服薬", "外用薬", "注射薬", "検査薬", "医療材料"]
WARDS = ["内科病棟", "外科病棟", "ICU", "外来"]

# 薬品マスタ（50品目）
MEDICINES = []
for i in range(1, 51):
    code = f"MED-{i:03d}"
    cat = CATEGORIES[(i - 1) % len(CATEGORIES)]
    name_map = {
        "内服薬": f"錠剤{i:02d}号",
        "外用薬": f"軟膏{i:02d}号",
        "注射薬": f"注射液{i:02d}号",
        "検査薬": f"試薬{i:02d}号",
        "医療材料": f"材料{i:02d}号",
    }
    MEDICINES.append({"code": code, "name": name_map[cat], "category": cat})

# 基準日
START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 1, 31)


def random_dates(n):
    delta = (END_DATE - START_DATE).days
    return [START_DATE + timedelta(days=random.randint(0, delta)) for _ in range(n)]


def make_record(med, ward, rec_date):
    min_stock = random.randint(10, 50)
    daily_usage = round(random.uniform(1.0, 20.0), 1)
    unit_price = random.randint(100, 50000)

    # 15% の確率で欠品（在庫数 = 0 〜 min_stock-1）
    if random.random() < 0.15:
        stock_qty = random.randint(0, max(0, min_stock - 1))
    else:
        stock_qty = random.randint(min_stock, min_stock * 5)

    return {
        "rec_date": rec_date,
        "code": med["code"],
        "name": med["name"],
        "category": med["category"],
        "ward": ward,
        "stock_qty": stock_qty,
        "min_stock": min_stock,
        "daily_usage": daily_usage,
        "unit_price": unit_price,
    }


# 全レコードを生成（合計 = 400件以上）
# スタイルAに160件、B+Cに各120件（計400件）
all_records = []
dates_a = random_dates(160)
dates_b = random_dates(120)
dates_c = random_dates(120)

records_a, records_b, records_c = [], [], []
for i, rec_date in enumerate(dates_a):
    med = MEDICINES[i % len(MEDICINES)]
    ward = WARDS[i % len(WARDS)]
    records_a.append(make_record(med, ward, rec_date))

for i, rec_date in enumerate(dates_b):
    med = MEDICINES[i % len(MEDICINES)]
    ward = WARDS[(i + 1) % len(WARDS)]
    records_b.append(make_record(med, ward, rec_date))

for i, rec_date in enumerate(dates_c):
    med = MEDICINES[i % len(MEDICINES)]
    ward = WARDS[(i + 2) % len(WARDS)]
    records_c.append(make_record(med, ward, rec_date))


# ============================================================
# スタイルA: 標準日本語列名, 日付 YYYY/MM/DD
# ============================================================
import csv

path_a = DATA_DIR / "medicine_stock_A_202401.csv"
with open(path_a, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["集計日", "薬品コード", "薬品名", "カテゴリ", "病棟",
                     "在庫数量", "最低在庫数", "1日平均使用量", "単価"])
    for r in records_a:
        writer.writerow([
            r["rec_date"].strftime("%Y/%m/%d"),
            r["code"], r["name"], r["category"], r["ward"],
            r["stock_qty"], r["min_stock"], r["daily_usage"], r["unit_price"],
        ])

# ============================================================
# スタイルB: 英語列名, 日付 YYYY-MM-DD
# ============================================================
path_b = DATA_DIR / "medicine_stock_B_202401.csv"
with open(path_b, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "MedCode", "MedName", "Category", "Ward",
                     "StockQty", "MinStock", "DailyUsage", "UnitPrice"])
    for r in records_b:
        writer.writerow([
            r["rec_date"].strftime("%Y-%m-%d"),
            r["code"], r["name"], r["category"], r["ward"],
            r["stock_qty"], r["min_stock"], r["daily_usage"], r["unit_price"],
        ])

# ============================================================
# スタイルC: バリアント日本語列名, 日付 YYYY/MM/DD
# ============================================================
path_c = DATA_DIR / "medicine_stock_C_202401.csv"
with open(path_c, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["記録日", "品目コード", "品目名", "薬品区分", "使用病棟",
                     "現在庫", "安全在庫", "日次使用量", "薬価"])
    for r in records_c:
        writer.writerow([
            r["rec_date"].strftime("%Y/%m/%d"),
            r["code"], r["name"], r["category"], r["ward"],
            r["stock_qty"], r["min_stock"], r["daily_usage"], r["unit_price"],
        ])

total = len(records_a) + len(records_b) + len(records_c)
print(f"[OK] サンプルデータ生成完了: {total} 件")
print(f"  スタイルA: {path_a} ({len(records_a)} 件)")
print(f"  スタイルB: {path_b} ({len(records_b)} 件)")
print(f"  スタイルC: {path_c} ({len(records_c)} 件)")
