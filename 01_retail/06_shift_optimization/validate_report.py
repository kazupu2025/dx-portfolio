# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "store_summary_202401.csv")

results = []


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {label}")
    results.append(condition)


# 1. analysis_report.md exists
check("analysis_report.md 存在", os.path.exists(REPORT_PATH))

# 2. store_summary_202401.csv exists
check("store_summary_202401.csv 存在", os.path.exists(SUMMARY_PATH))

if not os.path.exists(REPORT_PATH) or not os.path.exists(SUMMARY_PATH):
    print("Result: 0/10 checks passed")
    raise SystemExit(1)

with open(REPORT_PATH, "r", encoding="utf-8") as f:
    report_text = f.read()

df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")

# 3. Report contains heading
check("レポートにタイトル行あり", "シフト充足率" in report_text)

# 4. Report contains store section
check("レポートに店舗別セクションあり", "店舗別" in report_text)

# 5. Report contains role section
check("レポートに役割別セクションあり", "役割別" in report_text)

# 6. Report contains daily trend section
check("レポートに日別トレンドセクションあり", "日別" in report_text)

# 7. Store summary has required columns
required_cols = {"store_name", "total_labor_cost", "avg_fill_rate", "understaffed_count"}
check("store_summary必須列の存在", required_cols.issubset(set(df.columns)))

# 8. Store summary has 5 stores
check("store_summaryに5店舗", len(df) == 5)

# 9. total_labor_cost values are positive
check("total_labor_cost > 0", (df["total_labor_cost"] > 0).all())

# 10. avg_fill_rate values are between 0 and some reasonable value
check("avg_fill_rate >= 0", (df["avg_fill_rate"] >= 0).all())

passed = sum(results)
total = len(results)
print(f"\nResult: {passed}/{total} checks passed")
if passed < total:
    raise SystemExit(1)
