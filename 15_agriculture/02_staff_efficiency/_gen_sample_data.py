# -*- coding: utf-8 -*-
"""
C-59 農場スタッフ勤怠・作業効率分析パイプライン
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

STAFF_IDS = [f"STAFF-{i:02d}" for i in range(1, 11)]
WORK_TYPES_JP = ["播種", "施肥", "収穫", "管理作業"]
CROPS_JP = ["トマト", "キュウリ", "レタス", "イチゴ", "ホウレンソウ"]
DATES = pd.date_range("2024-01-01", "2024-01-20", freq="D")

# --- Generate base 480 records ---
records = []
for i in range(480):
    rec_id = f"AGR-{i+1:04d}"
    dt = random.choice(DATES)
    staff = random.choice(STAFF_IDS)
    work_type = random.choice(WORK_TYPES_JP)
    crop = random.choice(CROPS_JP)
    work_hours = round(random.uniform(2.0, 10.0), 1)
    target_qty = random.randint(100, 1000)
    actual_qty = round(target_qty * random.uniform(0.6, 1.2))
    is_target_met = 1 if actual_qty >= target_qty else 0
    records.append({
        "date_dash": dt.strftime("%Y-%m-%d"),
        "date_slash": dt.strftime("%Y/%m/%d"),
        "record_id": rec_id,
        "staff_id": staff,
        "work_type": work_type,
        "crop": crop,
        "work_hours": work_hours,
        "target_qty": target_qty,
        "actual_qty": int(actual_qty),
        "is_target_met": is_target_met,
    })

df_all = pd.DataFrame(records)

# --- Split 1/3 each (160 records per style) ---
df_a = df_all.iloc[:160].copy()
df_b = df_all.iloc[160:320].copy()
df_c = df_all.iloc[320:480].copy()

# StyleA: 標準日本語、日付 YYYY/MM/DD
style_a = pd.DataFrame({
    "作業日": df_a["date_slash"].values,
    "記録ID": df_a["record_id"].values,
    "スタッフID": df_a["staff_id"].values,
    "作業区分": df_a["work_type"].values,
    "作物": df_a["crop"].values,
    "作業時間": df_a["work_hours"].values,
    "目標数量": df_a["target_qty"].values,
    "実績数量": df_a["actual_qty"].values,
    "目標達成": df_a["is_target_met"].values,
})

# StyleB: English、日付 YYYY-MM-DD
style_b = pd.DataFrame({
    "WorkDate": df_b["date_dash"].values,
    "RecordID": df_b["record_id"].values,
    "StaffID": df_b["staff_id"].values,
    "WorkType": df_b["work_type"].values,
    "Crop": df_b["crop"].values,
    "WorkHours": df_b["work_hours"].values,
    "TargetQty": df_b["target_qty"].values,
    "ActualQty": df_b["actual_qty"].values,
    "IsTargetMet": df_b["is_target_met"].values,
})

# StyleC: バリアント日本語、日付 YYYY/MM/DD
style_c = pd.DataFrame({
    "日付": df_c["date_slash"].values,
    "管理番号": df_c["record_id"].values,
    "作業者ID": df_c["staff_id"].values,
    "作業種別": df_c["work_type"].values,
    "栽培品目": df_c["crop"].values,
    "勤務時間": df_c["work_hours"].values,
    "計画量": df_c["target_qty"].values,
    "収穫量": df_c["actual_qty"].values,
    "達成フラグ": df_c["is_target_met"].values,
})

style_a.to_csv(os.path.join(OUTPUT_DIR, "farm_work_styleA.csv"), index=False, encoding="utf-8-sig")
style_b.to_csv(os.path.join(OUTPUT_DIR, "farm_work_styleB.csv"), index=False, encoding="utf-8-sig")
style_c.to_csv(os.path.join(OUTPUT_DIR, "farm_work_styleC.csv"), index=False, encoding="utf-8-sig")

print("[OK] StyleA saved:", len(style_a), "rows")
print("[OK] StyleB saved:", len(style_b), "rows")
print("[OK] StyleC saved:", len(style_c), "rows")
print("[OK] Total:", len(style_a) + len(style_b) + len(style_c), "rows")
