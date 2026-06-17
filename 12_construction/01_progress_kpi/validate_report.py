# -*- coding: utf-8 -*-
import os
import pandas as pd

passed = 0
total = 10

def check(label, condition):
    global passed
    result = "[PASS]" if condition else "[FAIL]"
    if condition:
        passed += 1
    print(f"{result} {label}")

# 1. analysis_report.md exists
check("analysis_report.md 存在", os.path.exists("output/analysis_report.md"))

# 2. site_summary CSV exists
check("site_summary_202401.csv 存在", os.path.exists("output/site_summary_202401.csv"))

# 3. report has content
try:
    with open("output/analysis_report.md", encoding="utf-8") as f:
        content = f.read()
    check("レポート文字数>100", len(content) > 100)
except Exception:
    check("レポート文字数>100", False)

# 4. report contains site section
check("レポートに現場別セクション", "現場別" in content)

# 5. report contains process section
check("レポートに工程別セクション", "工程別" in content)

# 6. report contains worker section
check("レポートに作業員別セクション", "作業員別" in content)

# 7. site_summary has rows
try:
    ss = pd.read_csv("output/site_summary_202401.csv", encoding="utf-8-sig")
    check("site_summary 行数>=5", len(ss) >= 5)
    check("site_summary avg_progress 列あり", "avg_progress" in ss.columns)
    check("site_summary total_defects 列あり", "total_defects" in ss.columns)
    check("site_summary delayed_count 列あり", "delayed_count" in ss.columns)
except Exception:
    check("site_summary 行数>=5", False)
    check("site_summary avg_progress 列あり", False)
    check("site_summary total_defects 列あり", False)
    check("site_summary delayed_count 列あり", False)

print(f"\nResult: {passed}/{total} checks passed")
