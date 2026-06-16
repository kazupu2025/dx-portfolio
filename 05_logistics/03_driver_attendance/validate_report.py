"""
C-22 ドライバー勤怠・拘束時間管理パイプライン
レポートバリデーション（7項目以上）
"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "driver_summary_202401.csv"


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

    # 01 analysis_report.md の存在
    report_exists = REPORT_PATH.exists()
    results.append(check("01 analysis_report.mdの存在", report_exists, str(REPORT_PATH)))

    # 02 driver_summary_202401.csv の存在
    csv_exists = CSV_PATH.exists()
    results.append(check("02 driver_summary_202401.csvの存在", csv_exists, str(CSV_PATH)))

    if not report_exists:
        print("\n[ERROR] レポートファイルが存在しません。analyze.py を実行してください。")
        sys.exit(1)

    report_text = REPORT_PATH.read_text(encoding="utf-8")

    # 03 「拘束」が含まれる
    has_confinement = "拘束" in report_text
    results.append(check("03 レポートに「拘束」が含まれる", has_confinement))

    # 04 「違反」が含まれる
    has_violation = "違反" in report_text
    results.append(check("04 レポートに「違反」が含まれる", has_violation))

    # 05 インサイト・改善提案が含まれる
    has_insight = "インサイト" in report_text or "改善" in report_text or "提案" in report_text
    results.append(check("05 レポートにインサイト・改善提案が含まれる", has_insight))

    # 06 数値が含まれる
    has_numbers = bool(re.search(r"\d{2,}", report_text))
    results.append(check("06 レポートに数値が含まれる", has_numbers))

    # 07 CSV の行数 >= 1
    if csv_exists:
        try:
            df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
            csv_rows = len(df)
        except Exception:
            csv_rows = 0
        results.append(check("07 driver_summary_202401.csvの行数 >= 1", csv_rows >= 1,
                             f"{csv_rows} rows"))
    else:
        results.append(check("07 driver_summary_202401.csvの行数", False, "ファイルなし"))

    # 08 「営業所」が含まれる
    has_office = "営業所" in report_text
    results.append(check("08 レポートに「営業所」が含まれる", has_office))

    # 09 「運行区分」または「長距離」「中距離」「市内」が含まれる
    has_op = "運行区分" in report_text or "長距離" in report_text or "市内" in report_text
    results.append(check("09 レポートに運行区分情報が含まれる", has_op))

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
