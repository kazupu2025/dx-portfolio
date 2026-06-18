# -*- coding: utf-8 -*-
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
STAFF_CSV_FILE = os.path.join(OUTPUT_DIR, "staff_summary_202401.csv")
RESULT_JSON_FILE = os.path.join(OUTPUT_DIR, "result_analysis.json")

results = []


def check(label, passed):
    status = "[PASS]" if passed else "[FAIL]"
    print("{} {}".format(status, label))
    results.append(passed)


# 1. analysis_report.md exists
check("analysis_report.md exists", os.path.exists(REPORT_FILE))

# 2. staff_summary_202401.csv exists
check("staff_summary_202401.csv exists", os.path.exists(STAFF_CSV_FILE))

# 3. result_analysis.json exists
check("result_analysis.json exists", os.path.exists(RESULT_JSON_FILE))

# 4. Report contains staff type section
if os.path.exists(REPORT_FILE):
    with open(REPORT_FILE, encoding="utf-8") as f:
        content = f.read()
    check("Report contains staff type section", "スタッフ種別" in content)
else:
    check("Report contains staff type section", False)
    content = ""

# 5. Report contains department section
check("Report contains department section", "診療科" in content)

# 6. Report contains KPI values
check("Report contains attendance rate", "出勤率" in content)

# 7. Staff summary CSV has required columns
if os.path.exists(STAFF_CSV_FILE):
    import pandas as pd
    df = pd.read_csv(STAFF_CSV_FILE, encoding="utf-8-sig")
    required_cols = ["staff_type", "total_records", "absent_count", "avg_overtime_hours",
                     "avg_utilization_rate", "attendance_rate"]
    check("Staff summary CSV has required columns", all(c in df.columns for c in required_cols))
    check("Staff summary has 4 rows (4 staff types)", len(df) == 4)
else:
    check("Staff summary CSV has required columns", False)
    check("Staff summary has 4 rows (4 staff types)", False)

# 9. result_analysis.json has required keys
if os.path.exists(RESULT_JSON_FILE):
    with open(RESULT_JSON_FILE, encoding="utf-8") as f:
        result = json.load(f)
    required_keys = [
        "total_records", "attendance_count", "absent_count",
        "overall_attendance_rate", "avg_utilization_rate",
        "avg_overtime_hours", "overtime_count"
    ]
    check("result_analysis.json has required keys", all(k in result for k in required_keys))
    check("total_records >= 420", result.get("total_records", 0) >= 420)
else:
    check("result_analysis.json has required keys", False)
    check("total_records >= 420", False)

total = len(results)
passed = sum(results)
print("Result: {}/{} checks passed".format(passed, total))
