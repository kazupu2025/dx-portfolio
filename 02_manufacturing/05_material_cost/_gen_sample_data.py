import pandas as pd
import numpy as np
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
rng = np.random.default_rng(42)

BASE = Path(__file__).parent
data_dir = BASE / "data"
data_dir.mkdir(exist_ok=True)

# 原材料定義: (コード, 名前, カテゴリ, ベース単価)
MATERIALS = [
    ("MAT-001", "熱延鋼板",     "鉄鋼",   85000),
    ("MAT-002", "冷延鋼板",     "鉄鋼",   92000),
    ("MAT-003", "ステンレス板", "鉄鋼",  210000),
    ("MAT-004", "形鋼(H鋼)",    "鉄鋼",   78000),
    ("MAT-005", "鋼管",         "鉄鋼",   96000),
    ("MAT-006", "アルミ板",     "非鉄金属", 320000),
    ("MAT-007", "銅線",         "非鉄金属", 980000),
    ("MAT-008", "亜鉛地金",     "非鉄金属", 420000),
    ("MAT-009", "ニッケル板",   "非鉄金属", 1850000),
    ("MAT-010", "チタン棒",     "非鉄金属", 2300000),
    ("MAT-011", "ABS樹脂",      "樹脂",    245000),
    ("MAT-012", "ポリプロピレン", "樹脂",  198000),
    ("MAT-013", "ナイロン66",   "樹脂",    430000),
    ("MAT-014", "PET樹脂",      "樹脂",    215000),
    ("MAT-015", "ポリカーボネート", "樹脂", 510000),
    ("MAT-016", "硫酸",         "化学品",   35000),
    ("MAT-017", "水酸化ナトリウム", "化学品", 48000),
    ("MAT-018", "エタノール",   "化学品",  125000),
    ("MAT-019", "アセトン",     "化学品",   95000),
    ("MAT-020", "塩酸",         "化学品",   28000),
]

SUPPLIERS = ["SUP-A", "SUP-B", "SUP-C", "SUP-D", "SUP-E"]

# 単価変動シミュレーション: ベース単価に月次変動を適用
# 各原材料の「前月比」をランダム生成（seed固定済み）
def gen_price_pair(base_price):
    """(unit_price, prev_month_price) を返す。10%の確率で急騰・急落。"""
    if rng.random() < 0.10:
        # 急騰または急落: ±20%超
        direction = 1 if rng.random() < 0.5 else -1
        change_rate = direction * rng.uniform(0.20, 0.35)
    else:
        change_rate = rng.uniform(-0.20, 0.20)
    prev = base_price * rng.uniform(0.85, 1.15)
    prev = round(prev, 0)
    unit = prev * (1 + change_rate)
    unit = max(unit, prev * 0.3)  # 下限保護
    return round(unit, 0), round(prev, 0)


def business_days(year=2024, month=1):
    days = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


bdays = business_days()


def gen_rows_style_a(n_rows):
    """スタイルA: 標準日本語列名、YYYY/MM/DD"""
    rows = []
    for _ in range(n_rows):
        mat = random.choice(MATERIALS)
        code, name, cat, base = mat
        supplier = random.choice(SUPPLIERS)
        d = random.choice(bdays)
        qty = round(rng.uniform(1.0, 50.0), 2)
        unit, prev = gen_price_pair(base)
        rows.append({
            "仕入日":      d.strftime("%Y/%m/%d"),
            "原材料コード": code,
            "原材料名":    name,
            "カテゴリ":    cat,
            "仕入先":      supplier,
            "数量":        qty,
            "単価":        unit,
            "前月単価":    prev,
        })
    return rows


def gen_rows_style_b(n_rows):
    """スタイルB: 英語列名、YYYY-MM-DD"""
    rows = []
    for _ in range(n_rows):
        mat = random.choice(MATERIALS)
        code, name, cat, base = mat
        supplier = random.choice(SUPPLIERS)
        d = random.choice(bdays)
        qty = round(rng.uniform(1.0, 50.0), 2)
        unit, prev = gen_price_pair(base)
        rows.append({
            "PurchaseDate":    d.strftime("%Y-%m-%d"),
            "MaterialCode":    code,
            "MaterialName":    name,
            "Category":        cat,
            "Supplier":        supplier,
            "Quantity":        qty,
            "UnitPrice":       unit,
            "PrevMonthPrice":  prev,
        })
    return rows


def gen_rows_style_c(n_rows):
    """スタイルC: バリアント日本語列名、YYYY/MM/DD"""
    rows = []
    for _ in range(n_rows):
        mat = random.choice(MATERIALS)
        code, name, cat, base = mat
        supplier = random.choice(SUPPLIERS)
        d = random.choice(bdays)
        qty = round(rng.uniform(1.0, 50.0), 2)
        unit, prev = gen_price_pair(base)
        rows.append({
            "購入日":   d.strftime("%Y/%m/%d"),
            "品目コード": code,
            "品目名":   name,
            "品種":     cat,
            "取引先":   supplier,
            "購入数量": qty,
            "仕入単価": unit,
            "先月単価": prev,
        })
    return rows


files_config = [
    ("style_a_material_202401.csv", gen_rows_style_a, 160),
    ("style_b_material_202401.csv", gen_rows_style_b, 140),
    ("style_c_material_202401.csv", gen_rows_style_c, 140),
]

total = 0
for filename, gen_fn, n_rows in files_config:
    rows = gen_fn(n_rows)
    df = pd.DataFrame(rows)
    out_path = data_dir / filename
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    total += len(df)
    print(f"Created {filename}: {len(df)} rows")

print(f"\nSample data generation complete. Total rows: {total}")
