# -*- coding: utf-8 -*-
"""10項目レポートバリデーション"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_PATH = OUTPUT_DIR / "delivery_summary_202401.csv"

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    return condition


# 1. analysis_report.md 存在
check("analysis_report.md存在", REPORT_PATH.exists())

# 2. delivery_summary_202401.csv 存在
check("delivery_summary_202401.csv存在", SUMMARY_PATH.exists())

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    # 3. 「利益率」含む
    check("レポートに「利益率」含む", "利益率" in text)

    # 4. 「配送区分」含む
    check("レポートに「配送区分」含む", "配送区分" in text)

    # 5. 「エリア」含む
    check("レポートに「エリア」含む", "エリア" in text)

    # 6. 「車両」または「km単価」含む
    check("レポートに「車両」または「km単価」含む",
          "車両" in text or "km単価" in text)

    # 7. インサイト・改善示唆含む
    check("インサイト・改善示唆含む",
          "インサイト" in text or "改善示唆" in text or "推奨" in text or "改善" in text)

    # 8. 数値含む
    check("レポートに数値含む", bool(re.search(r"\d{2,}", text)))

if SUMMARY_PATH.exists():
    df = pd.read_csv(SUMMARY_PATH, encoding="utf-8-sig")

    # 9. サマリ行数 >= 1
    check("サマリ行数>=1", len(df) >= 1, f"{len(df)}行")

    # 10. 配送区分列含む
    check("delivery_type列存在", "delivery_type" in df.columns)

print("\n=== validate_report.py 結果 ===")
total = len(results)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
for name, status, detail in results:
    mark = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {mark} {name}" + (f" ({detail})" if detail else ""))
print(f"\nResult: {passed}/{total} checks passed")

if failed > 0:
    sys.exit(1)
