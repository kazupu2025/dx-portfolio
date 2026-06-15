import json
import re
from pathlib import Path

REPORT_PATH = Path("output/analysis_report.md")
CSV_PATH    = Path("output/cleaned_cost_202401.csv")
RESULT_PATH = Path("output/result_analysis.json")
results = []


def check(check_id, name, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({"id": check_id, "name": name, "status": status,
                    "detail": "" if condition else detail,
                    "fix_hint": "" if condition else fix_hint})
    return condition


check(1, "report_exists", REPORT_PATH.exists(),
      "analysis_report.md が存在しない", "analyze.py を再実行")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    sections = ["カテゴリ別仕入コスト", "店舗別食材ロス率", "廃棄コスト上位食材",
                "日次廃棄コスト", "高廃棄ロス検出", "ビジネスインサイト"]
    missing = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing) == 0,
          f"欠落: {missing}", "analyze.py を確認")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        stores = df["store"].unique().tolist() if "store" in df.columns else []
        missing_s = [s for s in stores if s not in text]
        check(3, "all_stores_in_report", len(missing_s) == 0,
              f"未掲載店舗: {missing_s}", "store_summary を確認")
    else:
        check(3, "all_stores_in_report", False, "CSV なし", "cleanse.py を先に実行")

    keywords = ["ロス率", "廃棄", "仕入"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0,
          f"欠落: {missing_kw}", "ビジネスインサイトを確認")

    cat_match = re.search(r"## 1.*?(?=## 2|\Z)", text, re.DOTALL)
    cat_lines = len(cat_match.group(0).strip().splitlines()) if cat_match else 0
    check(5, "category_section_content", cat_lines >= 4,
          f"カテゴリセクションが薄い({cat_lines}行)", "cat_summary を確認")

    has_yen = bool(re.search(r"\d{1,3}(,\d{3})+円", text))
    check(6, "numeric_cost_present", has_yen,
          "コスト金額が含まれない", "format を確認")

    alert_ok = ("アラート" in text or "要対応" in text or "要改善" in text) and "ロス率" in text
    check(7, "alert_section", alert_ok,
          "アラートセクションが不完全", "analyze.py を確認")
else:
    for i in range(2, 8):
        results.append({"id": i, "name": f"check_{i}", "status": "FAIL",
                        "detail": "レポートなし", "fix_hint": "analyze.py を実行"})

passed = sum(1 for r in results if r["status"] == "PASS")
failed  = len(results) - passed
out = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
RESULT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*48}\n  レポート品質チェック: {passed}/{len(results)} PASS\n{'='*48}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print("\n  全7項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")
if failed > 0:
    raise SystemExit(1)
