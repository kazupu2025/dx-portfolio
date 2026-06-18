# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
分析レポートバリデーションスクリプト (10項目)
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
CAT_CSV_PATH = os.path.join(OUTPUT_DIR, "category_summary_202401.csv")

EXPECTED_CATEGORIES = {"ログイン障害", "機能不具合", "請求問い合わせ", "使い方質問", "データ移行"}
EXPECTED_PRIORITIES = {"高", "中", "低"}


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {label}")
    return condition


def main():
    results = []

    # 1. analysis_report.md が存在する
    results.append(check("analysis_report.mdが存在する", os.path.exists(REPORT_PATH)))

    # 2. category_summary_202401.csv が存在する
    results.append(check("category_summary_202401.csvが存在する", os.path.exists(CAT_CSV_PATH)))

    # レポートの内容チェック
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # 3. レポートに「全体サマリー」セクションがある
        results.append(check("全体サマリーセクションが存在する", "全体サマリー" in content))

        # 4. レポートにカテゴリ別分析がある
        results.append(check("カテゴリ別分析セクションが存在する", "カテゴリ別分析" in content))

        # 5. レポートに優先度別分析がある
        results.append(check("優先度別分析セクションが存在する", "優先度別分析" in content))

        # 6. レポートに担当者別分析がある
        results.append(check("担当者別分析セクションが存在する", "担当者別分析" in content))

        # 7. レポートに解決率が記載されている
        results.append(check("解決率が記載されている", "解決率" in content))
    else:
        results.extend([check(f"スキップ(ファイル不存在): チェック{i}", False) for i in range(3, 8)])

    # CSVの内容チェック
    if os.path.exists(CAT_CSV_PATH):
        cat_df = pd.read_csv(CAT_CSV_PATH, encoding="utf-8-sig")

        # 8. カテゴリサマリーCSVに5カテゴリ含まれる
        actual_cats = set(cat_df["category"].unique())
        results.append(check(
            f"カテゴリサマリーに5カテゴリ含まれる (実際: {actual_cats})",
            EXPECTED_CATEGORIES <= actual_cats
        ))

        # 9. カテゴリサマリーに必須列が存在する
        required = {"category", "count", "resolve_rate", "avg_resolution_hours", "avg_satisfaction"}
        missing = required - set(cat_df.columns)
        results.append(check(f"カテゴリサマリーに必須列が存在する (不足: {missing})", len(missing) == 0))

        # 10. カテゴリサマリーの件数合計が420以上
        total_count = cat_df["count"].sum() if "count" in cat_df.columns else 0
        results.append(check(f"カテゴリサマリーの件数合計が420以上 (実際: {total_count})", total_count >= 420))
    else:
        results.extend([check(f"スキップ(ファイル不存在): CSVチェック{i}", False) for i in range(8, 11)])

    total = len(results)
    passed = sum(results)
    print(f"\n[結果] {passed}/{total} PASS")
    if passed == total:
        print("[OK] すべての分析レポートチェックに合格しました")
    else:
        print(f"[NG] {total - passed}件のチェックが失敗しました")


if __name__ == "__main__":
    main()
