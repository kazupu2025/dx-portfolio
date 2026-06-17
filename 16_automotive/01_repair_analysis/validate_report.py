# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
SHOP_CSV_PATH = os.path.join(OUTPUT_DIR, "shop_summary_202401.csv")

results = []

def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    results.append((status, label))
    print(f"{status} {label}")

def main():
    # 1. Report file exists
    check("analysis_report.md exists", os.path.exists(REPORT_PATH))

    # 2. shop_summary_202401.csv exists
    check("shop_summary_202401.csv exists", os.path.exists(SHOP_CSV_PATH))

    if os.path.exists(REPORT_PATH):
        content = open(REPORT_PATH, encoding="utf-8").read()

        # 3. Report contains shop analysis section
        check("Report contains shop analysis", "店舗別" in content)

        # 4. Report contains work type section
        check("Report contains work type analysis", "作業区分" in content)

        # 5. Report contains tech analysis
        check("Report contains tech analysis", "技術者" in content)

        # 6. Report contains KPI section
        check("Report contains KPI section", "全体KPI" in content or "完了率" in content)

        # 7. Report contains total revenue data
        check("Report contains revenue data", "売上" in content)

    if os.path.exists(SHOP_CSV_PATH):
        df = pd.read_csv(SHOP_CSV_PATH, encoding="utf-8-sig")

        # 8. shop_summary has 3 rows (3 shops)
        check("shop_summary has 3 rows", len(df) == 3)

        # 9. shop_summary has revenue column
        check("shop_summary has revenue column", "売上合計" in df.columns)

        # 10. shop_summary revenue > 0
        check("shop_summary revenue values > 0", (df["売上合計"] > 0).all())

    passed = sum(1 for s, _ in results if s == "[PASS]")
    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")

if __name__ == "__main__":
    main()
