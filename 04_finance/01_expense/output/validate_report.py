import json
import re
from pathlib import Path

REPORT_PATH = Path("output/analysis_report.md")
CSV_PATH = Path("output/cleaned_expense_202401.csv")
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

    sections = ["部門別経費サマリー", "予算超過検知", "費目別経費サマリー", "日次経費トレンド", "異常値検出", "ビジネスインサイト"]
    missing = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing) == 0, f"欠落: {missing}", "analyze.py を確認")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        depts = df["department"].unique().tolist() if "department" in df.columns else []
        missing_d = [d for d in depts if d not in text]
        check(3, "all_depts_in_report", len(missing_d) == 0, f"未掲載部門: {missing_d}", "dept_summary を確認")
    else:
        check(3, "all_depts_in_report", False, "CSV なし", "cleanse.py を先に実行")

    keywords = ["総経費", "予算消化率", "経費合計"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0, f"欠落: {missing_kw}", "ビジネスインサイトを確認")

    anomaly_match = re.search(r"## 5.*?(?=## 6|\Z)", text, re.DOTALL)
    anomaly_lines = len(anomaly_match.group(0).strip().splitlines()) if anomaly_match else 0
    check(5, "anomaly_section_content", anomaly_lines >= 2, f"異常値セクションが薄い({anomaly_lines}行)", "±2σロジックを確認")

    has_numbers = bool(re.search(r"\d{1,3}(,\d{3})+円", text))
    check(6, "numeric_values_present", has_numbers, "金額が含まれない", "formatを確認")

    budget_section_ok = "予算超過" in text and "%" in text
    check(7, "budget_alert_section", budget_section_ok, "予算超過セクションが空", "analyze.py を確認")
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
