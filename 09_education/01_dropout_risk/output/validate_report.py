"""
validate_report.py — 分析レポートの7チェック
実行: cd 09_education/01_dropout_risk && python output/validate_report.py
"""
import sys, subprocess, time
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "output"

def run_checks() -> list[tuple[str, bool, str]]:
    results = []

    def chk(name, ok, msg=""):
        results.append((name, ok, msg))

    report_path = OUT / "analysis_report.md"
    alert_path  = OUT / "alert_students_202401.csv"

    # 1. report_exists
    chk("report_exists", report_path.exists())
    # 2. alert_csv_exists
    chk("alert_csv_exists", alert_path.exists())

    if not report_path.exists():
        for name in ["all_sections","all_subjects","insight_keywords","numeric_present","alert_section"]:
            chk(name, False, "レポートなし")
        if not alert_path.exists():
            chk("alert_csv_student_id", False, "CSVなし")
        return results

    text = report_path.read_text(encoding="utf-8")

    # 3. all_sections
    sections = ["リスク分類", "科目", "コース", "アラート", "インサイト"]
    missing_sec = [s for s in sections if s not in text]
    chk("all_sections", len(missing_sec)==0, f"欠損: {missing_sec}")

    # 4. all_subjects
    subjects = ["数学", "英語", "物理", "国語", "情報"]
    missing_subj = [s for s in subjects if s not in text]
    chk("all_subjects", len(missing_subj)==0, f"欠損: {missing_subj}")

    # 5. insight_keywords
    keywords = ["退学", "リスク", "出席"]
    missing_kw = [k for k in keywords if k not in text]
    chk("insight_keywords", len(missing_kw)==0, f"欠損: {missing_kw}")

    # 6. numeric_present
    import re
    has_num = bool(re.search(r'\d+\.?\d*\s*%', text)) or bool(re.search(r'\d{2,}', text))
    chk("numeric_present", has_num)

    # 7. alert_section
    alert_kw = any(k in text for k in ["要支援", "介入", "アラート"])
    chk("alert_section", alert_kw)

    # alert_csv check (additional)
    if alert_path.exists():
        try:
            adf = pd.read_csv(alert_path, encoding="utf-8-sig")
            chk("alert_csv_student_id", "student_id" in adf.columns, f"columns: {list(adf.columns)}")
        except Exception as e:
            chk("alert_csv_student_id", False, str(e))
    else:
        chk("alert_csv_student_id", False, "CSVなし")

    return results

def main():
    MAX_ROUNDS = 5

    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"\n=== PDCA Round {round_num}/{MAX_ROUNDS} ===")

        # analyze.py 実行
        result = subprocess.run(
            ["C:/Users/realp/miniconda3/python.exe", "output/analyze.py"],
            cwd=str(BASE), capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0:
            print("analyze.py エラー:", result.stderr[-2000:])
        else:
            print(result.stdout)

        checks = run_checks()
        passed = sum(1 for _, ok, _ in checks if ok)
        total  = len(checks)
        print(f"結果: {passed}/{total} PASS")

        for name, ok, msg in checks:
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}" + (f" - {msg}" if msg else ""))

        if passed == total:
            print(f"\n全{total}チェック PASS - 完了")
            sys.exit(0)

        if round_num < MAX_ROUNDS:
            print(f"FAILあり。Round {round_num+1} へ...")
            time.sleep(1)

    print(f"\n最大ラウンド到達。{passed}/{total} PASS")
    sys.exit(1 if passed < total else 0)

if __name__ == "__main__":
    main()
