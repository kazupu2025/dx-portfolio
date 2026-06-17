# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
レポートバリデーションスクリプト: 8 項目以上のチェックを実施する
絵文字・em-dash・記号は使わず [PASS]/[FAIL] で出力する
"""

import re
import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV_PATH = OUTPUT_DIR / "dept_summary_202401.csv"


def main():
    print("=" * 60)
    print("レポートバリデーション開始")
    print("=" * 60)

    fail_count = 0
    pass_count = 0

    def record(name: str, passed: bool, detail: str = ""):
        nonlocal fail_count, pass_count
        tag = "[PASS]" if passed else "[FAIL]"
        suffix = f" -- {detail}" if detail else ""
        print(f"{tag} {name}{suffix}")
        if passed:
            pass_count += 1
        else:
            fail_count += 1

    # 1. analysis_report.md 存在確認
    report_exists = REPORT_PATH.exists()
    record("analysis_report.md 存在確認", report_exists,
           str(REPORT_PATH) if report_exists else "ファイルが見つかりません")

    # 2. dept_summary_202401.csv 存在確認
    csv_exists = SUMMARY_CSV_PATH.exists()
    record("dept_summary_202401.csv 存在確認", csv_exists,
           str(SUMMARY_CSV_PATH) if csv_exists else "ファイルが見つかりません")

    if not report_exists:
        print("[FAIL] レポートが存在しないため後続チェックをスキップします")
        sys.exit(1)

    report_text = REPORT_PATH.read_text(encoding="utf-8")

    # 3. レポートに「来院」または「受付」が含まれる
    has_keyword1 = "来院" in report_text or "受付" in report_text
    record("レポートに来院または受付を含む", has_keyword1,
           "含まれる" if has_keyword1 else "どちらも含まれない")

    # 4. レポートに「待ち時間」または「長待ち」が含まれる
    has_keyword2 = "待ち時間" in report_text or "長待ち" in report_text
    record("レポートに待ち時間または長待ちを含む", has_keyword2,
           "含まれる" if has_keyword2 else "どちらも含まれない")

    # 5. レポートにインサイト・まとめがある
    has_insight = "インサイト" in report_text or "まとめ" in report_text
    record("レポートにインサイトまたはまとめがある", has_insight,
           "含まれる" if has_insight else "含まれない")

    # 6. レポートに数値がある
    has_numbers = bool(re.search(r"\d+", report_text))
    record("レポートに数値がある", has_numbers,
           "数値あり" if has_numbers else "数値なし")

    # 7. dept_summary_202401.csv の行数 >= 1
    if csv_exists:
        try:
            df_csv = pd.read_csv(SUMMARY_CSV_PATH, encoding="utf-8-sig")
            csv_rows = len(df_csv)
            record("dept_summary_202401.csv 行数 >= 1", csv_rows >= 1, f"{csv_rows} 行")
        except Exception as e:
            record("dept_summary_202401.csv 行数 >= 1", False, f"読み込みエラー: {e}")
    else:
        record("dept_summary_202401.csv 行数 >= 1", False, "ファイルが存在しない")

    # 8. レポートに診療科別分析がある
    has_dept = "診療科" in report_text
    record("レポートに診療科別分析がある", has_dept,
           "含まれる" if has_dept else "含まれない")

    # 9. レポートに時間帯分析がある
    has_timeslot = "時間帯" in report_text or "ピーク" in report_text
    record("レポートに時間帯またはピークの分析がある", has_timeslot,
           "含まれる" if has_timeslot else "含まれない")

    # 10. レポートのサイズが十分（500文字以上）
    report_len = len(report_text)
    has_enough_content = report_len >= 500
    record("レポートが 500 文字以上", has_enough_content, f"{report_len} 文字")

    print("=" * 60)
    total = pass_count + fail_count
    print(f"結果: {pass_count}/{total} PASS, {fail_count} FAIL")
    if fail_count > 0:
        sys.exit(1)
    print("全チェック PASS")


if __name__ == "__main__":
    main()
