"""7項目レポートバリデーション"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_PATH = OUTPUT_DIR / "variance_summary_202401.csv"

checks = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append((name, status, detail))
    return condition

# 1
check("analysis_report.md存在", REPORT_PATH.exists())

# 2
check("variance_summary_202401.csv存在", SUMMARY_PATH.exists())

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    # 3
    check("レポートに「差異」含む", "差異" in text)

    # 4
    check("レポートに「材料費」または「コスト」含む", "材料費" in text or "コスト" in text)

    # 5
    check("インサイト・提案含む", "改善提案" in text or "インサイト" in text or "推奨" in text)

    # 6 - numbers in report
    check("レポートに数値含む", bool(re.search(r"\d{3,}", text)))

if SUMMARY_PATH.exists():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")
    # 7
    check("variance_summary行数>=1", len(df) >= 1, f"{len(df)}行")

print("\n=== validate_report.py 結果 ===")
passed = sum(1 for _, s, _ in checks if s == "PASS")
failed = sum(1 for _, s, _ in checks if s == "FAIL")
for name, status, detail in checks:
    mark = "PASS" if status == "PASS" else "FAIL"
    print(f"  [{mark}] {status} - {name}" + (f" ({detail})" if detail else ""))
print(f"\n合計: {passed}件PASS / {failed}件FAIL")

if failed > 0:
    sys.exit(1)
