# -*- coding: utf-8 -*-
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
PLAN_SUMMARY_FILE = os.path.join(OUTPUT_DIR, "plan_summary_202401.csv")

results = []


def check(label, passed):
    mark = "[PASS]" if passed else "[FAIL]"
    print(f"{mark} {label}")
    results.append(passed)


def main():
    # Check 1: analysis_report.md exists
    check("analysis_report.md 存在", os.path.exists(REPORT_FILE))

    # Check 2: plan_summary_202401.csv exists
    check("plan_summary_202401.csv 存在", os.path.exists(PLAN_SUMMARY_FILE))

    # Check 3: report contains plan section
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, encoding="utf-8") as f:
            content = f.read()
        check("レポートにプラン別分析セクションあり", "プラン別分析" in content)
        check("レポートに業種別分析セクションあり", "業種別分析" in content)
        check("レポートにコホート分析セクションあり", "コホート分析" in content)
        check("レポートに全体解約率の記載あり", "全体解約率" in content)
        check("レポートにLTVの記載あり", "LTV" in content)
    else:
        for _ in range(5):
            check("(skip - report not found)", False)

    # Check 6-10: plan_summary CSV checks
    if os.path.exists(PLAN_SUMMARY_FILE):
        df = pd.read_csv(PLAN_SUMMARY_FILE, encoding="utf-8-sig")
        check(f"plan_summary 行数==3 (実際: {len(df)})", len(df) == 3)
        check("churn_rate列あり", "churn_rate" in df.columns)
        check("avg_ltv列あり", "avg_ltv" in df.columns)
        check("avg_login列あり", "avg_login" in df.columns)
        check("churn_rate値が0-1の範囲", df["churn_rate"].between(0, 1).all())
    else:
        for _ in range(5):
            check("(skip - plan_summary not found)", False)

    passed = sum(results)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")


if __name__ == "__main__":
    main()
