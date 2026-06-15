"""
発注最適化・需要予測パイプライン
レポート品質チェックリスト（7項目）
output/result_analysis.json に構造化結果を出力する
"""
import json
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
FORECAST_CSV = OUTPUT_DIR / "forecast_202401.csv"

results = []


def check(check_id, name, category, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id, "name": name, "category": category,
        "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


# 1. report_exists
check(1, "report_exists", "存在", REPORT_PATH.exists(),
      f"{REPORT_PATH} が存在しない", "analyze.py を再実行する")

# 2. forecast_csv_exists
check(2, "forecast_csv_exists", "存在", FORECAST_CSV.exists(),
      f"{FORECAST_CSV} が存在しない", "analyze.py を再実行する")

report_text = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else ""

# 3. all_sections
required_sections = ["需要予測", "欠品", "過剰在庫", "カテゴリ", "インサイト"]
missing_secs = [s for s in required_sections if s not in report_text]
check(3, "all_sections", "内容",
      len(missing_secs) == 0,
      f"不足セクション: {missing_secs}",
      "analyze.py のレポート生成部分を確認")

# 4. all_categories
required_cats = ["食品", "飲料", "日用品", "衣料", "電化製品"]
missing_cats = [c for c in required_cats if c not in report_text]
check(4, "all_categories", "内容",
      len(missing_cats) == 0,
      f"不足カテゴリ: {missing_cats}",
      "analyze.py のカテゴリ別サマリーを確認")

# 5. insight_keywords
insight_keywords = ["発注", "在庫", "欠品"]
missing_kw = [k for k in insight_keywords if k not in report_text]
check(5, "insight_keywords", "内容",
      len(missing_kw) == 0,
      f"不足キーワード: {missing_kw}",
      "analyze.py のインサイトセクションを確認")

# 6. numeric_present
import re
has_numeric = bool(re.search(r'\d+', report_text))
check(6, "numeric_present", "品質", has_numeric,
      "レポートに数値が含まれない", "analyze.py の数値出力ロジックを確認")

# 7. alert_section
has_alert = any(kw in report_text for kw in ["アラート", "緊急", "欠品リスク"])
check(7, "alert_section", "内容", has_alert,
      "アラートセクションが含まれない（'アラート' or '緊急' or '欠品リスク'）",
      "analyze.py のインサイトセクションにアラート文言を追加")

# ── forecast_csv 商品数チェック（bonus: analyze.py が 50行 出力しているか）
if FORECAST_CSV.exists():
    try:
        fdf = pd.read_csv(FORECAST_CSV, encoding="utf-8-sig")
        n_products = fdf.shape[0]
        print(f"  forecast_202401.csv: {n_products} 商品")
    except Exception as e:
        print(f"  forecast_202401.csv 読み込みエラー: {e}")

# ── 結果出力 ──────────────────────────────────────────────────────────
passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed

output = {
    "passed": passed,
    "failed": failed,
    "all_passed": failed == 0,
    "results": results,
}
(OUTPUT_DIR / "result_analysis.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}")
print(f"  レポート品質チェック: {passed}/{len(results)} PASS")
print(f"{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}]  [{r['category']:4s}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}"
    print(line)

if failed == 0:
    print("\n  全7項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。")
