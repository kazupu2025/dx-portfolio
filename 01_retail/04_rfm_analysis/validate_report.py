# -*- coding: utf-8 -*-
"""
validate_report.py
分析アウトプット（analysis_report.md / customer_rfm_202401.csv）を8項目以上でバリデーションする。
print文に絵文字・em-dash・円記号を使わない。[PASS]/[FAIL] を使う。
"""

import pandas as pd
import re
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
RFM_CSV = OUTPUT_DIR / "customer_rfm_202401.csv"


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return condition


def main():
    results = []

    # 1. analysis_report.md 存在確認
    report_exists = REPORT_FILE.exists()
    results.append(check("analysis_report.md 存在確認", report_exists, str(REPORT_FILE)))

    # 2. customer_rfm_202401.csv 存在確認
    csv_exists = RFM_CSV.exists()
    results.append(check("customer_rfm_202401.csv 存在確認", csv_exists, str(RFM_CSV)))

    if not report_exists:
        print("[FAIL] レポートが存在しないため以降のレポートチェックをスキップします")
    else:
        report_text = REPORT_FILE.read_text(encoding="utf-8")

        # 3. レポートに「RFM」または「顧客」含む
        has_rfm_or_customer = "RFM" in report_text or "顧客" in report_text
        results.append(check("レポートに 'RFM' または '顧客' を含む", has_rfm_or_customer))

        # 4. レポートに「セグメント」または「優良」含む
        has_segment = "セグメント" in report_text or "優良" in report_text
        results.append(check("レポートに 'セグメント' または '優良' を含む", has_segment))

        # 5. レポートにインサイト・まとめがある
        has_insight = "インサイト" in report_text or "まとめ" in report_text
        results.append(check("レポートにインサイト・まとめがある", has_insight))

        # 6. レポートに数値がある
        has_numbers = bool(re.search(r"\d+", report_text))
        results.append(check("レポートに数値がある", has_numbers))

        # 7. (CSV側) customer_rfm_202401.csvの行数 >= 50 - ここでもチェック
        if csv_exists:
            df = pd.read_csv(RFM_CSV, encoding="utf-8-sig")
            row_count = len(df)
            results.append(check("customer_rfm_202401.csv 行数 >= 50", row_count >= 50, f"実際={row_count}"))
        else:
            results.append(check("customer_rfm_202401.csv 行数 >= 50", False, "CSVなし"))

        # 8. レポートにRecency/Frequency/Monetary分析がある
        has_rfm_analysis = (
            "Recency" in report_text
            and "Frequency" in report_text
            and "Monetary" in report_text
        )
        results.append(check("レポートに Recency / Frequency / Monetary 分析がある", has_rfm_analysis))

        # 9. レポートに改善示唆がある
        has_suggestion = "改善示唆" in report_text or "改善" in report_text
        results.append(check("レポートに改善示唆がある", has_suggestion))

    # サマリー
    passed = sum(results)
    total = len(results)
    print()
    print(f"レポートバリデーション結果: {passed}/{total} 項目 PASS")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
