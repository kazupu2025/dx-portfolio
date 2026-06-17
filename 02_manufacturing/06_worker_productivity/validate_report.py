"""8項目レポートバリデーション"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_PATH = OUTPUT_DIR / "worker_summary_202401.csv"

checks = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append((name, status, detail))
    return condition


# 1. analysis_report.md存在
check("analysis_report.md存在", REPORT_PATH.exists())

# 2. worker_summary_202401.csv存在
check("worker_summary_202401.csv存在", SUMMARY_PATH.exists())

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    # 3. 「生産性」含む
    check("レポートに「生産性」含む", "生産性" in text)

    # 4. 「不良率」含む
    check("レポートに「不良率」含む", "不良率" in text)

    # 5. インサイト・改善示唆含む
    check("インサイト・改善示唆含む",
          "インサイト" in text or "改善示唆" in text or "推奨" in text or "OJT" in text)

    # 6. 数値含む
    check("レポートに数値含む", bool(re.search(r"\d{2,}", text)))

    # 7. 作業員IDランキング含む（WRK-）
    check("作業員IDランキング含む", bool(re.search(r"WRK-\d{3}", text)))

if SUMMARY_PATH.exists():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")

    # 8. サマリ行数 >= 1
    check("worker_summary行数>=1", len(df) >= 1, f"{len(df)}行")

print("\n=== validate_report.py 結果 ===")
passed = sum(1 for _, s, _ in checks if s == "PASS")
failed = sum(1 for _, s, _ in checks if s == "FAIL")
for name, status, detail in checks:
    mark = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {mark} {name}" + (f" ({detail})" if detail else ""))
print(f"\n合計: {passed}件PASS / {failed}件FAIL")

if failed > 0:
    sys.exit(1)
