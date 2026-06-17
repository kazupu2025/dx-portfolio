# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_shift_202401.csv")

REQUIRED_COLS = [
    "shift_date", "store_id", "store_name", "role",
    "required_staff", "actual_staff", "work_hours", "hourly_rate",
    "daily_wage", "staffing_gap", "is_understaffed", "labor_cost_flag", "source_file"
]

EXPECTED_STORES = {"新宿店", "渋谷店", "池袋店", "銀座店", "品川店"}
EXPECTED_ROLES = {"レジ", "品出し", "フロア"}
EXPECTED_SOURCES = {"shift_styleA.csv", "shift_styleB.csv", "shift_styleC.csv"}

results = []


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {label}")
    results.append(condition)


# 1. File exists
check("ファイル存在確認", os.path.exists(CSV_PATH))

# Load if exists
if not os.path.exists(CSV_PATH):
    print("Result: 0/18 checks passed")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# 2. Row count >= 280
check("行数 >= 280", len(df) >= 280)

# 3. Required columns present
missing = [c for c in REQUIRED_COLS if c not in df.columns]
check("必須列の存在", len(missing) == 0)

# 4. shift_date format YYYY-MM-DD
import re
date_ok = df["shift_date"].dropna().apply(lambda x: bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(x)))).all()
check("shift_dateフォーマット(YYYY-MM-DD)", date_ok)

# 5. store_name 5 varieties
check("store_name 5種類", set(df["store_name"].unique()) == EXPECTED_STORES)

# 6. role 3 varieties
check("role 3種類", set(df["role"].unique()) == EXPECTED_ROLES)

# 7. required_staff >= 1
check("required_staff >= 1", (df["required_staff"] >= 1).all())

# 8. actual_staff >= 0
check("actual_staff >= 0", (df["actual_staff"] >= 0).all())

# 9. work_hours > 0
check("work_hours > 0", (df["work_hours"] > 0).all())

# 10. hourly_rate >= 1000
check("hourly_rate >= 1000", (df["hourly_rate"] >= 1000).all())

# 11. daily_wage >= 0
check("daily_wage >= 0", (df["daily_wage"] >= 0).all())

# 12. staffing_gap calculation (actual - required)
calc_gap = df["actual_staff"] - df["required_staff"]
check("staffing_gap計算整合性", (df["staffing_gap"] == calc_gap).all())

# 13. is_understaffed 0 or 1 only
check("is_understaffed 0/1のみ", set(df["is_understaffed"].unique()).issubset({0, 1}))

# 14. missing rate <= 15%
total_cells = df.shape[0] * df.shape[1]
missing_cells = df.isnull().sum().sum()
miss_rate = missing_cells / total_cells if total_cells > 0 else 1
check("欠損率 <= 15%", miss_rate <= 0.15)

# 15. source_file 3 varieties
check("source_file 3種類", set(df["source_file"].unique()) == EXPECTED_SOURCES)

# 16. understaffed count >= 1
check("不足シフト件数 >= 1", (df["is_understaffed"] == 1).sum() >= 1)

# 17. surplus count >= 1
check("余剰シフト件数 >= 1", (df["staffing_gap"] > 0).sum() >= 1)

# 18. labor_cost_flag kinds == 2
check("labor_cost_flag種類==2", len(df["labor_cost_flag"].unique()) == 2)

passed = sum(results)
total = len(results)
print(f"\nResult: {passed}/{total} checks passed")
if passed < total:
    raise SystemExit(1)
