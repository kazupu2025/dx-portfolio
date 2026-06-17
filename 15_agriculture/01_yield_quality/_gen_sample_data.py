# -*- coding: utf-8 -*-
"""
C-49 作物収量・品質検査レポートパイプライン
サンプルデータ生成スクリプト (480件 / 3スタイル各160件)
"""

import random
import numpy as np
import pandas as pd
import os

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FARMS = [
    ("FARM-A", "農場A"),
    ("FARM-B", "農場B"),
    ("FARM-C", "農場C"),
    ("FARM-D", "農場D"),
]
CROPS_JP = ["トマト", "キュウリ", "ピーマン", "レタス", "ほうれん草"]
INSPECTORS = ["INS-01", "INS-02", "INS-03", "INS-04", "INS-05"]
DATES = pd.date_range("2024-01-01", "2024-01-20", freq="D")

# --- Generate base 480 records ---
records = []
for i in range(480):
    rec_id = f"REC-{i+1:04d}"
    dt = random.choice(DATES)
    farm = random.choice(FARMS)
    crop = random.choice(CROPS_JP)
    harvest_qty = round(random.uniform(50, 500), 1)
    grade_a_qty = round(random.uniform(0, harvest_qty), 1)
    defect_qty = round(random.uniform(0, harvest_qty * 0.10), 1)
    inspector = random.choice(INSPECTORS)
    records.append({
        "harvest_date_dash": dt.strftime("%Y-%m-%d"),
        "harvest_date_slash": dt.strftime("%Y/%m/%d"),
        "record_id": rec_id,
        "farm_id": farm[0],
        "farm_name_jp": farm[1],
        "crop_jp": crop,
        "harvest_qty": harvest_qty,
        "grade_a_qty": grade_a_qty,
        "defect_qty": defect_qty,
        "inspector_id": inspector,
    })

df_all = pd.DataFrame(records)

# --- Split 1/3 each ---
df_a = df_all.iloc[:160].copy()
df_b = df_all.iloc[160:320].copy()
df_c = df_all.iloc[320:480].copy()

# StyleA: 標準日本語、日付 YYYY/MM/DD
style_a = pd.DataFrame({
    "収穫日": df_a["harvest_date_slash"].values,
    "記録ID": df_a["record_id"].values,
    "農場ID": df_a["farm_id"].values,
    "農場名": df_a["farm_name_jp"].values,
    "作物名": df_a["crop_jp"].values,
    "収穫量(kg)": df_a["harvest_qty"].values,
    "A等級数量": df_a["grade_a_qty"].values,
    "不合格数量": df_a["defect_qty"].values,
    "検査員ID": df_a["inspector_id"].values,
})

# StyleB: English、日付 YYYY-MM-DD
style_b = pd.DataFrame({
    "HarvestDate": df_b["harvest_date_dash"].values,
    "RecordID": df_b["record_id"].values,
    "FarmID": df_b["farm_id"].values,
    "FarmName": df_b["farm_name_jp"].values,
    "Crop": df_b["crop_jp"].values,
    "HarvestQty": df_b["harvest_qty"].values,
    "GradeAQty": df_b["grade_a_qty"].values,
    "DefectQty": df_b["defect_qty"].values,
    "InspectorID": df_b["inspector_id"].values,
})

# StyleC: バリアント日本語、日付 YYYY/MM/DD
style_c = pd.DataFrame({
    "出荷日": df_c["harvest_date_slash"].values,
    "レコード番号": df_c["record_id"].values,
    "圃場ID": df_c["farm_id"].values,
    "圃場名": df_c["farm_name_jp"].values,
    "品目": df_c["crop_jp"].values,
    "収量kg": df_c["harvest_qty"].values,
    "A品数量": df_c["grade_a_qty"].values,
    "不良数量": df_c["defect_qty"].values,
    "担当検査員": df_c["inspector_id"].values,
})

style_a.to_csv(os.path.join(OUTPUT_DIR, "harvest_styleA.csv"), index=False, encoding="utf-8-sig")
style_b.to_csv(os.path.join(OUTPUT_DIR, "harvest_styleB.csv"), index=False, encoding="utf-8-sig")
style_c.to_csv(os.path.join(OUTPUT_DIR, "harvest_styleC.csv"), index=False, encoding="utf-8-sig")

print("[OK] StyleA saved:", len(style_a), "rows")
print("[OK] StyleB saved:", len(style_b), "rows")
print("[OK] StyleC saved:", len(style_c), "rows")
print("[OK] Total:", len(style_a) + len(style_b) + len(style_c), "rows")
