import json
import re
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "material_summary_202401.csv"
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


# 1: analysis_report.md 存在確認
check(1, "report_exists", REPORT_PATH.exists(),
      "analysis_report.md が存在しない", "analyze.py を再実行")

# 2: material_summary_202401.csv 存在確認
check(2, "summary_csv_exists", CSV_PATH.exists(),
      "material_summary_202401.csv が存在しない", "analyze.py を再実行")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    # 3: レポートに「原材料」または「コスト」含む
    has_keyword = "原材料" in text or "コスト" in text
    check(3, "has_material_or_cost", has_keyword,
          "「原材料」「コスト」がレポートに含まれない", "analyze.py の出力を確認")

    # 4: レポートに「変動」含む
    check(4, "has_hendo", "変動" in text,
          "「変動」がレポートに含まれない", "analyze.py の見出しを確認")

    # 5: レポートにインサイト・まとめがある
    has_insight = "インサイト" in text or "まとめ" in text or "ビジネス" in text
    check(5, "has_insight", has_insight,
          "インサイト・まとめセクションがない", "analyze.py のセクション5を確認")

    # 6: レポートに数値がある
    has_number = bool(re.search(r"\d{3,}", text))
    check(6, "has_numeric_values", has_number,
          "レポートに数値が含まれない", "analyze.py の数値フォーマットを確認")

    # 7: material_summary_202401.csvの行数 >= 1
    if CSV_PATH.exists():
        try:
            df_sum = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
            check(7, "summary_csv_rows", len(df_sum) >= 1,
                  f"summary CSV 行数 {len(df_sum)} < 1", "analyze.py の集計処理を確認")
        except Exception as e:
            check(7, "summary_csv_rows", False,
                  f"CSV 読み込みエラー: {e}", "analyze.py を確認")
    else:
        check(7, "summary_csv_rows", False, "summary CSV なし", "analyze.py を実行")

    # 8: レポートにカテゴリ別分析がある
    has_cat_section = "カテゴリ" in text and ("合計" in text or "変動率" in text)
    check(8, "has_category_analysis", has_cat_section,
          "カテゴリ別分析セクションが不足", "analyze.py のセクション1を確認")

    # 9: レポートに仕入先分析がある
    has_sup_section = "仕入先" in text or "SUP-" in text
    check(9, "has_supplier_analysis", has_sup_section,
          "仕入先分析セクションが不足", "analyze.py のセクション3を確認")

else:
    for i in range(3, 10):
        results.append({
            "id": i, "name": f"check_{i}", "status": "FAIL",
            "detail": "レポートなし", "fix_hint": "analyze.py を実行",
        })
    if not CSV_PATH.exists():
        pass  # check 2 already recorded

# --- 結果出力 ---
passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
out = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
OUTPUT_DIR.mkdir(exist_ok=True)
RESULT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*48}\n  Report quality check: {passed}/{len(results)} PASS\n{'='*48}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\n  All {len(results)} checks cleared!" if failed == 0 else f"\n  {failed} check(s) failed")
if failed > 0:
    raise SystemExit(1)
