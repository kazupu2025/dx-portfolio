"""
C-23: validate_report.py -- 分析成果物の品質チェック (7項目以上)
全PASS必須。絵文字・em-dashは使用しない(Windows CP932互換)。
"""

import sys
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "property_summary_202401.csv"

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
check("property_summary_202401.csv が存在する", CSV_PATH.exists(), str(CSV_PATH))

# レポートの内容チェック
report_text = ""
if REPORT_PATH.exists():
    try:
        report_text = REPORT_PATH.read_text(encoding="utf-8")
    except Exception as e:
        report_text = ""
        print(f"[WARN] レポート読み込みエラー: {e}")

# -------------------------------------------------------------------
# 3. 「修繕」キーワードを含む
# -------------------------------------------------------------------
check("レポートに「修繕」が含まれる", "修繕" in report_text,
      f"文字数: {len(report_text)}")

# -------------------------------------------------------------------
# 4. 「コスト」または「費用」キーワードを含む
# -------------------------------------------------------------------
has_cost_keyword = "コスト" in report_text or "費用" in report_text
check("レポートに「コスト」または「費用」が含まれる", has_cost_keyword)

# -------------------------------------------------------------------
# 5. インサイト記述を含む
# -------------------------------------------------------------------
has_insight = "インサイト" in report_text or "まとめ" in report_text or "推奨" in report_text
check("レポートにインサイト・まとめが含まれる", has_insight)

# -------------------------------------------------------------------
# 6. 数値（3桁以上）が含まれる
# -------------------------------------------------------------------
has_numbers = bool(re.search(r"\d{3,}", report_text))
check("レポートに数値（3桁以上）が含まれる", has_numbers)

# -------------------------------------------------------------------
# 7. CSVの行数 >= 1
# -------------------------------------------------------------------
if CSV_PATH.exists():
    import pandas as pd
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        check("property_summary_202401.csv の行数 >= 1", len(df) >= 1,
              f"実際: {len(df)} 行")
    except Exception as e:
        check("property_summary_202401.csv 読み込み成功", False, str(e))
else:
    check("property_summary_202401.csv の行数チェック", False, "ファイルが存在しない")

# -------------------------------------------------------------------
# 8. エリア分析が含まれる
# -------------------------------------------------------------------
has_area = "エリア" in report_text or "渋谷区" in report_text or "新宿区" in report_text
check("レポートにエリア別分析が含まれる", has_area)

# -------------------------------------------------------------------
# 9. 緊急対応の分析が含まれる
# -------------------------------------------------------------------
has_urgent = "緊急" in report_text
check("レポートに緊急対応の分析が含まれる", has_urgent)

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
