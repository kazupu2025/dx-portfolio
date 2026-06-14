import pandas as pd
import random
from pathlib import Path

random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory")

categories = ["食料品", "日用品", "電子部品", "衣料品", "工業用品"]
items_by_cat = {
    "食料品":   [("コメ25kg", 8000, 50), ("小麦粉20kg", 4500, 30), ("食用油18L", 3200, 20), ("砂糖50kg", 6000, 15)],
    "日用品":   [("洗剤業務用", 2800, 40), ("ティッシュ箱", 1200, 80), ("トイレットペーパー", 1500, 60)],
    "電子部品": [("基板A型", 15000, 5), ("センサーB型", 8500, 8), ("ケーブル10m", 2200, 25), ("コネクタC", 450, 100)],
    "衣料品":   [("作業着M", 4200, 10), ("安全靴26cm", 6800, 8), ("手袋L", 320, 200)],
    "工業用品": [("ボルトM6×50", 120, 500), ("グリース缶", 1800, 30), ("切削油5L", 2500, 20)],
}


def gen_rows(warehouse_name: str, n: int = 120, col_style: str = "standard") -> list:
    rows = []
    for _ in range(n):
        day = random.randint(1, 28)
        date_str = f"2024/01/{day:02d}"
        cat = random.choice(categories)
        item_name, unit_cost, typical_stock = random.choice(items_by_cat[cat])
        item_code = f"ITM-{abs(hash(item_name)) % 9000 + 1000}"
        min_stock = int(typical_stock * random.uniform(0.2, 0.4))
        if random.random() < 0.10:
            stock_qty = random.randint(0, max(0, min_stock - 1))
        else:
            stock_qty = int(typical_stock * random.uniform(0.5, 1.5))
        received_qty = random.randint(0, int(typical_stock * 0.3))
        shipped_qty = random.randint(0, min(stock_qty, int(typical_stock * 0.2)))

        if col_style == "standard":
            rows.append({
                "日付": date_str, "倉庫名": warehouse_name,
                "品目コード": item_code, "品目名": item_name, "カテゴリ": cat,
                "在庫数量": stock_qty, "最低在庫数": min_stock,
                "単価": unit_cost, "入庫数量": received_qty, "出庫数量": shipped_qty,
            })
        elif col_style == "english":
            rows.append({
                "Date": date_str, "Warehouse": warehouse_name,
                "ItemCode": item_code, "ItemName": item_name, "Category": cat,
                "StockQty": stock_qty, "MinStock": min_stock,
                "UnitCost": unit_cost, "ReceivedQty": received_qty, "ShippedQty": shipped_qty,
            })
        elif col_style == "variant":
            rows.append({
                "集計日": date_str, "倉庫": warehouse_name,
                "コード": item_code, "品名": item_name, "分類": cat,
                "在庫": stock_qty, "安全在庫": min_stock,
                "原価": unit_cost, "入庫": received_qty, "出庫": shipped_qty,
            })
    return rows


warehouses = [
    ("東京第1倉庫", "standard", "01_東京第1倉庫_在庫_202401.csv"),
    ("大阪第2倉庫", "english",  "02_大阪第2倉庫_在庫_202401.csv"),
    ("名古屋倉庫",  "variant",  "03_名古屋倉庫_在庫_202401.csv"),
    ("福岡倉庫",    "standard", "04_福岡倉庫_在庫_202401.csv"),
    ("札幌倉庫",    "standard", "05_札幌倉庫_在庫_202401.csv"),
]

for warehouse_name, style, filename in warehouses:
    n = random.randint(110, 160)
    rows = gen_rows(warehouse_name, n=n, col_style=style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("\nサンプルデータ生成完了（5倉庫）")
