# -*- coding: utf-8 -*-
"""
分析レポートのバリデーションスクリプト
8項目以上のチェックを実施する
"""
import re
import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
ROUTE_SUMMARY_CSV = OUTPUT_DIR / "route_summary_202401.csv"


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "[PASS]" if passed else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return passed


def run_validation() -> bool:
    results = []

    # 1. analysis_report.md 存在確認
    report_exists = REPORT_MD.exists()
    results.append(check("01. analysis_report.md 存在確認", report_exists, str(REPORT_MD)))

    # 2. route_summary_202401.csv 存在確認
    csv_exists = ROUTE_SUMMARY_CSV.exists()
    results.append(check("02. route_summary_202401.csv 存在確認", csv_exists, str(ROUTE_SUMMARY_CSV)))

    report_text = ""
    if report_exists:
        report_text = REPORT_MD.read_text(encoding="utf-8")

    # 3. レポートに「ルート」または「配送」含む
    has_route_delivery = "ルート" in report_text or "配送" in report_text
    results.append(check("03. レポートに「ルート」または「配送」含む", has_route_delivery))

    # 4. レポートに「効率」または「コスト」含む
    has_efficiency_cost = "効率" in report_text or "コスト" in report_text
    results.append(check("04. レポートに「効率」または「コスト」含む", has_efficiency_cost))

    # 5. レポートにインサイト・まとめがある
    has_insights = "インサイト" in report_text or "まとめ" in report_text
    results.append(check("05. レポートにインサイト・まとめがある", has_insights))

    # 6. レポートに数値がある
    has_numbers = bool(re.search(r"\d+", report_text))
    results.append(check("06. レポートに数値がある", has_numbers))

    # 7. route_summary_202401.csvの行数 >= 1
    if csv_exists:
        try:
            df = pd.read_csv(ROUTE_SUMMARY_CSV, encoding="utf-8-sig")
            row_count = len(df)
            results.append(check("07. route_summary_202401.csvの行数 >= 1", row_count >= 1, f"行数={row_count}"))
        except Exception as e:
            results.append(check("07. route_summary_202401.csvの行数 >= 1", False, str(e)))
    else:
        results.append(check("07. route_summary_202401.csvの行数 >= 1", False, "CSVファイルなし"))

    # 8. レポートにエリア別分析がある
    has_area = "エリア" in report_text
    results.append(check("08. レポートにエリア別分析がある", has_area))

    # 9. レポートに遅延分析がある
    has_delay = "遅延" in report_text
    results.append(check("09. レポートに遅延分析がある", has_delay))

    # サマリー
    pass_count = sum(results)
    total_count = len(results)
    print(f"\n[SUMMARY] {pass_count}/{total_count} チェック通過")

    all_passed = all(results)
    if all_passed:
        print("[VALIDATE] 全チェック通過")
    else:
        print("[VALIDATE] 一部チェック失敗")
    return all_passed


if __name__ == "__main__":
    ok = run_validation()
    sys.exit(0 if ok else 1)
