"""
C-19: validate_report.py
analysis_report.md と pnl_summary_202401.csv の 7 項目チェック
em-dash や絵文字は使用しない（Windows CP932 対応）
"""
import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
SUMMARY_FILE = os.path.join(BASE_DIR, "output", "pnl_summary_202401.csv")

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    return condition


def main():
    # 1. レポートファイル存在
    check("analysis_report.md 存在", os.path.isfile(REPORT_FILE))

    # 2. サマリーCSV存在
    check("pnl_summary_202401.csv 存在", os.path.isfile(SUMMARY_FILE))

    # 3〜7: レポート内容チェック
    if os.path.isfile(REPORT_FILE):
        with open(REPORT_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # 3. 「売上」を含む
        check("レポートに'売上'含む", "売上" in content)

        # 4. 「粗利」または「利益」含む
        check("レポートに'粗利'または'利益'含む", "粗利" in content or "利益" in content)

        # 5. インサイト含む（「インサイト」または「所見」）
        check("インサイト/所見セクション含む", "インサイト" in content or "所見" in content)

        # 6. 数値含む（円記号またはパーセント）
        import re
        has_number = bool(re.search(r"\d+[,\d]*\s*円|\d+\.\d+%|\d{2,}%", content))
        check("数値（円/パーセント）含む", has_number)

    else:
        check("レポートに'売上'含む", False, "file missing")
        check("レポートに'粗利'または'利益'含む", False, "file missing")
        check("インサイト/所見セクション含む", False, "file missing")
        check("数値（円/パーセント）含む", False, "file missing")

    # 7. サマリーCSV 行数 1 以上
    if os.path.isfile(SUMMARY_FILE):
        df = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
        check("pnl_summary 行数1以上", len(df) >= 1, f"rows={len(df)}")
    else:
        check("pnl_summary 行数1以上", False, "file missing")

    print(f"\n{'No':>3}  {'Check':<45}  {'Status':<6}  Detail")
    print("-" * 80)
    for i, (name, status, detail) in enumerate(results, 1):
        print(f"{i:>3}  {name:<45}  {status:<6}  {detail}")

    total = len(results)
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = total - passed

    print(f"\n[RESULT] {passed}/{total} PASS, {failed} FAIL")
    if failed > 0:
        sys.exit(1)
    else:
        print("[validate_report.py] All checks passed.")


if __name__ == "__main__":
    main()
