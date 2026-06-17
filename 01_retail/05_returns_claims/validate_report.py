# -*- coding: utf-8 -*-
"""
C-34 返品・クレームデータ集計レポートパイプライン
レポートバリデーションスクリプト

analysis_report.md と store_summary_202401.csv に対して 8 項目以上のチェックを実施する。
絵文字・em-dash・記号は使わず [PASS]/[FAIL] を使う。
"""

import sys
import re
import json
import pandas as pd
from pathlib import Path


def check(label: str, condition: bool) -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {label}")
    return condition


def main() -> None:
    base_dir = Path(__file__).parent
    output_dir = base_dir / "output"
    report_path = output_dir / "analysis_report.md"
    store_csv_path = output_dir / "store_summary_202401.csv"
    json_path = output_dir / "result_analysis.json"

    results = []

    # 1. analysis_report.md の存在確認
    results.append(check("01. analysis_report.md が存在する", report_path.exists()))

    if report_path.exists():
        report_text = report_path.read_text(encoding="utf-8")

        # 2. レポートが空でない
        results.append(check(f"02. レポートが空でない ({len(report_text)} 文字)", len(report_text) > 100))

        # 3. タイトルが含まれる
        results.append(check("03. タイトル行が含まれる (# 返品)", "# 返品" in report_text))

        # 4. 店舗別サマリーセクションが存在する
        results.append(check("04. 店舗別サマリーセクションが存在する", "店舗別" in report_text))

        # 5. クレーム区分セクションが存在する
        results.append(check("05. クレーム区分ランキングセクションが存在する", "クレーム区分" in report_text))

        # 6. インサイト・改善示唆セクションが存在する
        results.append(check("06. インサイト・改善示唆セクションが存在する", "インサイト" in report_text or "改善示唆" in report_text))

        # 7. 数値が含まれる（件数など）
        has_numbers = bool(re.search(r"\d+", report_text))
        results.append(check("07. レポートに数値が含まれる", has_numbers))

        # 8. Markdown テーブルが含まれる
        has_table = "|" in report_text and "---" in report_text
        results.append(check("08. Markdown テーブルが含まれる", has_table))

    else:
        for i in range(2, 9):
            results.append(check(f"0{i}. (スキップ - ファイル未存在)", False))

    # 9. store_summary_202401.csv の存在確認
    results.append(check("09. store_summary_202401.csv が存在する", store_csv_path.exists()))

    if store_csv_path.exists():
        try:
            store_df = pd.read_csv(store_csv_path, encoding="utf-8-sig")

            # 10. 店舗数が 5 件
            results.append(check(
                f"10. 店舗サマリーに 5 店舗分のデータがある (実際: {len(store_df)})",
                len(store_df) == 5,
            ))

            # 11. 必須集計列が存在する
            expected_cols = ["クレーム件数", "解決率", "平均返品金額"]
            has_cols = all(c in store_df.columns for c in expected_cols)
            results.append(check(f"11. 必須集計列が存在する ({expected_cols})", has_cols))

        except Exception as e:
            results.append(check(f"10. 店舗サマリー読み込みエラー: {e}", False))
            results.append(check("11. 必須集計列の確認 (スキップ)", False))
    else:
        results.append(check("10. (スキップ - ファイル未存在)", False))
        results.append(check("11. (スキップ - ファイル未存在)", False))

    # 12. result_analysis.json の存在確認
    results.append(check("12. result_analysis.json が存在する", json_path.exists()))

    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            has_keys = all(k in data for k in ["total_claims", "resolve_rate", "avg_response_days"])
            results.append(check("13. JSON に必須キーが存在する", has_keys))

            resolve_rate_valid = 70 <= data.get("resolve_rate", 0) <= 100
            results.append(check(
                f"14. 解決率が妥当な範囲 70-100% (実際: {data.get('resolve_rate')}%)",
                resolve_rate_valid,
            ))
        except Exception as e:
            results.append(check(f"13. JSON パースエラー: {e}", False))
            results.append(check("14. 解決率確認 (スキップ)", False))
    else:
        results.append(check("13. (スキップ - ファイル未存在)", False))
        results.append(check("14. (スキップ - ファイル未存在)", False))

    # サマリー
    passed = sum(results)
    total = len(results)
    print(f"\n[SUMMARY] {passed}/{total} checks passed")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
