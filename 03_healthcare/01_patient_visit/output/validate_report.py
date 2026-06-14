import json
import re
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH    = OUTPUT_DIR / "cleaned_visit_202401.csv"
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

    sections = ["時間帯別来院数", "曜日別来院数", "診療科別来院サマリー",
                "曜日×時間帯", "長時間待ち分析", "ビジネスインサイト"]
    missing = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing) == 0, f"欠落: {missing}", "analyze.py を確認")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        depts = df["department"].unique().tolist() if "department" in df.columns else []
        missing_d = [d for d in depts if d not in text]
        check(3, "all_depts_in_report", len(missing_d) == 0, f"未掲載診療科: {missing_d}", "dept_summary を確認")
    else:
        check(3, "all_depts_in_report", False, "CSV なし", "cleanse.py を先に実行")

    keywords = ["ピーク", "待ち時間", "来院数"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0, f"欠落: {missing_kw}", "ビジネスインサイトを確認")

    peak_match = re.search(r"## 1.*?(?=## 2|\Z)", text, re.DOTALL)
    peak_lines = len(peak_match.group(0).strip().splitlines()) if peak_match else 0
    check(5, "peak_section_content", peak_lines >= 3, f"時間帯セクションが薄い({peak_lines}行)", "hour_counts を確認")

    has_numbers = bool(re.search(r"\d+件", text))
    check(6, "numeric_counts_present", has_numbers, "来院件数が含まれない", "format を確認")

    wait_section_ok = "長時間待ち" in text and ("件" in text or "%" in text)
    check(7, "wait_alert_section", wait_section_ok, "長時間待ちセクションが不完全", "analyze.py を確認")
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
