"""
C-30: validate_report.py -- 分析出力の品質チェック (9項目)
絵文字・em-dash・YEN記号は使用しない。[PASS]/[FAIL]を使う。
"""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "dept_summary_202401.csv"

results = []


def check(label: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append(passed)


# -------------------------------------------------------------------
# 1. analysis_report.md 存在確認
# -------------------------------------------------------------------
check("analysis_report.md が存在する", REPORT_PATH.exists(), str(REPORT_PATH))

# -------------------------------------------------------------------
# 2. dept_summary_202401.csv 存在確認
# -------------------------------------------------------------------
check("dept_summary_202401.csv が存在する", CSV_PATH.exists(), str(CSV_PATH))

# レポートが存在する場合のみ内容チェック
report_text = ""
if REPORT_PATH.exists():
    report_text = REPORT_PATH.read_text(encoding="utf-8")

# -------------------------------------------------------------------
# 3. レポートに「人件費」含む
# -------------------------------------------------------------------
check("レポートに「人件費」が含まれる", "人件費" in report_text)

# -------------------------------------------------------------------
# 4. レポートに「予算」または「差異」含む
# -------------------------------------------------------------------
check("レポートに「予算」または「差異」が含まれる",
      "予算" in report_text or "差異" in report_text)

# -------------------------------------------------------------------
# 5. レポートにインサイト・まとめがある
# -------------------------------------------------------------------
check("レポートにインサイトまたはまとめセクションがある",
      "インサイト" in report_text or "まとめ" in report_text)

# -------------------------------------------------------------------
# 6. レポートに数値がある
# -------------------------------------------------------------------
import re
has_number = bool(re.search(r"\d+", report_text))
check("レポートに数値が含まれる", has_number)

# -------------------------------------------------------------------
# 7. dept_summary_202401.csv の行数 >= 1
# -------------------------------------------------------------------
if CSV_PATH.exists():
    dept_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    check("dept_summary_202401.csv の行数 >= 1", len(dept_df) >= 1, f"実際: {len(dept_df)} 行")
else:
    check("dept_summary_202401.csv 行数チェック (ファイル不在のためスキップ)", False)

# -------------------------------------------------------------------
# 8. レポートに部門別分析がある
# -------------------------------------------------------------------
check("レポートに部門別分析が含まれる",
      "部門" in report_text or "department" in report_text.lower())

# -------------------------------------------------------------------
# 9. レポートに雇用区分別分析がある
# -------------------------------------------------------------------
check("レポートに雇用区分別分析が含まれる",
      "雇用区分" in report_text or "雇用形態" in report_text)

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
