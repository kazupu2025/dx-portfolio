# -*- coding: utf-8 -*-
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
DEPT_CSV_PATH = os.path.join(OUTPUT_DIR, "dept_summary_202401.csv")

checks = []


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    checks.append((label, status))
    print("{} {}".format(status, label))


# 1. analysis_report.md exists
check("analysis_report.md exists", os.path.exists(REPORT_PATH))

# 2. dept_summary_202401.csv exists
check("dept_summary_202401.csv exists", os.path.exists(DEPT_CSV_PATH))

if os.path.exists(REPORT_PATH):
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 3. Report contains Overview section
    check("Report contains Overview section", "## 1. Overview" in content)

    # 4. Report contains By Department section
    check("Report contains By Department section", "## 2. By Department" in content)

    # 5. Report contains By Insurance Type section
    check("Report contains By Insurance Type section", "## 3. By Insurance Type" in content)

    # 6. Report contains Daily Revenue Trend section
    check("Report contains Daily Revenue Trend section", "## 4. Daily Revenue Trend" in content)

    # 7. Report mentions total records
    check("Report mentions Total records", "Total records" in content)

    # 8. Report mentions total claim amount
    check("Report mentions Total claim amount", "Total claim amount" in content)

    # 9. Report mentions reduction rate
    check("Report mentions reduction rate", "reduction rate" in content)
else:
    for lbl in ["Overview section", "By Department section", "By Insurance Type section",
                "Daily Revenue Trend section", "Total records", "Total claim amount", "reduction rate"]:
        check("Report contains " + lbl, False)

if os.path.exists(DEPT_CSV_PATH):
    import pandas as pd
    dept_df = pd.read_csv(DEPT_CSV_PATH, encoding="utf-8-sig")
    # 10. Dept summary has 5 rows
    check("Dept summary has 5 rows", len(dept_df) == 5)
else:
    check("Dept summary has 5 rows", False)

passed = sum(1 for _, s in checks if s == "[PASS]")
total = len(checks)
print("")
print("Result: {}/{} checks passed".format(passed, total))

if passed < total:
    sys.exit(1)
