# -*- coding: utf-8 -*-
import os
import pandas as pd

FPATH = "output/cleaned_progress_202401.csv"
REQUIRED_COLS = [
    "work_date", "site_id", "site_name", "process", "worker_id",
    "planned_hours", "actual_hours", "progress_pct", "defect_count",
    "efficiency", "is_delayed", "kpi_flag", "source_file"
]

passed = 0
total = 18

def check(label, condition):
    global passed
    result = "[PASS]" if condition else "[FAIL]"
    if condition:
        passed += 1
    print(f"{result} {label}")

# 1. File exists
check("ファイル存在", os.path.exists(FPATH))

try:
    df = pd.read_csv(FPATH, encoding="utf-8-sig")
except Exception as e:
    print(f"[FAIL] CSV読み込みエラー: {e}")
    print(f"Result: {passed}/{total} checks passed")
    raise SystemExit(1)

# 2. Row count >= 380
check("行数>=380", len(df) >= 380)

# 3. Required columns
missing = [c for c in REQUIRED_COLS if c not in df.columns]
check("必須列が存在する", len(missing) == 0)

# 4. work_date format
try:
    pd.to_datetime(df["work_date"], format="%Y-%m-%d")
    date_ok = True
except Exception:
    date_ok = False
check("work_dateフォーマット(YYYY-MM-DD)", date_ok)

# 5. site_name 5 kinds
check("site_name 5種類", df["site_name"].nunique() == 5)

# 6. process 4 kinds
check("process 4種類", df["process"].nunique() == 4)

# 7. planned_hours > 0
check("planned_hours>0", (df["planned_hours"] > 0).all())

# 8. actual_hours > 0
check("actual_hours>0", (df["actual_hours"] > 0).all())

# 9. progress_pct in [0, 100]
check("progress_pct in [0,100]", df["progress_pct"].between(0, 100).all())

# 10. defect_count >= 0
check("defect_count>=0", (df["defect_count"] >= 0).all())

# 11. efficiency > 0
eff_valid = df["efficiency"].dropna()
check("efficiency>0", (eff_valid > 0).all())

# 12. is_delayed only 0/1
check("is_delayed 0/1のみ", set(df["is_delayed"].unique()).issubset({0, 1}))

# 13. kpi_flag == 2 kinds ("正常"/"問題あり")
check("kpi_flag種類==2", set(df["kpi_flag"].unique()) == {"正常", "問題あり"})

# 14. missing rate <= 15%
missing_rate = df.isnull().mean().max()
check("欠損率<=15%", missing_rate <= 0.15)

# 15. source_file 3 kinds
check("source_file 3種類", df["source_file"].nunique() == 3)

# 16. delayed count >= 1
check("遅延件数>=1", (df["is_delayed"] == 1).sum() >= 1)

# 17. problem KPI >= 1
check("問題ありKPI>=1", (df["kpi_flag"] == "問題あり").sum() >= 1)

# 18. worker count >= 15
check("作業員数>=15", df["worker_id"].nunique() >= 15)

print(f"\nResult: {passed}/{total} checks passed")
