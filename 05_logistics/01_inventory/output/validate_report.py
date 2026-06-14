import json
import re
from pathlib import Path

BASE_DIR = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/05_logistics/01_inventory")
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "cleaned_inventory_202401.csv"
RESULT_PATH = OUTPUT_DIR / "result_analysis.json"

results = []


def check(check_id, name, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({"id": check_id, "name": name, "status": status,
                    "detail": "" if condition else detail,
                    "fix_hint": "" if condition else fix_hint})
    return condition


check(1, "report_exists", REPORT_PATH.exists(),
      "analysis_report.md が存在しない", "analyze.py を再実行する")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    sections = ["倉庫別在庫サマリー", "欠品検知", "倉庫別欠品品目数",
                "在庫回転率", "異常値検出", "ビジネスインサイト"]
    missing_sec = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing_sec) == 0,
          f"欠落セクション: {missing_sec}", "analyze.py の各分析ブロックを確認する")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        warehouses = df["warehouse"].unique().tolist() if "warehouse" in df.columns else []
        missing_wh = [w for w in warehouses if w not in text]
        check(3, "all_warehouses_in_report", len(missing_wh) == 0,
              f"レポートに未掲載の倉庫: {missing_wh}", "wh_summary を確認")
    else:
        check(3, "all_warehouses_in_report", False, "CSVが存在しない", "inventory-cleaner を先に実行")

    keywords = ["欠品品目数", "総在庫金額", "在庫金額"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0,
          f"欠落キーワード: {missing_kw}", "analyze.py の '6. ビジネスインサイト' を確認")

    anomaly_match = re.search(r"## 5.*?(?=## 6|\Z)", text, re.DOTALL)
    anomaly_lines = len(anomaly_match.group(0).strip().splitlines()) if anomaly_match else 0
    check(5, "anomaly_section_content", anomaly_lines >= 2,
          f"異常値検出セクションが薄い（{anomaly_lines}行）", "analyze.py の ±2σ ロジックを確認")

    has_numbers = bool(re.search(r"\d{1,3}(,\d{3})+円", text))
    check(6, "numeric_values_present", has_numbers,
          "レポートに金額が含まれない", "analyze.py の format 処理を確認")

    stockout_section_ok = "欠品" in text and "%" in text
    check(7, "stockout_section", stockout_section_ok,
          "欠品検知セクションが存在しないか内容が空", "analyze.py の '2. 欠品検知' を確認")
else:
    for i in range(2, 8):
        results.append({"id": i, "name": f"check_{i}", "status": "FAIL",
                        "detail": "レポートが存在しないためスキップ",
                        "fix_hint": "analyze.py を実行してレポートを生成する"})

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*48}")
print(f"  レポート品質チェック: {passed}/{len(results)} PASS")
print(f"{'='*48}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)

if failed == 0:
    print("\n  全7項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。result_analysis.json を参照してください。")
