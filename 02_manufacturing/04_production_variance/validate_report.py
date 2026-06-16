# -*- coding: utf-8 -*-
"""
C-25: 生産計画 vs 実績 差異分析パイプライン
レポートバリデーション（8項目チェック）
"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
LINE_SUMMARY_CSV = OUTPUT_DIR / "line_summary_202401.csv"

NUMBER_PATTERN = re.compile(r"\d{3,}")


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return condition


def validate_report() -> bool:
    results = []

    # 1. analysis_report.md 存在確認
    results.append(check("analysis_report.md 存在確認", REPORT_MD.exists(), str(REPORT_MD)))

    # 2. line_summary_202401.csv 存在確認
    results.append(check("line_summary_202401.csv 存在確認", LINE_SUMMARY_CSV.exists(), str(LINE_SUMMARY_CSV)))

    if not REPORT_MD.exists():
        print("[FAIL] レポートが存在しないため、以降のチェックをスキップします。")
        return False

    report_text = REPORT_MD.read_text(encoding="utf-8")

    # 3. レポートに「計画」含む
    results.append(check('レポートに「計画」含む', "計画" in report_text))

    # 4. レポートに「達成」または「実績」含む
    results.append(check('レポートに「達成」または「実績」含む',
                          "達成" in report_text or "実績" in report_text))

    # 5. レポートにインサイト・まとめがある
    has_insight = "インサイト" in report_text or "まとめ" in report_text or "改善示唆" in report_text
    results.append(check("レポートにインサイト・まとめがある", has_insight))

    # 6. レポートに数値（3桁以上の数字）がある
    has_numbers = bool(NUMBER_PATTERN.search(report_text))
    results.append(check("レポートに3桁以上の数値がある", has_numbers))

    if LINE_SUMMARY_CSV.exists():
        # 7. line_summary_202401.csvの行数 >= 1
        try:
            df = pd.read_csv(LINE_SUMMARY_CSV, encoding="utf-8-sig")
            results.append(check("line_summary行数 >= 1", len(df) >= 1, f"actual={len(df)}"))
        except Exception as e:
            results.append(check("line_summary行数 >= 1", False, str(e)))
    else:
        results.append(check("line_summary行数 >= 1", False, "ファイルなし"))

    # 8. レポートにライン別分析がある
    has_line_analysis = "ライン別" in report_text or "LINE-" in report_text
    results.append(check("レポートにライン別分析がある", has_line_analysis))

    # 9. レポートに不良率分析がある
    has_defect_analysis = "不良率" in report_text or "不良" in report_text
    results.append(check("レポートに不良率分析がある", has_defect_analysis))

    passed = sum(results)
    total = len(results)
    print(f"\n[RESULT] {passed}/{total} checks passed")
    return passed == total


if __name__ == "__main__":
    ok = validate_report()
    sys.exit(0 if ok else 1)
