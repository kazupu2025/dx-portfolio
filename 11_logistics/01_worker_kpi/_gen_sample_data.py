# -*- coding: utf-8 -*-
import os
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

WORKERS = [f"WRK-{str(i).zfill(3)}" for i in range(1, 21)]
ZONES_JA = ["入荷", "保管", "出荷", "検品"]
ZONES_EN = ["Inbound", "Storage", "Outbound", "Inspection"]
TASKS_JA = ["フォークリフト", "ピッキング", "仕分け"]
TASKS_EN = ["Forklift", "Picking", "Sorting"]

dates = pd.date_range("2024-01-01", "2024-01-20")

rows = []
for d in dates:
    for w in WORKERS:
        rows.append({
            "date": d,
            "worker_id": w,
            "zone_idx": random.randint(0, 3),
            "task_idx": random.randint(0, 2),
            "processed_qty": random.randint(50, 300),
            "error_qty": random.randint(0, 10),
            "work_hours": round(random.uniform(6, 10), 1),
            "overtime_hours": round(random.uniform(0, 3), 1),
        })

df_base = pd.DataFrame(rows)

# StyleA: Japanese columns, YYYY/MM/DD
df_a = pd.DataFrame({
    "作業日": df_base["date"].dt.strftime("%Y/%m/%d"),
    "作業員ID": df_base["worker_id"],
    "ゾーン": df_base["zone_idx"].apply(lambda i: ZONES_JA[i]),
    "作業区分": df_base["task_idx"].apply(lambda i: TASKS_JA[i]),
    "処理件数": df_base["processed_qty"],
    "エラー件数": df_base["error_qty"],
    "作業時間": df_base["work_hours"],
    "残業時間": df_base["overtime_hours"],
})
df_a.to_csv(os.path.join(DATA_DIR, "worker_kpi_styleA.csv"), index=False, encoding="utf-8-sig")

# StyleB: English columns, YYYY-MM-DD
df_b = pd.DataFrame({
    "WorkDate": df_base["date"].dt.strftime("%Y-%m-%d"),
    "WorkerID": df_base["worker_id"],
    "Zone": df_base["zone_idx"].apply(lambda i: ZONES_JA[i]),
    "TaskType": df_base["task_idx"].apply(lambda i: TASKS_JA[i]),
    "ProcessedQty": df_base["processed_qty"],
    "ErrorQty": df_base["error_qty"],
    "WorkHours": df_base["work_hours"],
    "OvertimeHours": df_base["overtime_hours"],
})
df_b.to_csv(os.path.join(DATA_DIR, "worker_kpi_styleB.csv"), index=False, encoding="utf-8-sig")

# StyleC: Variant Japanese columns, YYYY/MM/DD
df_c = pd.DataFrame({
    "日付": df_base["date"].dt.strftime("%Y/%m/%d"),
    "従業員番号": df_base["worker_id"],
    "エリア": df_base["zone_idx"].apply(lambda i: ZONES_JA[i]),
    "業務種別": df_base["task_idx"].apply(lambda i: TASKS_JA[i]),
    "処理数": df_base["processed_qty"],
    "誤処理数": df_base["error_qty"],
    "稼働時間": df_base["work_hours"],
    "残業": df_base["overtime_hours"],
})
df_c.to_csv(os.path.join(DATA_DIR, "worker_kpi_styleC.csv"), index=False, encoding="utf-8-sig")

print(f"[OK] StyleA: {len(df_a)} rows -> data/worker_kpi_styleA.csv")
print(f"[OK] StyleB: {len(df_b)} rows -> data/worker_kpi_styleB.csv")
print(f"[OK] StyleC: {len(df_c)} rows -> data/worker_kpi_styleC.csv")
print("[OK] Sample data generation complete.")
