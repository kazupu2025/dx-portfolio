"""
C-41: validate_report.py -- 分析出力の品質チェック (8項目以上)
絵文字・em-dash・YEN記号は使用しない。[PASS]/[FAIL]を使う。
"""

import re
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CSV_PATH = OUTPUT_DIR / "channel_summary_202401.csv"

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
# 2. channel_summary_202401.csv 存在確認
# -------------------------------------------------------------------
check("channel_summary_202401.csv が存在する", CSV_PATH.exists(), str(CSV_PATH))

report_text = ""
if REPORT_PATH.exists():
    report_text = REPORT_PATH.read_text(encoding="utf-8")

# -------------------------------------------------------------------
# 3. レポートに「採用」または「コスト」が含まれる
# -------------------------------------------------------------------
check("レポートに「採用」または「コスト」が含まれる",
      "採用" in report_text or "コスト" in report_text)

# -------------------------------------------------------------------
# 4. レポートに「チャネル」が含まれる
# -------------------------------------------------------------------
check("レポートに「チャネル」が含まれる", "チャネル" in report_text)

# -------------------------------------------------------------------
# 5. レポートにインサイト・まとめがある
# -------------------------------------------------------------------
check("レポートにインサイトまたはまとめセクションがある",
      "インサイト" in report_text or "まとめ" in report_text)

# -------------------------------------------------------------------
# 6. レポートに数値がある
# -------------------------------------------------------------------
has_number = bool(re.search(r"\d+", report_text))
check("レポートに数値が含まれる", has_number)

# -------------------------------------------------------------------
# 7. channel_summary_202401.csv の行数 >= 1
# -------------------------------------------------------------------
if CSV_PATH.exists():
    channel_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    check("channel_summary_202401.csv の行数 >= 1",
          len(channel_df) >= 1, f"実際: {len(channel_df)} 行")
else:
    check("channel_summary_202401.csv 行数チェック (ファイル不在のためスキップ)", False)

# -------------------------------------------------------------------
# 8. レポートに職種別分析が含まれる
# -------------------------------------------------------------------
check("レポートに職種別分析が含まれる",
      "職種" in report_text or "job_type" in report_text.lower())

# -------------------------------------------------------------------
# 9. レポートにフェーズ・ファネル分析が含まれる
# -------------------------------------------------------------------
check("レポートにフェーズ/ファネル分析が含まれる",
      "フェーズ" in report_text or "ファネル" in report_text)

# -------------------------------------------------------------------
# 10. channel_summary に channel 列が含まれる
# -------------------------------------------------------------------
if CSV_PATH.exists():
    channel_df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    check("channel_summary に channel 列が含まれる",
          "channel" in channel_df.columns,
          f"列: {list(channel_df.columns)}")
else:
    check("channel_summary 列チェック (ファイル不在のためスキップ)", False)

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
