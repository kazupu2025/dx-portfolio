# -*- coding: utf-8 -*-
"""
C-40: アルバイトシフト管理・人件費集計パイプライン
分析レポートバリデーションスクリプト（8項目チェック）
"""

import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
STORE_CSV_FILE = OUTPUT_DIR / "store_summary_202401.csv"


def check(label: str, result: bool, detail: str = "") -> bool:
    status = "[PASS]" if result else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return result


def validate() -> bool:
    results = []

    # 1. レポートファイル存在確認
    report_exists = REPORT_FILE.exists()
    results.append(check("レポートファイル存在確認", report_exists, str(REPORT_FILE)))

    # 2. 店舗別サマリーCSV存在確認
    csv_exists = STORE_CSV_FILE.exists()
    results.append(check("店舗別サマリーCSV存在確認", csv_exists, str(STORE_CSV_FILE)))

    if report_exists:
        content = REPORT_FILE.read_text(encoding="utf-8")

        # 3. レポートが空でないこと
        results.append(check("レポートが空でない", len(content.strip()) > 100,
                              f"文字数: {len(content)}"))

        # 4. 必須セクションの存在（店舗別サマリー）
        has_store_section = "店舗別" in content
        results.append(check("店舗別サマリーセクションの存在", has_store_section))

        # 5. スタッフ別ランキングセクションの存在
        has_staff_section = "スタッフ別" in content
        results.append(check("スタッフ別ランキングセクションの存在", has_staff_section))

        # 6. insights・改善示唆セクションの存在
        has_insights = "Insights" in content or "改善示唆" in content
        results.append(check("Insights/改善示唆セクションの存在", has_insights))

        # 7. 数値が含まれる（人件費など）
        import re
        has_numbers = bool(re.search(r"\d{4,}", content))
        results.append(check("数値データが含まれる", has_numbers))

    else:
        # ファイルなしの場合3〜7をFAILに
        for _ in range(5):
            results.append(False)
            print("[FAIL] (レポートファイルが存在しないためスキップ)")

    if csv_exists:
        df = pd.read_csv(STORE_CSV_FILE, encoding="utf-8-sig")

        # 8. 店舗別サマリーが3行（3店舗）
        results.append(check("店舗別サマリーが 3 行", len(df) == 3,
                              f"実際: {len(df)} 行"))
    else:
        results.append(False)
        print("[FAIL] (店舗別サマリーCSVが存在しないためスキップ)")

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n結果: {passed}/{total} PASS")
    return passed == total


def main():
    print("=" * 60)
    print("分析レポートバリデーション (8 項目)")
    print("=" * 60)
    success = validate()
    print("=" * 60)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
