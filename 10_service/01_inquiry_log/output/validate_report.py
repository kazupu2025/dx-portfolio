"""
B-15 レポートバリデーション (7チェック)
"""
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
RPT_PATH = OUT / "analysis_report.md"

results = []

def check(name: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    results.append((name, ok, detail))
    print(msg)
    return ok

# 1. report_exists
if not check("report_exists", RPT_PATH.exists(), str(RPT_PATH)):
    print("レポートが存在しません。analyze.py を先に実行してください。")
    sys.exit(1)

with open(RPT_PATH, encoding="utf-8") as f:
    content = f.read()

# 2. all_sections
sections = ["カテゴリ", "担当者", "チャネル", "対応時間", "インサイト"]
missing_sections = [s for s in sections if s not in content]
check("all_sections", len(missing_sections)==0,
      f"missing: {missing_sections}" if missing_sections else "all sections present")

# 3. all_categories
cats = ["請求・支払い", "製品不具合", "使い方・操作方法", "配送・到着", "返品・交換", "その他"]
missing_cats = [c for c in cats if c not in content]
check("all_categories", len(missing_cats)==0,
      f"missing: {missing_cats}" if missing_cats else "all 6 categories present")

# 4. insight_keywords
kws = ["対応時間", "解決率", "エスカレ"]
missing_kws = [k for k in kws if k not in content]
check("insight_keywords", len(missing_kws)==0,
      f"missing: {missing_kws}" if missing_kws else "all keywords present")

# 5. operator_section_content (担当者セクション4行以上)
import re
op_section_match = re.search(r"## 担当者別パフォーマンス(.+?)(?=\n## |\Z)", content, re.DOTALL)
if op_section_match:
    op_lines = [l for l in op_section_match.group(1).strip().split("\n") if l.strip()]
    check("operator_section_content", len(op_lines) >= 4, f"operator lines: {len(op_lines)}")
else:
    check("operator_section_content", False, "operator section not found")

# 6. numeric_present
has_numeric = bool(re.search(r"\d+\.?\d*%", content))
check("numeric_present", has_numeric, "% values present")

# 7. alert_section
alert_keywords = ["アラート", "要改善", "長時間"]
has_alert = any(k in content for k in alert_keywords)
check("alert_section", has_alert, f"found: {[k for k in alert_keywords if k in content]}")

# サマリー
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
print(f"\n=== レポート検証: {passed}/{total} PASS ===")
if passed < total:
    sys.exit(1)
