# -*- coding: utf-8 -*-
"""
C-38: 予約キャンセル集計・傾向分析パイプライン
レポートバリデーションスクリプト (8項目以上チェック)
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
STORE_CSV = OUTPUT_DIR / "store_summary_202401.csv"
JSON_FILE = OUTPUT_DIR / "result_analysis.json"


def check(label, condition, detail=""):
    tag = "[PASS]" if condition else "[FAIL]"
    msg = f"{tag} {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    return condition


def main():
    results = []

    # 1. レポートファイル存在確認
    results.append(check("01. analysis_report.md が存在する", REPORT_FILE.exists()))

    # 2. 店舗サマリーCSV存在確認
    results.append(check("02. store_summary_202401.csv が存在する", STORE_CSV.exists()))

    # 3. JSONサマリー存在確認
    results.append(check("03. result_analysis.json が存在する", JSON_FILE.exists()))

    if not REPORT_FILE.exists():
        print("[FAIL] レポートファイルが存在しないため以降のチェックをスキップします")
        sys.exit(1)

    content = REPORT_FILE.read_text(encoding="utf-8")

    # 4. レポートに店舗別分析セクションが含まれる
    results.append(check("04. 店舗別キャンセル分析セクションが存在する", "店舗別" in content))

    # 5. レポートにキャンセル理由セクションが含まれる
    results.append(check("05. キャンセル理由別ランキングセクションが存在する", "キャンセル理由" in content))

    # 6. レポートに曜日別セクションが含まれる
    results.append(check("06. 曜日別セクションが存在する", "曜日" in content))

    # 7. レポートにコース別セクションが含まれる
    results.append(check("07. コース別セクションが存在する", "コース" in content))

    # 8. レポートに改善示唆セクションが含まれる
    results.append(check("08. 改善示唆セクションが存在する", "改善示唆" in content))

    # 9. JSONのキーが正しい
    if JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        required_keys = {"total_reserv", "cancel_count", "cancel_rate", "loss_amount_total"}
        has_keys = required_keys.issubset(data.keys())
        results.append(check("09. result_analysis.json に必須キーが存在する", has_keys, f"keys={list(data.keys())}"))

        # 10. キャンセル率が0~100の範囲
        rate_ok = 0 <= data.get("cancel_rate", -1) <= 100
        results.append(check("10. cancel_rate が 0-100 の範囲", rate_ok, f"actual={data.get('cancel_rate')}"))

        # 11. 損失金額が非負
        loss_ok = data.get("loss_amount_total", -1) >= 0
        results.append(check("11. loss_amount_total が非負", loss_ok, f"actual={data.get('loss_amount_total')}"))
    else:
        results.append(check("09. result_analysis.json に必須キーが存在する", False, "file missing"))
        results.append(check("10. cancel_rate が 0-100 の範囲", False, "file missing"))
        results.append(check("11. loss_amount_total が非負", False, "file missing"))

    # 12. レポートに全体サマリーが含まれる
    results.append(check("12. 全体サマリーセクションが存在する", "全体サマリー" in content or "サマリー" in content))

    # サマリー
    pass_count = sum(results)
    total = len(results)
    print(f"\nResult: {pass_count}/{total} checks passed")

    if pass_count < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
