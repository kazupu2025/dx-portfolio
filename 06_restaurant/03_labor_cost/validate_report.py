"""
C-20: validate_report.py -- 分析成果物の品質チェック (7項目以上)
全PASS必須。絵文字・em-dashは使用しない(Windows CP932互換)。
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "labor_summary_202401.csv"

results = []


def check(label: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append(passed)


# -------------------------------------------------------------------
# 1. レポートファイル存在チェック
# -------------------------------------------------------------------
check("analysis_report.md が存在する", REPORT_PATH.exists(), str(REPORT_PATH))

# -------------------------------------------------------------------
# 2. サマリーCSV 存在チェック
# -------------------------------------------------------------------
check("labor_summary_202401.csv が存在する", CSV_PATH.exists(), str(CSV_PATH))

# レポートの内容チェック
report_text = ""
if REPORT_PATH.exists():
    try:
        report_text = REPORT_PATH.read_text(encoding="utf-8")
    except Exception as e:
        report_text = ""
        print(f"[WARN] レポート読み込みエラー: {e}")

# -------------------------------------------------------------------
# 3. 「人件費」キーワードを含む
# -------------------------------------------------------------------
check("レポートに「人件費」が含まれる", "人件費" in report_text,
      f"文字数: {len(report_text)}")

# -------------------------------------------------------------------
# 4. 「店舗」キーワードを含む
# -------------------------------------------------------------------
check("レポートに「店舗」が含まれる", "店舗" in report_text)

# -------------------------------------------------------------------
# 5. インサイト記述を含む
# -------------------------------------------------------------------
has_insight = "インサイト" in report_text or "まとめ" in report_text or "推奨" in report_text
check("レポートにインサイト・まとめが含まれる", has_insight)

# -------------------------------------------------------------------
# 6. 数値（円または時間）が含まれる
# -------------------------------------------------------------------
import re
has_numbers = bool(re.search(r"\d{3,}", report_text))
check("レポートに数値（3桁以上）が含まれる", has_numbers)

# -------------------------------------------------------------------
# 7. CSVの行数 >= 1
# -------------------------------------------------------------------
if CSV_PATH.exists():
    import pandas as pd
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        check("labor_summary_202401.csv の行数 >= 1", len(df) >= 1,
              f"実際: {len(df)} 行")
    except Exception as e:
        check("labor_summary_202401.csv 読み込み成功", False, str(e))
else:
    check("labor_summary_202401.csv の行数チェック", False, "ファイルが存在しない")

# -------------------------------------------------------------------
# 8. レポートに雇用区分の分析が含まれる
# -------------------------------------------------------------------
has_emp_analysis = "アルバイト" in report_text or "雇用区分" in report_text
check("レポートに雇用区分の分析が含まれる", has_emp_analysis)

# -------------------------------------------------------------------
# 結果サマリー
# -------------------------------------------------------------------
total = len(results)
passed = sum(results)
failed = total - passed

print(f"\n結果: {passed}/{total} PASS")

if failed > 0:
    print(f"FAIL: {failed} 件の検証に失敗しました")
    sys.exit(1)
else:
    print("全チェック PASS")
    sys.exit(0)
