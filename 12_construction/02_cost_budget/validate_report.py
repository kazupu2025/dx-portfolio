# -*- coding: utf-8 -*-
"""
C-58: validate_report.py -- 分析成果物の品質チェック (10項目)
全PASS必須。絵文字・em-dashは使用しない(Windows CP932互換)。
"""

import re
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "project_summary_202401.csv"

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
check("project_summary_202401.csv が存在する", CSV_PATH.exists(), str(CSV_PATH))

# レポートの内容チェック
report_text = ""
if REPORT_PATH.exists():
    try:
        report_text = REPORT_PATH.read_text(encoding="utf-8")
    except Exception as e:
        report_text = ""
        print(f"[WARN] レポート読み込みエラー: {e}")

# -------------------------------------------------------------------
# 3. 「予算」キーワードを含む
# -------------------------------------------------------------------
check("レポートに「予算」が含まれる", "予算" in report_text,
      f"文字数: {len(report_text)}")

# -------------------------------------------------------------------
# 4. 「工事」キーワードを含む
# -------------------------------------------------------------------
check("レポートに「工事」が含まれる", "工事" in report_text)

# -------------------------------------------------------------------
# 5. インサイト・まとめが含まれる
# -------------------------------------------------------------------
has_insight = "インサイト" in report_text or "まとめ" in report_text or "推奨" in report_text
check("レポートにインサイト・まとめが含まれる", has_insight)

# -------------------------------------------------------------------
# 6. 数値（3桁以上）が含まれる
# -------------------------------------------------------------------
has_numbers = bool(re.search(r"\d{3,}", report_text))
check("レポートに数値（3桁以上）が含まれる", has_numbers)

# -------------------------------------------------------------------
# 7. サマリーCSVの行数 >= 4 (4プロジェクト以上)
# -------------------------------------------------------------------
if CSV_PATH.exists():
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        check("project_summary_202401.csv の行数 >= 4", len(df) >= 4,
              f"実際: {len(df)} 行")
    except Exception as e:
        check("project_summary_202401.csv 読み込み成功", False, str(e))
else:
    check("project_summary_202401.csv の行数チェック", False, "ファイルが存在しない")

# -------------------------------------------------------------------
# 8. サマリーCSVに必要列が含まれる
# -------------------------------------------------------------------
if CSV_PATH.exists():
    try:
        df_sum = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        needed = ["project_no", "budget_total", "actual_total", "variance_rate", "over_count"]
        missing = [c for c in needed if c not in df_sum.columns]
        check("project_summary に必要列が含まれる", len(missing) == 0, f"不足: {missing}")
    except Exception as e:
        check("project_summary 列チェック", False, str(e))
else:
    check("project_summary 列チェック", False, "ファイルが存在しない")

# -------------------------------------------------------------------
# 9. 「差異」キーワードを含む
# -------------------------------------------------------------------
check("レポートに「差異」が含まれる", "差異" in report_text)

# -------------------------------------------------------------------
# 10. 「費目」キーワードを含む
# -------------------------------------------------------------------
check("レポートに「費目」が含まれる", "費目" in report_text)

# -------------------------------------------------------------------
# 結果サマリー
# -------------------------------------------------------------------
total = len(results)
passed = sum(results)
failed = total - passed

print(f"\nResult: {passed}/{total} checks passed")

if failed > 0:
    print(f"FAIL: {failed} 件の検証に失敗しました")
    sys.exit(1)
else:
    print("全チェック PASS")
    sys.exit(0)
