# -*- coding: utf-8 -*-
import os
import re
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_worker_kpi_202401.csv")

REQUIRED_COLS = [
    "work_date", "worker_id", "zone", "task_type",
    "processed_qty", "error_qty", "work_hours", "overtime_hours",
    "error_rate", "throughput", "kpi_flag", "source_file"
]
VALID_ZONES = {"入荷", "保管", "出荷", "検品"}
VALID_TASKS = {"フォークリフト", "ピッキング", "仕分け"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

results = []


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    results.append((status, label))
    print(f"{status} {label}")


# 1. File exists
check("ファイル存在確認", os.path.exists(CSV_PATH))

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig") if os.path.exists(CSV_PATH) else pd.DataFrame()

# 2. Row count >= 380
check("行数 >= 380", len(df) >= 380)

# 3. Required columns present
check("必須列が存在する", all(c in df.columns for c in REQUIRED_COLS))

# 4. work_date format YYYY-MM-DD
if "work_date" in df.columns:
    valid_dates = df["work_date"].astype(str).apply(lambda x: bool(DATE_PATTERN.match(x)))
    check("work_date フォーマット YYYY-MM-DD", valid_dates.all())
else:
    check("work_date フォーマット YYYY-MM-DD", False)

# 5. zone 4 types
if "zone" in df.columns:
    actual_zones = set(df["zone"].dropna().unique())
    check("zone が 4 種類存在", len(actual_zones) >= 4)
else:
    check("zone が 4 種類存在", False)

# 6. task_type 3 types
if "task_type" in df.columns:
    actual_tasks = set(df["task_type"].dropna().unique())
    check("task_type が 3 種類存在", len(actual_tasks) >= 3)
else:
    check("task_type が 3 種類存在", False)

# 7. processed_qty >= 1
if "processed_qty" in df.columns:
    check("processed_qty >= 1", (df["processed_qty"] >= 1).all())
else:
    check("processed_qty >= 1", False)

# 8. error_qty >= 0
if "error_qty" in df.columns:
    check("error_qty >= 0", (df["error_qty"] >= 0).all())
else:
    check("error_qty >= 0", False)

# 9. work_hours > 0
if "work_hours" in df.columns:
    check("work_hours > 0", (df["work_hours"] > 0).all())
else:
    check("work_hours > 0", False)

# 10. error_rate in [0, 1]
if "error_rate" in df.columns:
    valid_er = df["error_rate"].dropna()
    check("error_rate in [0,1]", ((valid_er >= 0) & (valid_er <= 1)).all())
else:
    check("error_rate in [0,1]", False)

# 11. throughput > 0
if "throughput" in df.columns:
    valid_tp = df["throughput"].dropna()
    check("throughput > 0", (valid_tp > 0).all())
else:
    check("throughput > 0", False)

# 12. kpi_flag has exactly 2 values
if "kpi_flag" in df.columns:
    kpi_vals = set(df["kpi_flag"].dropna().unique())
    check("kpi_flag 種類 == 2 (優秀/標準)", kpi_vals == {"優秀", "標準"})
else:
    check("kpi_flag 種類 == 2 (優秀/標準)", False)

# 13. Missing rate <= 15%
if len(df) > 0:
    missing_rate = df.isnull().sum().sum() / (len(df) * len(df.columns))
    check("欠損率 <= 15%", missing_rate <= 0.15)
else:
    check("欠損率 <= 15%", False)

# 14. source_file has 3 types
if "source_file" in df.columns:
    check("source_file が 3 種類存在", df["source_file"].nunique() >= 3)
else:
    check("source_file が 3 種類存在", False)

# 15. High KPI workers >= 1
if "kpi_flag" in df.columns:
    high_kpi = df[df["kpi_flag"] == "優秀"]["worker_id"].nunique() if "worker_id" in df.columns else 0
    check("高KPI作業員 >= 1", high_kpi >= 1)
else:
    check("高KPI作業員 >= 1", False)

# 16. Rows with error_rate > 0 >= 1
if "error_rate" in df.columns:
    check("エラー率 > 0 の行 >= 1", (df["error_rate"] > 0).sum() >= 1)
else:
    check("エラー率 > 0 の行 >= 1", False)

# 17. overtime_hours >= 0
if "overtime_hours" in df.columns:
    check("overtime_hours >= 0", (df["overtime_hours"] >= 0).all())
else:
    check("overtime_hours >= 0", False)

# 18. Worker count >= 15
if "worker_id" in df.columns:
    check("作業員数 >= 15", df["worker_id"].nunique() >= 15)
else:
    check("作業員数 >= 15", False)

passed = sum(1 for s, _ in results if s == "[PASS]")
total = len(results)
print(f"\nResult: {passed}/{total} checks passed")
