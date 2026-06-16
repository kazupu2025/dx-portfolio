"""
C-31: 契約更新アラート・期限管理パイプライン レポートバリデーション
9項目チェック。[PASS]/[FAIL] のみ。絵文字・em-dash・バックスラッシュY記号なし。
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV_PATH = OUTPUT_DIR / "contract_summary_202401.csv"
RESULT_PATH = OUTPUT_DIR / "result_analysis.json"

results = []


def check(check_id, name, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id,
        "name": name,
        "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


# --- 1. analysis_report.md 存在確認 ---
check(1, "report_exists",
      REPORT_PATH.exists(),
      "analysis_report.md が存在しない", "analyze.py を再実行")

# --- 2. contract_summary_202401.csv 存在確認 ---
check(2, "summary_csv_exists",
      SUMMARY_CSV_PATH.exists(),
      "contract_summary_202401.csv が存在しない", "analyze.py を再実行")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    # --- 3. レポートに「契約」または「更新」含む ---
    check(3, "report_has_contract_or_renewal",
          "契約" in text or "更新" in text,
          "レポートに「契約」または「更新」が含まれない", "analyze.py のレポートタイトルを確認")

    # --- 4. レポートに「期限」または「アラート」含む ---
    check(4, "report_has_expiry_or_alert",
          "期限" in text or "アラート" in text,
          "レポートに「期限」または「アラート」が含まれない", "analyze.py のアラートセクションを確認")

    # --- 5. レポートにインサイト・まとめがある ---
    check(5, "report_has_insight",
          "インサイト" in text or "まとめ" in text or "改善示唆" in text,
          "レポートにインサイト/まとめセクションがない", "analyze.py のセクション5を確認")

    # --- 6. レポートに数値がある ---
    has_numbers = bool(re.search(r"\d{1,3}(,\d{3})+", text))
    check(6, "report_has_numbers",
          has_numbers,
          "レポートに数値（カンマ区切り整数）が含まれない", "analyze.py の金額フォーマットを確認")

    # --- 7. contract_summary_202401.csv の行数 >= 1 ---
    if SUMMARY_CSV_PATH.exists():
        import pandas as pd
        summary_df = pd.read_csv(SUMMARY_CSV_PATH, encoding="utf-8-sig")
        check(7, "summary_csv_row_count",
              len(summary_df) >= 1,
              f"contract_summary 行数: {len(summary_df)} (期待: >= 1)", "analyze.py を確認")
    else:
        check(7, "summary_csv_row_count",
              False, "contract_summary_202401.csv なし", "analyze.py を再実行")

    # --- 8. レポートに担当者別分析がある ---
    check(8, "report_has_agent_analysis",
          "担当者" in text or "田中" in text or "佐藤" in text or "鈴木" in text,
          "レポートに担当者別分析が含まれない", "analyze.py の担当者別ランキングセクションを確認")

    # --- 9. レポートに保険種別分析がある ---
    check(9, "report_has_insurance_type_analysis",
          "保険種別" in text or "生命保険" in text or "損害保険" in text or "医療保険" in text or "年金保険" in text,
          "レポートに保険種別分析が含まれない", "analyze.py の保険種別セクションを確認")

else:
    for i in range(3, 10):
        results.append({
            "id": i,
            "name": f"check_{i}",
            "status": "FAIL",
            "detail": "レポートなし",
            "fix_hint": "analyze.py を実行",
        })

# --- 結果出力 ---
passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output_data = {
    "passed": passed,
    "failed": failed,
    "all_passed": failed == 0,
    "results": results,
}
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_PATH.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*48}")
print(f"  レポート品質チェック: {passed}/{len(results)} PASS")
print(f"{'='*48}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}"
        line += f"\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\n  全{len(results)}項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")
