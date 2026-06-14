"""
A-02 サンプルデータ生成スクリプト（5店舗・3列名バリエーション）
実行: C:\Users\realp\miniconda3\python.exe _gen_sample_data.py
"""
import pandas as pd
import random
from pathlib import Path

random.seed(42)
out = Path(".")

categories = ["麺類", "ご飯もの", "副菜", "ドリンク", "デザート"]
items_by_cat = {
    "麺類":    [("ラーメン", 900), ("つけ麺", 1000), ("担々麺", 980), ("塩ラーメン", 880)],
    "ご飯もの": [("チャーハン", 750), ("カレーライス", 800), ("天丼", 950)],
    "副菜":    [("餃子", 450), ("唐揚げ", 550), ("春巻き", 400)],
    "ドリンク": [("ウーロン茶", 250), ("コーラ", 300), ("ビール", 550)],
    "デザート": [("杏仁豆腐", 380), ("アイスクリーム", 400)],
}


def gen_rows(store_name, n=120, col_style="standard"):
    rows = []
    for _ in range(n):
        day = random.randint(1, 28)
        date_str = f"2024/01/{day:02d}"
        cat = random.choice(categories)
        item, price = random.choice(items_by_cat[cat])
        qty = random.randint(1, 8)
        sales = qty * price
        waste_qty = random.choices([0, 1, 2], weights=[0.7, 0.2, 0.1])[0]
        waste_amount = waste_qty * price

        if col_style == "standard":
            rows.append({"日付": date_str, "店舗名": store_name, "商品名": item,
                         "カテゴリ": cat, "数量": qty, "単価": price, "売上金額": sales,
                         "廃棄数量": waste_qty, "廃棄金額": waste_amount})
        elif col_style == "english":
            rows.append({"Date": date_str, "Store": store_name, "Item": item,
                         "Category": cat, "Qty": qty, "Price": price, "Sales": sales,
                         "WasteQty": waste_qty, "WasteAmount": waste_amount})
        elif col_style == "variant":
            rows.append({"日付け": date_str, "店舗": store_name, "品名": item,
                         "分類": cat, "個数": qty, "単価": price, "売上額": sales,
                         "廃棄": waste_qty, "廃棄金額": waste_amount})
    return rows


stores = [
    ("渋谷店", "standard", "01_渋谷店_売上_202401.csv"),
    ("新宿店", "english",  "02_新宿店_売上_202401.csv"),
    ("池袋店", "variant",  "03_池袋店_売上_202401.csv"),
    ("横浜店", "standard", "04_横浜店_売上_202401.csv"),
    ("大阪店", "standard", "05_大阪店_売上_202401.csv"),
]

for store_name, style, filename in stores:
    n = random.randint(110, 150)
    rows = gen_rows(store_name, n=n, col_style=style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("\nサンプルデータ生成完了（5店舗）")
