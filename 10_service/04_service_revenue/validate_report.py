# -*- coding: utf-8 -*-
"""
C-45: サービス別売上・原価レポート
分析レポートバリデーション (10項目)
"""

import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

MD_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
CSV_FILE = os.path.join(OUTPUT_DIR, "service_summary_202401.csv")
JSON_FILE = os.path.join(OUTPUT_DIR, "result_analysis.json")


def check(label: str, cond: bool) -> bool:
    status = "[PASS]" if cond else "[FAIL]"
    print(f"  {status} {label}")
    return cond


def main():
    results = []

    # 1. analysis_report.md 存在
    results.append(check("analysis_report.md が存在する", os.path.exists(MD_FILE)))

    # 2. service_summary_202401.csv 存在
    results.append(check("service_summary_202401.csv が存在する", os.path.exists(CSV_FILE)))

    # 3. result_analysis.json 存在
    results.append(check("result_analysis.json が存在する", os.path.exists(JSON_FILE)))

    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")

        # 4. サービス数 == 8
        results.append(check(f"サービス数 == 8 (実際: {len(df)})", len(df) == 8))

        # 5. revenue_total 列が存在し正値
        rev_ok = "revenue_total" in df.columns and (df["revenue_total"] > 0).all()
        results.append(check("revenue_total 列が存在し全行正値", rev_ok))

        # 6. gross_profit_total 列が存在
        results.append(check("gross_profit_total 列が存在する", "gross_profit_total" in df.columns))

        # 7. gross_margin_mean 列が存在し [-1, 1] 範囲内
        if "gross_margin_mean" in df.columns:
            gm_ok = ((df["gross_margin_mean"] >= -1) & (df["gross_margin_mean"] <= 1)).all()
        else:
            gm_ok = False
        results.append(check("gross_margin_mean が [-1, 1] 範囲内", gm_ok))

        # 8. revenue_rank 列が存在
        results.append(check("revenue_rank 列が存在する", "revenue_rank" in df.columns))
    else:
        results.extend([check(f"CSV check {i} (ファイル不在によりスキップ)", False) for i in range(4, 9)])

    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, encoding="utf-8") as f:
            j = json.load(f)

        # 9. total_revenue > 0
        results.append(check(f"total_revenue > 0 (実際: {j.get('total_revenue')})", j.get("total_revenue", 0) > 0))

        # 10. service_count == 8
        results.append(check(f"service_count == 8 (実際: {j.get('service_count')})", j.get("service_count") == 8))
    else:
        results.extend([check(f"JSON check {i} (ファイル不在によりスキップ)", False) for i in range(9, 11)])

    passed = sum(results)
    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")


if __name__ == "__main__":
    main()
