import json
import re
from pathlib import Path

REPORT_PATH = Path("output/analysis_report.md")
CSV_PATH = Path("output/cleaned_inspection_202401.csv")
RESULT_PATH = Path("output/result_analysis.json")
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

    sections = ["工程別不良率サマリー", "異常値検出", "製品別不良率", "日次不良率トレンド", "検査員別", "ビジネスインサイト"]
    missing = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing) == 0, f"欠落: {missing}", "analyze.py を確認")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        procs = df["process"].unique().tolist() if "process" in df.columns else []
        missing_p = [p for p in procs if p not in text]
        check(3, "all_processes_in_report", len(missing_p) == 0, f"未掲載工程: {missing_p}", "proc_summary を確認")
    else:
        check(3, "all_processes_in_report", False, "CSV なし", "cleanse.py を先に実行")

    keywords = ["不良率", "アラート", "ビジネス"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0, f"欠落: {missing_kw}", "ビジネスインサイトを確認")

    anomaly_match = re.search(r"## 2.*?(?=## 3|\Z)", text, re.DOTALL)
    anomaly_lines = len(anomaly_match.group(0).strip().splitlines()) if anomaly_match else 0
    check(5, "anomaly_section_content", anomaly_lines >= 2, f"異常値セクションが薄い({anomaly_lines}行)", "±Nσロジックを確認")

    has_pct = bool(re.search(r"\d+\.\d+%", text))
    check(6, "numeric_rates_present", has_pct, "不良率数値が含まれない", "format を確認")

    defect_section_ok = "不良率" in text and ("⚠" in text or "✅" in text or "要対応" in text or "正常" in text)
    check(7, "defect_alert_section", defect_section_ok, "不良率アラートセクションが不完全", "proc_summary を確認")
else:
    for i in range(2, 8):
        results.append({"id": i, "name": f"check_{i}", "status": "FAIL",
                        "detail": "レポートなし", "fix_hint": "analyze.py を実行"})

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*48}\n  レポート品質チェック: {passed}/{len(results)} PASS\n{'='*48}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print("\n  全7項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")
