"""
C-39: 入居者対応履歴・クレーム集計パイプライン
レポート出力バリデーションスクリプト（8項目以上）
絵文字・em-dash・円記号を使わず [PASS]/[FAIL] で表示する
"""

import sys
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
PROPERTY_CSV = OUTPUT_DIR / "property_summary_202401.csv"
JSON_PATH = OUTPUT_DIR / "result_analysis.json"


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "[PASS]" if passed else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    return passed


def run_validation() -> bool:
    results = []

    # 1. analysis_report.md の存在確認
    results.append(check("analysis_report.md の存在確認", REPORT_MD.exists(), str(REPORT_MD)))
    if not REPORT_MD.exists():
        print("[ERROR] レポートファイルが存在しません。analyze.py を先に実行してください。")
        return False

    content = REPORT_MD.read_text(encoding="utf-8")

    # 2. property_summary_202401.csv の存在確認
    results.append(check("property_summary_202401.csv の存在確認", PROPERTY_CSV.exists(), str(PROPERTY_CSV)))

    # 3. レポートに物件別セクションが含まれる
    results.append(check("物件別クレーム状況セクションの存在",
                         "物件別クレーム状況" in content))

    # 4. レポートにクレーム区分セクションが含まれる
    results.append(check("クレーム区分別発生件数セクションの存在",
                         "クレーム区分別発生件数" in content))

    # 5. 緊急対応セクションが含まれる
    results.append(check("緊急対応案件セクションの存在",
                         "緊急対応" in content))

    # 6. 月別トレンドセクションが含まれる
    results.append(check("月別トレンドセクションの存在",
                         "月別トレンド" in content))

    # 7. インサイト・改善示唆セクションが含まれる
    results.append(check("分析インサイト・改善示唆セクションの存在",
                         "改善示唆" in content or "インサイト" in content))

    # 8. property_summary_202401.csv の列チェック
    if PROPERTY_CSV.exists():
        import csv
        with open(PROPERTY_CSV, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
        expected_headers = ["property_name", "claim_count", "resolved_count",
                            "avg_response_days", "total_work_hours", "total_cost_estimate",
                            "resolution_rate_pct"]
        missing = [h for h in expected_headers if h not in headers]
        results.append(check("property_summary の必須列存在",
                             len(missing) == 0, f"不足: {missing}" if missing else ""))
    else:
        results.append(check("property_summary の必須列存在", False, "ファイルなし"))

    # 9. result_analysis.json の存在と内容確認
    results.append(check("result_analysis.json の存在", JSON_PATH.exists(), str(JSON_PATH)))
    if JSON_PATH.exists():
        try:
            data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
            required_keys = ["total_claims", "resolved_count", "unresolved_count", "avg_response_days"]
            missing_keys = [k for k in required_keys if k not in data]
            results.append(check("result_analysis.json の必須キー",
                                 len(missing_keys) == 0,
                                 f"不足: {missing_keys}" if missing_keys else ""))
            # total_claims が正の整数
            results.append(check("total_claims が正の値",
                                 isinstance(data.get("total_claims"), int) and data.get("total_claims", 0) > 0,
                                 f"値: {data.get('total_claims')}"))
        except json.JSONDecodeError as e:
            results.append(check("result_analysis.json の必須キー", False, f"JSON parse error: {e}"))
            results.append(check("total_claims が正の値", False, "JSON parse error"))
    else:
        results.append(check("result_analysis.json の必須キー", False, "ファイルなし"))
        results.append(check("total_claims が正の値", False, "ファイルなし"))

    # 集計
    passed = sum(results)
    total = len(results)
    print(f"\n--- Report Validation Summary ---")
    print(f"PASS: {passed} / {total}")
    if passed == total:
        print("Result: ALL PASSED")
    else:
        print(f"Result: {total - passed} FAILED")

    return passed == total


if __name__ == "__main__":
    ok = run_validation()
    sys.exit(0 if ok else 1)
