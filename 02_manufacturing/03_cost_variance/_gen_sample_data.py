"""サンプルデータ生成スクリプト - 3スタイルのCSVを data/ に生成"""
import os
import random
import pandas as pd
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS = [
    ("P001","部品A"),("P002","部品B"),("P003","部品C"),("P004","部品D"),("P005","部品E"),
    ("P006","ユニットX"),("P007","ユニットY"),("P008","ユニットZ"),("P009","製品P"),("P010","製品Q"),
    ("P011","PartA"),("P012","PartB"),("P013","PartC"),("P014","SubAsmX"),("P015","SubAsmY"),
    ("P016","FinGoodA"),("P017","FinGoodB"),("P018","FinGoodC"),("P019","FinGoodD"),("P020","FinGoodE"),
]
LINES = ["ライン1","ライン2","ライン3"]
DATES = pd.date_range("2024-01-01","2024-01-07")

def gen_base_rows():
    rows = []
    for date in DATES:
        for line in LINES:
            for pid, pname in PRODUCTS:
                planned_qty = random.randint(50, 200)
                # 10% chance of shortfall
                if random.random() < 0.10:
                    actual_qty = int(planned_qty * random.uniform(0.70, 0.95))
                else:
                    actual_qty = int(planned_qty * random.uniform(0.90, 1.10))

                base_material = random.uniform(50000, 200000)
                base_labor = random.uniform(20000, 80000)
                base_overhead = random.uniform(10000, 50000)

                planned_material = round(base_material, 0)
                planned_labor = round(base_labor, 0)
                planned_overhead = round(base_overhead, 0)

                actual_material = round(base_material * random.uniform(0.80, 1.20), 0)
                actual_labor = round(base_labor * random.uniform(0.80, 1.20), 0)
                actual_overhead = round(base_overhead * random.uniform(0.80, 1.20), 0)

                rows.append({
                    "pid": pid,
                    "pname": pname,
                    "date": date.strftime("%Y-%m-%d"),
                    "line": line,
                    "planned_qty": planned_qty,
                    "actual_qty": actual_qty,
                    "planned_material": planned_material,
                    "actual_material": actual_material,
                    "planned_labor": planned_labor,
                    "actual_labor": actual_labor,
                    "planned_overhead": planned_overhead,
                    "actual_overhead": actual_overhead,
                })
    return rows

rows = gen_base_rows()

# Style A (standard Japanese)
df_a = pd.DataFrame([{
    "製品ID": r["pid"], "製品名": r["pname"], "製造日": r["date"],
    "ラインID": r["line"],
    "計画数量": r["planned_qty"], "実績数量": r["actual_qty"],
    "計画材料費": r["planned_material"], "実績材料費": r["actual_material"],
    "計画労務費": r["planned_labor"], "実績労務費": r["actual_labor"],
    "計画間接費": r["planned_overhead"], "実績間接費": r["actual_overhead"],
} for r in rows[:140]])

# Style B (English)
df_b = pd.DataFrame([{
    "product_id": r["pid"], "product_name": r["pname"], "production_date": r["date"],
    "line_id": r["line"],
    "planned_qty": r["planned_qty"], "actual_qty": r["actual_qty"],
    "planned_material": r["planned_material"], "actual_material": r["actual_material"],
    "planned_labor": r["planned_labor"], "actual_labor": r["actual_labor"],
    "planned_overhead": r["planned_overhead"], "actual_overhead": r["actual_overhead"],
} for r in rows[140:280]])

# Style C (alternate Japanese)
df_c = pd.DataFrame([{
    "品番": r["pid"], "品目": r["pname"], "生産日": r["date"],
    "製造ライン": r["line"],
    "計画生産数": r["planned_qty"], "実績生産数": r["actual_qty"],
    "材料費予算": r["planned_material"], "材料費実績": r["actual_material"],
    "労務費予算": r["planned_labor"], "労務費実績": r["actual_labor"],
    "製造間接費予算": r["planned_overhead"], "製造間接費実績": r["actual_overhead"],
} for r in rows[280:]])

df_a.to_csv(DATA_DIR / "production_cost_styleA_202401.csv", index=False, encoding="utf-8-sig")
df_b.to_csv(DATA_DIR / "production_cost_styleB_202401.csv", index=False, encoding="utf-8-sig")
df_c.to_csv(DATA_DIR / "production_cost_styleC_202401.csv", index=False, encoding="utf-8-sig")

print(f"生成完了: A={len(df_a)}行, B={len(df_b)}行, C={len(df_c)}行, 合計={len(df_a)+len(df_b)+len(df_c)}行")
