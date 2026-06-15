import json
import re
from pathlib import Path

OUTPUT_DIR  = Path(__file__).parent
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH    = OUTPUT_DIR / "cleaned_inquiry_202401.csv"
RESULT_PATH = OUTPUT_DIR / "result_analysis.json"
results = []


def check(check_id, name, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({"id": check_id, "name": name, "status": status,
                    "detail": "" if condition else detail,
                    "fix_hint": "" if condition else fix_hint})
    return condition


check(1, "report_exists", REPORT_PATH.exists(), "analysis_report.md が存在しない", "analyze.py を再実行")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    sections = ["ファネル分析", "エリア別成約率", "担当者別成約率", "問い合わせ経路別分析", "物件種別", "ビジネスインサイト"]
    missing = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing) == 0, f"欠落: {missing}", "analyze.py を確認")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        areas = df["area"].unique().tolist() if "area" in df.columns else []
        missing_a = [a for a in areas if a not in text]
        check(3, "all_areas_in_report", len(missing_a) == 0, f"未掲載エリア: {missing_a}", "area_summary を確認")
    else:
        check(3, "all_areas_in_report", False, "CSV なし", "cleanse.py を先に実行")

    keywords = ["成約率", "ファネル", "ビジネス"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0, f"欠落: {missing_kw}", "ビジネスインサイトを確認")

    funnel_match = re.search(r"## 1.*?(?=## 2|\Z)", text, re.DOTALL)
    funnel_lines = len(funnel_match.group(0).strip().splitlines()) if funnel_match else 0
    check(5, "funnel_section_content", funnel_lines >= 4, f"ファネルセクションが薄い({funnel_lines}行)", "stage_counts を確認")

    has_pct = bool(re.search(r"\d+\.\d+%", text))
    check(6, "numeric_rates_present", has_pct, "成約率数値が含まれない", "format を確認")

    conv_section_ok = "成約率" in text and ("⚠" in text or "✅" in text or "アラート" in text or "低成約率" in text or "正常" in text)
    check(7, "conversion_alert_section", conv_section_ok, "成約率アラートが不完全", "area_summary を確認")
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
