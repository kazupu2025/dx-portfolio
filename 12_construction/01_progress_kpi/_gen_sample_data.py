# -*- coding: utf-8 -*-
import os
import random
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

os.makedirs("data", exist_ok=True)

SITES = [
    ("SITE-A", "現場A"),
    ("SITE-B", "現場B"),
    ("SITE-C", "現場C"),
    ("SITE-D", "現場D"),
    ("SITE-E", "現場E"),
]
PROCESSES = ["基礎", "躯体", "内装", "設備"]
WORKERS = [f"WRK-{i:03d}" for i in range(1, 21)]
DATES = pd.date_range("2024-01-01", "2024-01-20").strftime("%Y-%m-%d").tolist()

rows = []
for worker_id in WORKERS:
    for date in DATES:
        site_id, site_name = random.choice(SITES)
        process = random.choice(PROCESSES)
        planned_hours = round(random.uniform(6, 8), 1)
        actual_hours = round(random.uniform(4, 10), 1)
        progress_pct = random.randint(30, 100)
        defect_count = random.randint(0, 5)
        rows.append([date, site_id, site_name, process, worker_id,
                     planned_hours, actual_hours, progress_pct, defect_count])

df = pd.DataFrame(rows, columns=[
    "work_date", "site_id", "site_name", "process", "worker_id",
    "planned_hours", "actual_hours", "progress_pct", "defect_count"
])

# StyleA: Japanese columns, date YYYY/MM/DD
df_a = df.copy()
df_a["work_date"] = df_a["work_date"].str.replace("-", "/")
df_a.columns = ["作業日", "現場ID", "現場名", "工程", "作業員ID",
                "計画時間", "実績時間", "進捗率", "不具合件数"]
df_a.to_csv("data/style_a.csv", index=False, encoding="utf-8-sig")
print("[OK] data/style_a.csv generated:", len(df_a), "rows")

# StyleB: English columns, date YYYY-MM-DD
df_b = df.copy()
df_b.columns = ["WorkDate", "SiteID", "SiteName", "Process", "WorkerID",
                "PlannedHours", "ActualHours", "ProgressPct", "DefectCount"]
df_b.to_csv("data/style_b.csv", index=False, encoding="utf-8-sig")
print("[OK] data/style_b.csv generated:", len(df_b), "rows")

# StyleC: Variant Japanese columns, date YYYY/MM/DD
df_c = df.copy()
df_c["work_date"] = df_c["work_date"].str.replace("-", "/")
df_c.columns = ["施工日", "現場コード", "工事名", "作業区分", "職人ID",
                "予定時間", "稼働時間", "完了率", "手戻り件数"]
df_c.to_csv("data/style_c.csv", index=False, encoding="utf-8-sig")
print("[OK] data/style_c.csv generated:", len(df_c), "rows")
