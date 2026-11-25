# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
分析レポートのバリデーション（10項目チェック）
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
DEPT_SUMMARY_FILE = os.path.join(OUTPUT_DIR, "dept_summary_202401.csv")


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {label}")
    return condition


def main():
    results = []

    # 1. analysis_report.md が存在する
    results.append(check("analysis_report.md が存在する", os.path.exists(REPORT_FILE)))

    # 2. dept_summary_202401.csv が存在する
    results.append(check("dept_summary_202401.csv が存在する", os.path.exists(DEPT_SUMMARY_FILE)))

    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, encoding="utf-8") as f:
            content = f.read()

        # 3. レポートに KPI セクションがある
        results.append(check("レポートに KPIサマリー セクションが含まれる", "KPIサマリー" in content))

        # 4. レポートに学科別分析がある
        results.append(check("レポートに 学科別 セクションが含まれる", "学科別" in content))

        # 5. レポートに選考方法別分析がある
        results.append(check("レポートに 選考方法別 セクションが含まれる", "選考方法別" in content))

        # 6. レポートに地域別分析がある
        results.append(check("レポートに 地域別 セクションが含まれる", "地域別" in content))

        # 7. レポートに合格率が記載されている
        results.append(check("レポートに 合格率 が記載されている", "合格率" in content))
    else:
        for _ in range(5):
            results.append(False)
            print("[FAIL] analysis_report.md が存在しないためスキップ")

    if os.path.exists(DEPT_SUMMARY_FILE):
        df = pd.read_csv(DEPT_SUMMARY_FILE, encoding="utf-8-sig")

        # 8. dept_summary に 4 行（4学科）ある
        results.append(check(f"dept_summary に4行ある (実際: {len(df)})", len(df) == 4))

        # 9. dept_summary に合格率列がある
        has_rate_col = any("合格率" in str(c) for c in df.columns)
        results.append(check("dept_summary に合格率列がある", has_rate_col))

        # 10. dept_summary に平均点列がある
        has_avg_col = any("平均点" in str(c) for c in df.columns)
        results.append(check("dept_summary に平均点列がある", has_avg_col))
    else:
        for _ in range(3):
            results.append(False)
            print("[FAIL] dept_summary_202401.csv が存在しないためスキップ")

    total = len(results)
    passed = sum(results)
    print(f"\nResult: {passed}/{total} checks passed")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
