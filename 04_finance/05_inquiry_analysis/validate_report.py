# -*- coding: utf-8 -*-
"""
C-52: 保険契約問い合わせ・対応履歴分析パイプライン レポートバリデーション
10項目チェック。[PASS]/[FAIL] のみ。絵文字・em-dash なし。
"""
import json
import re
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
TYPE_CSV_PATH = OUTPUT_DIR / "type_summary_202401.csv"
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

# --- 2. type_summary_202401.csv 存在確認 ---
check(2, "type_csv_exists",
      TYPE_CSV_PATH.exists(),
      "type_summary_202401.csv が存在しない", "analyze.py を再実行")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    # --- 3. レポートに「保険」または「問い合わせ」含む ---
    check(3, "report_has_insurance_or_inquiry",
          "保険" in text or "問い合わせ" in text,
          "レポートに「保険」または「問い合わせ」が含まれない", "analyze.py のレポートタイトルを確認")

    # --- 4. レポートに「解決率」含む ---
    check(4, "report_has_resolution_rate",
          "解決率" in text,
          "レポートに「解決率」が含まれない", "analyze.py の分析セクションを確認")

    # --- 5. レポートにインサイト・まとめがある ---
    check(5, "report_has_insight",
          "インサイト" in text or "まとめ" in text or "改善示唆" in text,
          "レポートにインサイト/まとめセクションがない", "analyze.py のセクション6を確認")

    # --- 6. レポートに数値がある ---
    has_numbers = bool(re.search(r"\d+\.\d+|\d{2,}", text))
    check(6, "report_has_numbers",
          has_numbers,
          "レポートに数値が含まれない", "analyze.py の数値フォーマットを確認")

    # --- 7. type_summary_202401.csv の行数 >= 1 ---
    if TYPE_CSV_PATH.exists():
        type_df = pd.read_csv(TYPE_CSV_PATH, encoding="utf-8-sig")
        check(7, "type_csv_row_count",
              len(type_df) >= 1,
              f"type_summary 行数: {len(type_df)} (期待: >= 1)", "analyze.py を確認")
    else:
        check(7, "type_csv_row_count",
              False, "type_summary_202401.csv なし", "analyze.py を再実行")

    # --- 8. レポートにチャネル別分析がある ---
    check(8, "report_has_channel_analysis",
          "チャネル" in text or "電話" in text or "メール" in text or "窓口" in text,
          "レポートにチャネル別分析が含まれない", "analyze.py のセクション3を確認")

    # --- 9. レポートにオペレーター別分析がある ---
    check(9, "report_has_operator_analysis",
          "オペレーター" in text or "OP-" in text or "担当" in text,
          "レポートにオペレーター別分析が含まれない", "analyze.py のセクション4を確認")

    # --- 10. レポートに満足度の記述がある ---
    check(10, "report_has_satisfaction",
          "満足度" in text or "CS" in text or "評価" in text,
          "レポートに満足度の記述が含まれない", "analyze.py のサマリーセクションを確認")
else:
    for i in range(3, 11):
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
print(f"  Report quality check: {passed}/{len(results)} PASS")
print(f"{'='*48}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}"
        line += f"\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\nResult: {passed}/{len(results)} checks passed")
