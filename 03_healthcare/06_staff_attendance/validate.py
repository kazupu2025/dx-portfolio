# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_attendance_202401.csv")

results = []


def check(label, passed):
    status = "[PASS]" if passed else "[FAIL]"
    print("{} {}".format(status, label))
    results.append(passed)


# 1. File exists
check("File exists", os.path.exists(CLEANED_FILE))

if not os.path.exists(CLEANED_FILE):
    total = len(results)
    passed = sum(results)
    print("Result: {}/{} checks passed".format(passed, total))
    raise SystemExit(1)

df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

# 2. Row count >= 420
check("Row count >= 420", len(df) >= 420)

# 3. Required columns present
REQUIRED_COLS = [
    "work_date", "record_id", "staff_type", "department", "staff_id",
    "scheduled_hours", "actual_hours", "is_absent", "absence_reason",
    "overtime_hours", "utilization_rate", "attendance_flag", "overtime_flag",
    "source_file"
]
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
check("Required columns present", len(missing_cols) == 0)

# 4. work_date format YYYY-MM-DD
import re
date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
valid_dates = df["work_date"].dropna().apply(lambda x: bool(date_pattern.match(str(x))))
check("work_date format YYYY-MM-DD", valid_dates.all())

# 5. record_id uniqueness
check("record_id is unique", df["record_id"].nunique() == len(df))

# 6. staff_type has 4 kinds
check("staff_type has 4 kinds", df["staff_type"].nunique() == 4)

# 7. department has 5 kinds
check("department has 5 kinds", df["department"].nunique() == 5)

# 8. scheduled_hours > 0
check("scheduled_hours > 0", (df["scheduled_hours"] > 0).all())

# 9. actual_hours >= 0
check("actual_hours >= 0", (df["actual_hours"] >= 0).all())

# 10. is_absent values are 0 or 1 only
check("is_absent values 0 or 1 only", df["is_absent"].isin([0, 1]).all())

# 11. utilization_rate >= 0
check("utilization_rate >= 0", (df["utilization_rate"] >= 0).all())

# 12. attendance_flag has 2 kinds ("出勤" / "欠勤")
att_flags = set(df["attendance_flag"].dropna().unique())
check("attendance_flag has 2 kinds", att_flags == {"出勤", "欠勤"})

# 13. overtime_flag has 2 kinds
ot_flags = set(df["overtime_flag"].dropna().unique())
check("overtime_flag has 2 kinds", ot_flags == {"残業あり", "残業なし"})

# 14. Missing rate <= 15% (excluding absence_reason)
OPTIONAL_COLS = ["absence_reason"]
check_cols = [c for c in REQUIRED_COLS if c not in OPTIONAL_COLS]
max_null_rate = df[check_cols].isnull().mean().max()
check("Missing rate <= 15% (excl. absence_reason)", max_null_rate <= 0.15)

# 15. source_file has 3 kinds
check("source_file has 3 kinds", df["source_file"].nunique() == 3)

# 16. Attendance records >= 1
check("Attendance records >= 1", (df["is_absent"] == 0).sum() >= 1)

# 17. Absent records >= 1
check("Absent records >= 1", (df["is_absent"] == 1).sum() >= 1)

# 18. Overtime records >= 1
check("Overtime records >= 1", (df["overtime_hours"] > 0).sum() >= 1)

total = len(results)
passed = sum(results)
print("Result: {}/{} checks passed".format(passed, total))
