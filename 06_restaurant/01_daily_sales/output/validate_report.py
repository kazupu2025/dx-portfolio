"""
レポート品質チェックリスト（7項目）- 飲食業 A-02 版
"""
import json
import re
from pathlib import Path

REPORT_PATH = Path("output/analysis_report.md")
CSV_PATH = Path("output/cleaned_sales_202401.csv")
RESULT_PATH = Path("output/result_analysis.json")

results = []


def check(check_id, name, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({
        "id": check_id, "name": name, "status": status,
        "detail": "" if condition else detail,
        "fix_hint": "" if condition else fix_hint,
    })
    return condition


check(1, "report_exists", REPORT_PATH.exists(),
      "analysis_report.md が存在しない",
      "analyze.py を再実行する")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    sections = ["店舗別サマリー", "月間売上ランキング", "日次トレンド",
                "異常値検出", "ビジネスインサイト", "廃棄ロス率分析"]
    missing_sec = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing_sec) == 0,
          f"欠落セクション: {missing_sec}",
          "analyze.py の各分析ブロック（## N. セクション名）を確認する")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        stores = df["store_name"].unique().tolist() if "store_name" in df.columns else []
        missing_stores = [s for s in stores if s not in text]
        check(3, "all_stores_in_report", len(missing_stores) == 0,
              f"レポートに未掲載の店舗: {missing_stores}",
              "store_summary / ranking の groupby('store_name') を確認")
    else:
        check(3, "all_stores_in_report", False,
              "cleaned_sales_202401.csv が存在しない",
              "sales-cleaner を先に実行する")

    keywords = ["全店舗", "トップ店舗", "ボトム店舗"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0,
          f"インサイトセクションに欠落キーワード: {missing_kw}",
          "analyze.py の '5. ビジネスインサイト' セクションを確認")

    anomaly_match = re.search(r"## 4.*?(?=## 5|\Z)", text, re.DOTALL)
    anomaly_lines = len(anomaly_match.group(0).strip().splitlines()) if anomaly_match else 0
    check(5, "anomaly_section_content", anomaly_lines >= 3,
          f"異常値検出セクションが薄い（{anomaly_lines}行）",
          "analyze.py の ±2σ 異常値検出ロジックを確認")

    has_numbers = bool(re.search(r"\d{1,3}(,\d{3})+円", text))
    check(6, "numeric_values_present", has_numbers,
          "レポートに金額（例: 1,234,567円）が含まれない",
          "analyze.py の format 処理（{:,.0f}円）を確認")

    waste_section_ok = "廃棄ロス率" in text and "%" in text
    check(7, "waste_loss_section", waste_section_ok,
          "廃棄ロス率セクションが存在しないか内容が空",
          "analyze.py の '6. 廃棄ロス率分析' セクションを確認")

else:
    for i in range(2, 8):
        results.append({
            "id": i, "name": f"check_{i}", "status": "FAIL",
            "detail": "レポートが存在しないためスキップ",
            "fix_hint": "analyze.py を実行してレポートを生成する",
        })

passed = sum(1 for r in results if r["status"] == "PASS")
failed = len(results) - passed
output = {"passed": passed, "failed": failed, "all_passed": failed == 0, "results": results}
RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'='*48}")
print(f"  レポート品質チェック: {passed}/{len(results)} PASS")
print(f"{'='*48}")
for r in results:
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    line = f"  [{icon}] #{r['id']:02d} {r['name']}"
    if r["detail"]:
        line += f"\n         -> {r['detail']}"
        line += f"\n         HINT: {r['fix_hint']}"
    print(line)

if failed == 0:
    print("\n  全7項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。result_analysis.json の fix_hint を参照してください。")
