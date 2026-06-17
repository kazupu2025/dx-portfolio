# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas as pd

os.makedirs("output", exist_ok=True)

COLUMN_MAP = {
    # StyleA
    "作業日": "work_date",
    "現場ID": "site_id",
    "現場名": "site_name",
    "工程": "process",
    "作業員ID": "worker_id",
    "計画時間": "planned_hours",
    "実績時間": "actual_hours",
    "進捗率": "progress_pct",
    "不具合件数": "defect_count",
    # StyleB
    "WorkDate": "work_date",
    "SiteID": "site_id",
    "SiteName": "site_name",
    "Process": "process",
    "WorkerID": "worker_id",
    "PlannedHours": "planned_hours",
    "ActualHours": "actual_hours",
    "ProgressPct": "progress_pct",
    "DefectCount": "defect_count",
    # StyleC
    "施工日": "work_date",
    "現場コード": "site_id",
    "工事名": "site_name",
    "作業区分": "process",
    "職人ID": "worker_id",
    "予定時間": "planned_hours",
    "稼働時間": "actual_hours",
    "完了率": "progress_pct",
    "手戻り件数": "defect_count",
}

CANONICAL_COLS = [
    "work_date", "site_id", "site_name", "process", "worker_id",
    "planned_hours", "actual_hours", "progress_pct", "defect_count",
    "efficiency", "is_delayed", "kpi_flag", "source_file"
]

files = [
    ("data/style_a.csv", "style_a.csv"),
    ("data/style_b.csv", "style_b.csv"),
    ("data/style_c.csv", "style_c.csv"),
]

dfs = []
for fpath, fname in files:
    df = pd.read_csv(fpath, encoding="utf-8-sig")
    df = df.rename(columns=COLUMN_MAP)

    # Date normalization
    df["work_date"] = df["work_date"].astype(str).str.replace("/", "-")
    df["work_date"] = pd.to_datetime(df["work_date"], format="%Y-%m-%d").dt.strftime("%Y-%m-%d")

    # Numeric conversion
    for col in ["planned_hours", "actual_hours", "progress_pct", "defect_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derived columns
    df["efficiency"] = np.where(
        df["planned_hours"] > 0,
        df["actual_hours"] / df["planned_hours"],
        np.nan
    )
    df["is_delayed"] = (df["progress_pct"] < 70).astype(int)
    df["kpi_flag"] = np.where(
        (df["efficiency"] > 1.2) | (df["defect_count"] > 2),
        "問題あり",
        "正常"
    )
    df["source_file"] = fname

    dfs.append(df)
    print(f"[OK] Processed {fname}: {len(df)} rows")

combined = pd.concat(dfs, ignore_index=True)
combined = combined[CANONICAL_COLS]
combined.to_csv("output/cleaned_progress_202401.csv", index=False, encoding="utf-8-sig")
print(f"[OK] output/cleaned_progress_202401.csv: {len(combined)} rows")
