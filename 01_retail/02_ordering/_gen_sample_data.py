"""
B-10 サンプルデータ生成スクリプト
50商品 × 92日（2023年10月〜12月）の日次売上・在庫データを生成する
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from pathlib import Path
import random

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/01_retail/02_ordering")

categories = {
    "食品": [
        ("P-F001", "コーヒー豆 200g"),   ("P-F002", "緑茶パック"),
        ("P-F003", "即席ラーメン"),        ("P-F004", "チョコレート"),
        ("P-F005", "スナック菓子"),        ("P-F006", "ヨーグルト"),
        ("P-F007", "バター"),              ("P-F008", "食パン"),
        ("P-F009", "ジャム"),              ("P-F010", "缶詰セット"),
    ],
    "飲料": [
        ("P-D001", "ミネラルウォーター 2L"), ("P-D002", "コーラ 1.5L"),
        ("P-D003", "オレンジジュース"),       ("P-D004", "麦茶パック"),
        ("P-D005", "スポーツドリンク"),       ("P-D006", "アイスコーヒー"),
        ("P-D007", "緑茶 500ml"),             ("P-D008", "牛乳 1L"),
        ("P-D009", "豆乳"),                   ("P-D010", "炭酸水"),
    ],
    "日用品": [
        ("P-H001", "シャンプー"),      ("P-H002", "ボディソープ"),
        ("P-H003", "歯ブラシ"),        ("P-H004", "歯磨き粉"),
        ("P-H005", "トイレットペーパー"), ("P-H006", "洗剤"),
        ("P-H007", "柔軟剤"),           ("P-H008", "ティッシュ"),
        ("P-H009", "除菌シート"),       ("P-H010", "マスク"),
    ],
    "衣料": [
        ("P-C001", "Tシャツ L"),    ("P-C002", "ソックス 3足"),
        ("P-C003", "インナー M"),   ("P-C004", "ハンカチ"),
        ("P-C005", "ベルト"),       ("P-C006", "帽子"),
        ("P-C007", "手袋"),         ("P-C008", "スカーフ"),
        ("P-C009", "エプロン"),     ("P-C010", "作業着 L"),
    ],
    "電化製品": [
        ("P-E001", "USB充電ケーブル"), ("P-E002", "電池 AA 4本"),
        ("P-E003", "電球 LED"),        ("P-E004", "延長コード"),
        ("P-E005", "ライター"),         ("P-E006", "単三電池 6本"),
        ("P-E007", "スマホスタンド"),  ("P-E008", "マウスパッド"),
        ("P-E009", "キーボードカバー"),("P-E010", "画面クリーナー"),
    ],
}

# カテゴリ別の平均日次販売数
base_demand = {
    "食品": 25, "飲料": 40, "日用品": 15, "衣料": 8, "電化製品": 5,
}
# 曜日係数（月=0.9, 火=0.85, 水=0.95, 木=1.0, 金=1.2, 土=1.5, 日=1.4）
weekday_factors = [0.9, 0.85, 0.95, 1.0, 1.2, 1.5, 1.4]


def gen_days(start: date, n: int):
    return [start + timedelta(days=i) for i in range(n)]


# 2023-10-01〜2023-12-31 の92日間
train_start = date(2023, 10, 1)
all_days = gen_days(train_start, 92)

# スタイル割り当て（カテゴリ別）
cat_styles = {
    "食品":   ("standard", "01_食品_日次売上_2023Q4.csv"),
    "飲料":   ("english",  "02_beverages_daily_2023Q4.csv"),
    "日用品": ("standard", "03_日用品_日次売上_2023Q4.csv"),
    "衣料":   ("variant",  "04_衣料_日次売上_2023Q4.csv"),
    "電化製品":("variant", "05_電化製品_日次売上_2023Q4.csv"),
}

for cat, products in categories.items():
    style, filename = cat_styles[cat]
    base = base_demand[cat]
    rows = []
    lead_time_days = 3
    for prod_id, prod_name in products:
        trend_slope = rng.uniform(-0.05, 0.10)  # 緩やかなトレンド
        stock = int(base * 10 + rng.integers(0, 50))
        reorder_pt = int(base * lead_time_days * 1.5)
        for i, d in enumerate(all_days):
            wf = weekday_factors[d.weekday()]
            trend = 1.0 + trend_slope * i / 92
            demand = float(rng.normal(base * wf * trend, base * 0.2))
            sales = max(0, min(int(demand), stock))
            stock = max(0, stock - sales)
            if stock < reorder_pt:
                order_qty = int(base * 14)
                stock += order_qty
            else:
                order_qty = 0

            ts = d.strftime("%Y/%m/%d")
            if style == "standard":
                rows.append({
                    "日付": ts, "商品ID": prod_id, "商品名": prod_name,
                    "カテゴリ": cat, "販売数量": sales, "在庫数量": stock,
                    "発注点": reorder_pt, "入荷数量": order_qty, "リードタイム(日)": 3,
                })
            elif style == "english":
                rows.append({
                    "Date": ts, "ProductID": prod_id, "ProductName": prod_name,
                    "Category": cat, "SalesQty": sales, "StockQty": stock,
                    "ReorderPoint": reorder_pt, "OrderQty": order_qty, "LeadTimeDays": 3,
                })
            else:
                rows.append({
                    "日付": ts, "品番": prod_id, "品名": prod_name,
                    "分類": cat, "売数": sales, "在庫": stock,
                    "発注点": reorder_pt, "入荷量": order_qty, "リード日数": 3,
                })
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("サンプルデータ生成完了（50商品 × 92日）")
