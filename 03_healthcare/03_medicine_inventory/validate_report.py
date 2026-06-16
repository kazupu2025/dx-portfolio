# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
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
SUMMARY_CSV_PATH = OUTPUT_DIR / "medicine_summary_202401.csv"


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
    record("analysis_report.md 存在確認", report_exists, str(REPORT_PATH) if report_exists else "ファイルが見つかりません")

    # 2. medicine_summary_202401.csv 存在確認
    csv_exists = SUMMARY_CSV_PATH.exists()
    record("medicine_summary_202401.csv 存在確認", csv_exists, str(SUMMARY_CSV_PATH) if csv_exists else "ファイルが見つかりません")

    if not report_exists:
        print("[FAIL] レポートが存在しないため後続チェックをスキップします")
        sys.exit(1)

    report_text = REPORT_PATH.read_text(encoding="utf-8")

    # 3. レポートに「薬品」または「在庫」が含まれる
    has_keyword1 = "薬品" in report_text or "在庫" in report_text
    record("レポートに薬品または在庫を含む", has_keyword1,
           "含まれる" if has_keyword1 else "どちらも含まれない")

    # 4. レポートに「欠品」または「アラート」が含まれる
    has_keyword2 = "欠品" in report_text or "アラート" in report_text
    record("レポートに欠品またはアラートを含む", has_keyword2,
           "含まれる" if has_keyword2 else "どちらも含まれない")

    # 5. レポートにインサイト・まとめがある
    has_insight = "インサイト" in report_text or "まとめ" in report_text
    record("レポートにインサイトまたはまとめがある", has_insight,
           "含まれる" if has_insight else "含まれない")

    # 6. レポートに数値がある
    has_numbers = bool(re.search(r"\d+", report_text))
    record("レポートに数値がある", has_numbers,
           "数値あり" if has_numbers else "数値なし")

    # 7. medicine_summary_202401.csv の行数 >= 1
    if csv_exists:
        try:
            df_csv = pd.read_csv(SUMMARY_CSV_PATH, encoding="utf-8-sig")
            csv_rows = len(df_csv)
            record("medicine_summary_202401.csv 行数 >= 1", csv_rows >= 1, f"{csv_rows} 行")
        except Exception as e:
            record("medicine_summary_202401.csv 行数 >= 1", False, f"読み込みエラー: {e}")
    else:
        record("medicine_summary_202401.csv 行数 >= 1", False, "ファイルが存在しない")

    # 8. レポートに病棟別分析がある
    has_ward = "病棟" in report_text
    record("レポートに病棟別分析がある", has_ward,
           "含まれる" if has_ward else "含まれない")

    # 9. レポートにカテゴリ別分析がある
    has_category = "カテゴリ" in report_text
    record("レポートにカテゴリ別分析がある", has_category,
           "含まれる" if has_category else "含まれない")

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
