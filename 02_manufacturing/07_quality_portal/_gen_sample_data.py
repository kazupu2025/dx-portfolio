"""
5システム分のサンプルCSVを生成する。
実行: python _gen_sample_data.py
生成先: 02_manufacturing/07_quality_portal/ 直下
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

rng = np.random.default_rng(42)
OUT = Path(__file__).parent

def date_range(year=2024, month=1):
    d = date(year, month, 1)
    days = []
    while d.month == month:
        days.append(d)
        d += timedelta(days=1)
    return days

dates = date_range()

# ① 月次不良率集計 (defect_rate)
lines = ["L1", "L2", "L3", "L4", "L5"]
products = ["製品A", "製品B", "製品C", "製品D"]
rows = []
for d in dates:
    for line in lines:
        for product in rng.choice(products, size=2, replace=False):
            inspected = int(rng.integers(80, 120))
            defect_rate = rng.uniform(0.005, 0.05) if line != "L3" else rng.uniform(0.03, 0.08)
            defects = int(inspected * defect_rate)
            rows.append({"日付": d, "ライン": line, "製品名": product,
                          "検査数": inspected, "不良数": defects})
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_defect_rate.csv", index=False, encoding="utf-8-sig")
print(f"sample_defect_rate.csv: {len(df)}件")

# ② クレーム件数集計 (claim)
suppliers = ["鈴木金属", "田中部品", "山田製作所", "佐藤工業", "高橋商事"]
categories = ["寸法不良", "外観不良", "機能不良", "梱包不良", "数量不足"]
statuses = ["未対応", "対応中", "完了"]
rows = []
for d in dates:
    n = int(rng.integers(1, 5))
    for _ in range(n):
        supplier = rng.choice(suppliers)
        cat = rng.choice(categories)
        status_probs = [0.2, 0.3, 0.5] if d < date(2024, 1, 20) else [0.1, 0.2, 0.7]
        status = rng.choice(statuses, p=status_probs)
        rows.append({"日付": d, "仕入先名": supplier,
                      "不良カテゴリ": cat, "対応状況": status})
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_claim.csv", index=False, encoding="utf-8-sig")
print(f"sample_claim.csv: {len(df)}件")

# ③ 歩留まりトレンド (yield_)
processes = ["切断", "溶接", "プレス", "塗装", "組立"]
rows = []
for d in dates:
    for proc in processes:
        input_qty = int(rng.integers(150, 250))
        yield_rate = rng.uniform(0.88, 0.98) if proc != "塗装" else rng.uniform(0.80, 0.92)
        passed = int(input_qty * yield_rate)
        rows.append({"日付": d, "工程名": proc, "投入数": input_qty, "合格数": passed})
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_yield.csv", index=False, encoding="utf-8-sig")
print(f"sample_yield.csv: {len(df)}件")

# ④ 検査員別実績 (inspector)
inspectors = ["田中", "鈴木", "佐藤", "山田", "中村", "伊藤", "渡辺", "高橋"]
shifts = ["日勤", "夜勤"]
rows = []
for d in dates:
    for shift in shifts:
        members = rng.choice(inspectors, size=4, replace=False)
        for name in members:
            inspected = int(rng.integers(60, 100))
            pass_rate = rng.uniform(0.90, 0.99)
            passed = int(inspected * pass_rate)
            rows.append({"日付": d, "検査員名": name, "シフト": shift,
                          "検査数": inspected, "合格数": passed})
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_inspector.csv", index=False, encoding="utf-8-sig")
print(f"sample_inspector.csv: {len(df)}件")

# ⑤ ロット別合否判定 (lot)
lot_products = ["製品A", "製品B", "製品C", "製品D", "製品E"]
inspection_items = ["寸法", "外観", "機能", "強度"]
rows = []
lot_num = 1
for d in dates:
    n_lots = int(rng.integers(3, 7))
    for _ in range(n_lots):
        lot_id = f"LOT-{lot_num:03d}"
        product = rng.choice(lot_products)
        for item in inspection_items:
            fail_prob = 0.05 if product != "製品C" else 0.12
            result = "不合格" if rng.random() < fail_prob else "合格"
            rows.append({"ロットID": lot_id, "製品名": product,
                          "検査日": d, "検査項目": item, "判定": result})
        lot_num += 1
df = pd.DataFrame(rows)
df.to_csv(OUT / "sample_lot.csv", index=False, encoding="utf-8-sig")
print(f"sample_lot.csv: {len(df)}件")

print("\n[OK] 全サンプルデータ生成完了")
