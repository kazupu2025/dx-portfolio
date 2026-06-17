# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
SUMMARY_CSV = os.path.join(OUTPUT_DIR, "property_summary_202401.csv")

results = []
total = 10


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    results.append((status, label))
    print("{} {}".format(status, label))


# 1. analysis_report.md exists
check("analysis_report.md が存在する", os.path.exists(REPORT_PATH))

# 2. property_summary_202401.csv exists
check("property_summary_202401.csv が存在する", os.path.exists(SUMMARY_CSV))

# 3. Report has content
if os.path.exists(REPORT_PATH):
    with open(REPORT_PATH, encoding="utf-8") as f:
        content = f.read()
    check("レポートに内容がある（100文字以上）", len(content) >= 100)
else:
    check("レポートに内容がある（100文字以上）", False)
    content = ""

# 4. Report contains property type section
check("物件タイプ別分析セクションが存在する", "物件タイプ" in content)

# 5. Report contains area section
check("エリア別分析セクションが存在する", "エリア" in content)

# 6. Report contains staff section
check("スタッフ別分析セクションが存在する", "スタッフ" in content)

# 7. Summary CSV has rows
if os.path.exists(SUMMARY_CSV):
    df = pd.read_csv(SUMMARY_CSV, encoding="utf-8-sig")
    check("サマリーCSVに1行以上ある", len(df) >= 1)
else:
    df = pd.DataFrame()
    check("サマリーCSVに1行以上ある", False)

# 8. Summary CSV has conversion rate column
if not df.empty:
    check("サマリーCSVに成約率列がある", "成約率" in df.columns)
else:
    check("サマリーCSVに成約率列がある", False)

# 9. Summary CSV has 4 property type rows
if not df.empty:
    check("サマリーCSVに4物件タイプ分の行がある", len(df) == 4)
else:
    check("サマリーCSVに4物件タイプ分の行がある", False)

# 10. Report has markdown table header
check("レポートにMarkdownテーブルが含まれる", "|" in content)

passed = sum(1 for s, _ in results if s == "[PASS]")
print("")
print("Result: {}/{} checks passed".format(passed, total))
