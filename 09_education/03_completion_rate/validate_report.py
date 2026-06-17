import json
import re
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
REPORT_PATH = BASE / "output" / "analysis_report.md"
CSV_PATH = BASE / "output" / "course_summary_202401.csv"
RESULT_PATH = BASE / "output" / "result_analysis.json"

results = []


def check(check_id, name, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id, "name": name, "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


# 1: レポート存在
check(1, "report_exists", REPORT_PATH.exists(),
      "analysis_report.md が存在しない", "analyze.py を再実行")

# 2: 講座サマリーCSV存在
check(2, "summary_csv_exists", CSV_PATH.exists(),
      "course_summary_202401.csv が存在しない", "analyze.py を再実行")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    # 3: "修了率" を含む
    check(3, "contains_completion_rate", "修了率" in text,
          "レポートに「修了率」が含まれない", "analyze.py のレポート生成を確認")

    # 4: "講座" を含む
    check(4, "contains_course", "講座" in text,
          "レポートに「講座」が含まれない", "analyze.py のレポート生成を確認")

    # 5: インサイトセクション存在
    check(5, "insight_section_exists",
          "インサイト" in text or "改善" in text or "ビジネス" in text,
          "インサイト/改善セクションがない", "analyze.py の Section 6 を確認")

    # 6: 数値が含まれる
    has_numeric = bool(re.search(r"\d+\.\d+", text))
    check(6, "numeric_values_present", has_numeric,
          "レポートに数値が含まれない", "analyze.py のフォーマットを確認")

    # 7: "受講者タイプ" セクション存在
    check(7, "learner_type_section_exists", "受講者タイプ" in text,
          "受講者タイプセクションがない", "analyze.py の Section 2 を確認")

    # 8: "スコア" セクション存在
    check(8, "score_section_exists", "スコア" in text,
          "スコアセクションがない", "analyze.py の Section 5 を確認")

else:
    for i in range(3, 9):
        results.append({
            "id": i, "name": f"check_{i}", "status": "FAIL",
            "detail": "レポートなし", "fix_hint": "analyze.py を実行",
        })

# 9: CSV行数チェック
if CSV_PATH.exists():
    df_s = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    check(9, "summary_csv_row_count", len(df_s) >= 1,
          f"course_summary_202401.csv 行数: {len(df_s)}", "analyze.py の集計を確認")

    # 10: course_name列が存在する
    check(10, "summary_csv_has_course_name", "course_name" in df_s.columns,
          "course_name列なし", "analyze.py を確認")
else:
    for i in [9, 10]:
        results.append({
            "id": i, "name": f"check_{i}", "status": "FAIL",
            "detail": "CSVなし", "fix_hint": "analyze.py を実行",
        })

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
out = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
RESULT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*52}\n  レポート品質チェック: {passed}/{len(results)} PASS\n{'='*52}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)
print(f"\n  全{len(results)}項目クリア!" if failed == 0 else f"\n  {failed}項目が失敗")
if failed > 0:
    raise SystemExit(1)
