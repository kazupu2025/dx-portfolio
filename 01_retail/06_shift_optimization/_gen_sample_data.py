# -*- coding: utf-8 -*-
import random
import numpy as np
import pandas as pd
import os

random.seed(42)
np.random.seed(42)

STORES = [
    ("S001", "新宿店"),
    ("S002", "渋谷店"),
    ("S003", "池袋店"),
    ("S004", "銀座店"),
    ("S005", "品川店"),
]
ROLES = ["レジ", "品出し", "フロア"]
DATES = pd.date_range("2024-01-01", "2024-01-20")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def gen_rows():
    rows = []
    for date in DATES:
        for store_id, store_name in STORES:
            for role in ROLES:
                required_staff = random.randint(1, 5)
                actual_staff = random.randint(0, 6)
                work_hours = random.randint(6, 10)
                hourly_rate = random.randint(1000, 1300)
                rows.append({
                    "date": date,
                    "store_id": store_id,
                    "store_name": store_name,
                    "role": role,
                    "required_staff": required_staff,
                    "actual_staff": actual_staff,
                    "work_hours": work_hours,
                    "hourly_rate": hourly_rate,
                })
    return rows


rows = gen_rows()

# StyleA: Japanese headers, YYYY/MM/DD
df_a = pd.DataFrame([{
    "シフト日": r["date"].strftime("%Y/%m/%d"),
    "店舗コード": r["store_id"],
    "店舗名": r["store_name"],
    "役割": r["role"],
    "必要人員": r["required_staff"],
    "実員数": r["actual_staff"],
    "勤務時間": r["work_hours"],
    "時給": r["hourly_rate"],
} for r in rows])
df_a.to_csv(os.path.join(DATA_DIR, "shift_styleA.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleA generated:", len(df_a), "rows")

# StyleB: English headers, YYYY-MM-DD
df_b = pd.DataFrame([{
    "ShiftDate": r["date"].strftime("%Y-%m-%d"),
    "StoreID": r["store_id"],
    "StoreName": r["store_name"],
    "Role": r["role"],
    "RequiredStaff": r["required_staff"],
    "ActualStaff": r["actual_staff"],
    "WorkHours": r["work_hours"],
    "HourlyRate": r["hourly_rate"],
} for r in rows])
df_b.to_csv(os.path.join(DATA_DIR, "shift_styleB.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleB generated:", len(df_b), "rows")

# StyleC: Variant Japanese headers, YYYY/MM/DD
df_c = pd.DataFrame([{
    "勤務日": r["date"].strftime("%Y/%m/%d"),
    "店舗ID": r["store_id"],
    "店舗": r["store_name"],
    "ポジション": r["role"],
    "必要スタッフ数": r["required_staff"],
    "出勤スタッフ数": r["actual_staff"],
    "作業時間": r["work_hours"],
    "賃金": r["hourly_rate"],
} for r in rows])
df_c.to_csv(os.path.join(DATA_DIR, "shift_styleC.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleC generated:", len(df_c), "rows")

print("[OK] All sample data generated in", DATA_DIR)
