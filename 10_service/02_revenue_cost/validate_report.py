"""
C-21: レポートバリデーション (7項目)
全PASS必須。Windows CP932エラー回避のためASCII文字のみ使用。
"""
import sys
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV = OUTPUT_DIR / "service_summary_202401.csv"

results = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" : {detail}"
    results.append((name, cond, detail))
    print(msg)


def main():
    print("=== validate_report.py (7 checks) ===\n")

    # [1] レポート存在確認
    check("01_report_exists", REPORT_PATH.exists(), str(REPORT_PATH))

    # [2] サマリーCSV存在確認
    check("02_summary_csv_exists", SUMMARY_CSV.exists(), str(SUMMARY_CSV))

    report_text = ""
    if REPORT_PATH.exists():
        report_text = REPORT_PATH.read_text(encoding="utf-8")

    # [3] 「粗利」または「利益」含有
    has_profit = "粗利" in report_text or "利益" in report_text
    check("03_contains_profit_keyword", has_profit)

    # [4] 「サービス」含有
    has_service = "サービス" in report_text
    check("04_contains_service_keyword", has_service)

    # [5] インサイト含有（「インサイト」または「考察」）
    has_insight = "インサイト" in report_text or "考察" in report_text
    check("05_contains_insight_section", has_insight)

    # [6] 数値含有（円マーク または 数字）
    import re
    has_numbers = bool(re.search(r"[0-9]", report_text)) or "¥" in report_text
    check("06_contains_numbers", has_numbers)

    # [7] サマリーCSV行数 1以上
    if SUMMARY_CSV.exists():
        import csv
        with open(SUMMARY_CSV, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        # ヘッダー除いて1行以上
        data_rows = len(rows) - 1 if len(rows) > 0 else 0
        check("07_summary_csv_rows_ge_1", data_rows >= 1, f"data_rows={data_rows}")
    else:
        check("07_summary_csv_rows_ge_1", False, "CSV not found")

    # 結果サマリー
    print(f"\n=== 結果サマリー ===")
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"PASS: {passed} / {len(results)}")
    print(f"FAIL: {failed} / {len(results)}")

    if failed > 0:
        print("\n--- FAIL一覧 ---")
        for name, ok, detail in results:
            if not ok:
                print(f"  FAIL {name} : {detail}")
        sys.exit(1)
    else:
        print("\n全チェックPASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
