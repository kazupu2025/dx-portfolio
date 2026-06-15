import pandas as pd
import numpy as np
import random
from datetime import date, timedelta
from pathlib import Path

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/06_restaurant/02_cost_management")

stores = ["渋谷店", "新宿店", "池袋店", "品川店", "上野店"]
categories = ["野菜・果物", "肉類", "魚介類", "調味料・油", "乳製品・卵"]

# カテゴリ別食材定義（コード, 名前, 単価円/kg or 個）
ingredients = {
    "野菜・果物": [
        ("VG-001", "キャベツ",    120),  ("VG-002", "にんじん",   180),
        ("VG-003", "玉ねぎ",      150),  ("VG-004", "トマト",     300),
        ("VG-005", "レタス",      200),
    ],
    "肉類": [
        ("MT-001", "鶏もも肉",   800),  ("MT-002", "豚バラ",    1200),
        ("MT-003", "牛切り落とし", 2000), ("MT-004", "鶏むね肉",  600),
    ],
    "魚介類": [
        ("FS-001", "鮭",         1500), ("FS-002", "エビ",      2500),
        ("FS-003", "イカ",       1200), ("FS-004", "アジ",       800),
    ],
    "調味料・油": [
        ("SE-001", "醤油(L)",    400),  ("SE-002", "サラダ油(L)", 350),
        ("SE-003", "みりん(L)",  600),  ("SE-004", "塩(kg)",     200),
    ],
    "乳製品・卵": [
        ("DY-001", "牛乳(L)",    200),  ("DY-002", "バター(250g)", 450),
        ("DY-003", "卵(10個)",   250),  ("DY-004", "チーズ(kg)", 1800),
    ],
}

def business_days(year=2024, month=1):
    days = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days

bdays = business_days()


def gen_rows(store: str, n_per_day: int, col_style: str) -> list:
    rows = []
    for d in bdays:
        for _ in range(n_per_day):
            cat = random.choice(categories)
            ing_code, ing_name, unit_cost = random.choice(ingredients[cat])
            purchase_qty = round(float(rng.uniform(2.0, 20.0)), 1)
            # 使用量は仕入の70〜95%
            used_ratio = rng.uniform(0.70, 0.95)
            used_qty = round(purchase_qty * used_ratio, 1)
            # 廃棄量 = 仕入 - 使用（10%確率でロス率20%超の高廃棄）
            if rng.random() < 0.10:
                waste_qty = round(purchase_qty * rng.uniform(0.15, 0.30), 1)
                used_qty = round(purchase_qty - waste_qty, 1)
            else:
                waste_qty = round(purchase_qty - used_qty, 1)
            waste_qty = max(0.0, waste_qty)
            date_str = d.strftime("%Y/%m/%d")

            if col_style == "standard":
                rows.append({
                    "日付": date_str, "店舗": store, "食材コード": ing_code,
                    "食材名": ing_name, "カテゴリ": cat,
                    "仕入量(kg)": purchase_qty, "仕入単価(円)": unit_cost,
                    "使用量(kg)": used_qty, "廃棄量(kg)": waste_qty,
                })
            elif col_style == "english":
                rows.append({
                    "Date": date_str, "Store": store, "IngredientCode": ing_code,
                    "IngredientName": ing_name, "Category": cat,
                    "PurchaseQty": purchase_qty, "UnitCost": unit_cost,
                    "UsedQty": used_qty, "WasteQty": waste_qty,
                })
            else:  # variant
                rows.append({
                    "日付": date_str, "拠点": store, "品番": ing_code,
                    "品目": ing_name, "分類": cat,
                    "発注量": purchase_qty, "原価": unit_cost,
                    "使用数": used_qty, "ロス数": waste_qty,
                })
    return rows


files_config = [
    ("渋谷店", "standard", "01_渋谷店_仕入_202401.csv",   6),
    ("新宿店", "english",  "02_新宿店_cost_202401.csv",   5),
    ("池袋店", "variant",  "03_池袋店_仕入_202401.csv",   5),
    ("品川店", "standard", "04_品川店_仕入_202401.csv",   4),
    ("上野店", "standard", "05_上野店_仕入_202401.csv",   4),
]

for store, style, filename, n_per_day in files_config:
    rows = gen_rows(store, n_per_day, style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print(f"\nサンプルデータ生成完了（5店舗 × {len(bdays)}営業日）")
