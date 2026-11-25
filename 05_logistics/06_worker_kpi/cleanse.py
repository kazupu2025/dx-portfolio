# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CANONICAL_COLS = [
    "work_date", "worker_id", "zone", "task_type",
    "processed_qty", "error_qty", "work_hours", "overtime_hours",
    "error_rate", "throughput", "kpi_flag", "source_file"
]

COLUMN_MAP = {
    # StyleA
    "作業日": "work_date",
    "作業員ID": "worker_id",
    "ゾーン": "zone",
    "作業区分": "task_type",
    "処理件数": "processed_qty",
    "エラー件数": "error_qty",
    "作業時間": "work_hours",
    "残業時間": "overtime_hours",
    # StyleB
    "WorkDate": "work_date",
    "WorkerID": "worker_id",
    "Zone": "zone",
    "TaskType": "task_type",
    "ProcessedQty": "processed_qty",
    "ErrorQty": "error_qty",
    "WorkHours": "work_hours",
    "OvertimeHours": "overtime_hours",
    # StyleC
    "日付": "work_date",
    "従業員番号": "worker_id",
    "エリア": "zone",
    "業務種別": "task_type",
    "処理数": "processed_qty",
    "誤処理数": "error_qty",
    "稼働時間": "work_hours",
    "残業": "overtime_hours",
}

files = [
    "worker_kpi_styleA.csv",
    "worker_kpi_styleB.csv",
    "worker_kpi_styleC.csv",
]

dfs = []
for fname in files:
    fpath = os.path.join(DATA_DIR, fname)
    df = pd.read_csv(fpath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)
    df["source_file"] = fname
    dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)

# Date normalization
combined["work_date"] = combined["work_date"].astype(str).str.replace("/", "-")
combined["work_date"] = pd.to_datetime(combined["work_date"], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")

# Numeric conversion
for col in ["processed_qty", "error_qty", "work_hours", "overtime_hours"]:
    combined[col] = pd.to_numeric(combined[col], errors="coerce")

# Derived columns
combined["error_rate"] = np.where(
    combined["processed_qty"] > 0,
    combined["error_qty"] / combined["processed_qty"],
    np.nan
)
combined["throughput"] = np.where(
    combined["work_hours"] > 0,
    combined["processed_qty"] / combined["work_hours"],
    np.nan
)

p75 = combined["throughput"].quantile(0.75)
combined["kpi_flag"] = np.where(
    combined["throughput"] > p75,
    "優秀",
    "標準"
)

output = combined[CANONICAL_COLS]
out_path = os.path.join(OUTPUT_DIR, "cleaned_worker_kpi_202401.csv")
output.to_csv(out_path, index=False, encoding="utf-8-sig")

print(f"[OK] Cleansed {len(output)} rows -> output/cleaned_worker_kpi_202401.csv")
print(f"[OK] Throughput 75th percentile: {p75:.2f}")
print(f"[OK] KPI flag distribution: {output['kpi_flag'].value_counts().to_dict()}")
