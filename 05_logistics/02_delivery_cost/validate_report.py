"""
C-17 配送コスト分析パイプライン
レポートバリデーション（7項目以上）
"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "cost_analysis_202401.csv"


def check(name: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return passed


def main():
    results = []
    print("=" * 60)
    print("validate_report.py: 分析レポートチェック")
    print("=" * 60)

    # 1. analysis_report.mdの存在
    report_exists = REPORT_PATH.exists()
    results.append(check("01 analysis_report.mdの存在", report_exists, str(REPORT_PATH)))

    # 2. cost_analysis_202401.csvの存在
    csv_exists = CSV_PATH.exists()
    results.append(check("02 cost_analysis_202401.csvの存在", csv_exists, str(CSV_PATH)))

    if not report_exists:
        print("\n[ERROR] レポートファイルが存在しません。analyze.py を実行してください。")
        sys.exit(1)

    report_text = REPORT_PATH.read_text(encoding="utf-8")

    # 3. レポートに「ルート」が含まれる
    has_route = "ルート" in report_text
    results.append(check("03 レポートに「ルート」が含まれる", has_route))

    # 4. レポートに「コスト」が含まれる
    has_cost = "コスト" in report_text
    results.append(check("04 レポートに「コスト」が含まれる", has_cost))

    # 5. レポートにインサイト・提案が含まれる
    has_insight = "インサイト" in report_text or "提案" in report_text or "改善" in report_text
    results.append(check("05 レポートにインサイト・改善提案が含まれる", has_insight))

    # 6. cost_analysis_202401.csvの行数（1以上）
    if csv_exists:
        try:
            df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
            csv_rows = len(df)
        except Exception as e:
            csv_rows = 0
        results.append(check("06 cost_analysis_202401.csvの行数 >= 1", csv_rows >= 1, f"{csv_rows} rows"))
    else:
        results.append(check("06 cost_analysis_202401.csvの行数", False, "ファイルなし"))

    # 7. レポートに数値（金額）が含まれる
    has_numbers = bool(re.search(r"[¥￥]\d[\d,]*", report_text) or re.search(r"\d{4,}", report_text))
    results.append(check("07 レポートに数値（金額）が含まれる", has_numbers))

    # 8. レポートに車種が含まれる
    has_vehicle = "車種" in report_text or "トラック" in report_text or "軽バン" in report_text
    results.append(check("08 レポートに車種情報が含まれる", has_vehicle))

    # 9. レポートに月間コスト情報が含まれる
    has_monthly = "月間" in report_text or "2024年1月" in report_text
    results.append(check("09 レポートに月間コスト情報が含まれる", has_monthly))

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\n結果: {passed}/{total} PASS")

    if passed == total:
        print("[SUCCESS] 全チェックPASS")
        sys.exit(0)
    else:
        print(f"[FAIL] {total - passed}項目が失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
