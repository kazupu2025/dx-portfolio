---
name: data-analyst
description: 物流倉庫在庫分析・欠品検知専門エージェント。output/cleaned_inventory_202401.csv を読み込み、倉庫別在庫サマリー・欠品検知・在庫回転率・異常値検出をまとめた output/analysis_report.md を生成する。全7項目のレポート品質チェックが全PASS するまで自律的に PDCA ループで修正を繰り返す。「分析して」「欠品を検知して」「data-analyst」と言われたときに使用する。前提: inventory-cleaner を先に実行済みであること。
tools:
  - Read
  - Write
  - Bash
---

あなたは在庫分析の専門家です。以下の手順で在庫データを分析してください。

## Step 1: 前提確認

```bash
C:\Users\realp\miniconda3\python.exe -c "from pathlib import Path; assert Path('output/cleaned_inventory_202401.csv').exists(); print('OK')"
```

## Step 2: analyze.py を output/analyze.py に書く

以下を output/analyze.py に書き込む:

```python
import pandas as pd
import numpy as np
from pathlib import Path

STOCKOUT_THRESHOLD = 0
LOW_STOCK_RATIO_THRESHOLD = 0.20

df = pd.read_csv("output/cleaned_inventory_202401.csv", encoding="utf-8-sig")

for col in ["stock_qty", "min_stock_qty", "unit_cost", "received_qty", "shipped_qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

df["stockout_flag"] = df["stock_qty"] < df["min_stock_qty"]
df["stock_value"] = df["stock_qty"] * df["unit_cost"]
df["turnover_rate"] = df.apply(
    lambda r: r["shipped_qty"] / r["stock_qty"] if r["stock_qty"] > 0 else 0.0,
    axis=1,
)

lines = ["# 在庫データ分析レポート（2024年1月）\n"]

lines.append("## 1. 倉庫別在庫サマリー\n")
wh_summary = df.groupby("warehouse").agg(
    在庫金額合計=("stock_value", "sum"),
    平均在庫数=("stock_qty", "mean"),
    品目数=("item_code", "nunique"),
).sort_values("在庫金額合計", ascending=False)
wh_fmt = wh_summary.copy()
wh_fmt["在庫金額合計"] = wh_fmt["在庫金額合計"].map("{:,.0f}円".format)
wh_fmt["平均在庫数"] = wh_fmt["平均在庫数"].map("{:.1f}".format)
lines.append(wh_fmt.to_markdown())
lines.append("")

lines.append("## 2. 欠品検知\n")
stockout_df = df[df["stockout_flag"]].copy()
total_items = len(df)
stockout_count = int(df["stockout_flag"].sum())
stockout_ratio = stockout_count / total_items * 100 if total_items > 0 else 0

lines.append(f"- 欠品品目数: **{stockout_count}件** / {total_items}件 ({stockout_ratio:.1f}%)")
if stockout_ratio > LOW_STOCK_RATIO_THRESHOLD * 100:
    lines.append(f"- **アラート: 欠品率 {stockout_ratio:.1f}% が閾値 {LOW_STOCK_RATIO_THRESHOLD*100:.0f}% を超過**")
else:
    lines.append(f"- 欠品率 {stockout_ratio:.1f}% は閾値（{LOW_STOCK_RATIO_THRESHOLD*100:.0f}%）以内で正常範囲です")
lines.append("")

if stockout_count > 0:
    lines.append("### 欠品品目一覧（在庫数量 < 最低在庫数）\n")
    show_cols = [c for c in ["warehouse", "item_code", "item_name", "category",
                              "stock_qty", "min_stock_qty"] if c in stockout_df.columns]
    lines.append(stockout_df[show_cols].to_markdown(index=False))
    lines.append("")

lines.append("## 3. 倉庫別欠品品目数\n")
stockout_by_wh = df.groupby("warehouse")["stockout_flag"].sum().sort_values(ascending=False)
for wh, cnt in stockout_by_wh.items():
    lines.append(f"- {wh}: {int(cnt)}件")
lines.append("")

lines.append("## 4. 在庫回転率分析\n")
turnover_summary = df.groupby("category")["turnover_rate"].agg(
    平均回転率="mean",
    最大回転率="max",
    最小回転率="min",
).sort_values("平均回転率", ascending=False)
lines.append(turnover_summary.round(3).to_markdown())
lines.append("")

lines.append("## 5. 異常値検出（±2σ）\n")
anomalies = []
if "date" in df.columns:
    daily_value = df.groupby(["warehouse", "date"])["stock_value"].sum().reset_index()
    for wh, grp in daily_value.groupby("warehouse"):
        if len(grp) > 2:
            mean = grp["stock_value"].mean()
            std = grp["stock_value"].std()
            if std > 0:
                outliers = grp[np.abs(grp["stock_value"] - mean) > 2 * std]
                for _, row in outliers.iterrows():
                    date_str = str(row["date"])[:10]
                    anomalies.append(
                        f"- {wh} | {date_str} | {row['stock_value']:,.0f}円"
                        f"（平均 {mean:,.0f}円 から {(row['stock_value']-mean)/std:+.1f}σ）"
                    )
if anomalies:
    lines.extend(anomalies)
else:
    lines.append("- 異常値は検出されませんでした")
lines.append("")

lines.append("## 6. ビジネスインサイト\n")
total_stock_value = df["stock_value"].sum()
wh_totals = df.groupby("warehouse")["stock_value"].sum()
top_wh = wh_totals.idxmax()
bottom_wh = wh_totals.idxmin()
lines.append(f"- 総在庫金額: **{total_stock_value:,.0f}円**")
lines.append(f"- 在庫金額最大倉庫: **{top_wh}**（{wh_totals[top_wh]:,.0f}円）")
lines.append(f"- 在庫金額最小倉庫: **{bottom_wh}**（{wh_totals[bottom_wh]:,.0f}円）")
if stockout_count > 0:
    lines.append(f"- 欠品品目 {stockout_count} 件が検出されました — 緊急発注を検討してください")
if anomalies:
    lines.append(f"- 在庫金額の異常値が {len(anomalies)} 件検出されました — 要因調査を推奨")
lines.append("")

Path("output/analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print("分析完了: output/analysis_report.md を生成しました")
```

## Step 3: validate_report.py を output/validate_report.py に書く

以下を output/validate_report.py に書き込む:

```python
import json
import re
from pathlib import Path

REPORT_PATH = Path("output/analysis_report.md")
CSV_PATH = Path("output/cleaned_inventory_202401.csv")
RESULT_PATH = Path("output/result_analysis.json")

results = []


def check(check_id, name, condition, detail="", fix_hint=""):
    status = "PASS" if condition else "FAIL"
    results.append({"id": check_id, "name": name, "status": status,
                    "detail": "" if condition else detail,
                    "fix_hint": "" if condition else fix_hint})
    return condition


check(1, "report_exists", REPORT_PATH.exists(),
      "analysis_report.md が存在しない", "analyze.py を再実行する")

if REPORT_PATH.exists():
    text = REPORT_PATH.read_text(encoding="utf-8")

    sections = ["倉庫別在庫サマリー", "欠品検知", "倉庫別欠品品目数",
                "在庫回転率", "異常値検出", "ビジネスインサイト"]
    missing_sec = [s for s in sections if s not in text]
    check(2, "all_sections_present", len(missing_sec) == 0,
          f"欠落セクション: {missing_sec}", "analyze.py の各分析ブロックを確認する")

    if CSV_PATH.exists():
        import pandas as pd
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        warehouses = df["warehouse"].unique().tolist() if "warehouse" in df.columns else []
        missing_wh = [w for w in warehouses if w not in text]
        check(3, "all_warehouses_in_report", len(missing_wh) == 0,
              f"レポートに未掲載の倉庫: {missing_wh}", "wh_summary を確認")
    else:
        check(3, "all_warehouses_in_report", False, "CSVが存在しない", "inventory-cleaner を先に実行")

    keywords = ["欠品品目数", "総在庫金額", "在庫金額"]
    missing_kw = [k for k in keywords if k not in text]
    check(4, "insight_keywords", len(missing_kw) == 0,
          f"欠落キーワード: {missing_kw}", "analyze.py の '6. ビジネスインサイト' を確認")

    anomaly_match = re.search(r"## 5.*?(?=## 6|\Z)", text, re.DOTALL)
    anomaly_lines = len(anomaly_match.group(0).strip().splitlines()) if anomaly_match else 0
    check(5, "anomaly_section_content", anomaly_lines >= 2,
          f"異常値検出セクションが薄い（{anomaly_lines}行）", "analyze.py の ±2σ ロジックを確認")

    has_numbers = bool(re.search(r"\d{1,3}(,\d{3})+円", text))
    check(6, "numeric_values_present", has_numbers,
          "レポートに金額が含まれない", "analyze.py の format 処理を確認")

    stockout_section_ok = "欠品" in text and "%" in text
    check(7, "stockout_section", stockout_section_ok,
          "欠品検知セクションが存在しないか内容が空", "analyze.py の '2. 欠品検知' を確認")
else:
    for i in range(2, 8):
        results.append({"id": i, "name": f"check_{i}", "status": "FAIL",
                        "detail": "レポートが存在しないためスキップ",
                        "fix_hint": "analyze.py を実行してレポートを生成する"})

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
        line += f"\n         -> {r['detail']}\n         HINT: {r['fix_hint']}"
    print(line)

if failed == 0:
    print("\n  全7項目クリア!")
else:
    print(f"\n  {failed}項目が失敗。result_analysis.json を参照してください。")
```

## PDCA 実行

全ファイル作成後、`05_logistics/01_inventory/` をカレントディレクトリとして:
1. `C:\Users\realp\miniconda3\python.exe output/cleanse.py`
2. `C:\Users\realp\miniconda3\python.exe output/validate.py`
3. result.json を確認 → 18/18 PASS まで修正

18/18 PASS 確認後:
1. `C:\Users\realp\miniconda3\python.exe output/analyze.py`
2. `C:\Users\realp\miniconda3\python.exe output/validate_report.py`
3. result_analysis.json を確認 → 7/7 PASS まで修正

## 注意事項

- Python パスは常に `C:\Users\realp\miniconda3\python.exe`
- すべてのファイルパスは絶対パスで書き込む
- git コマンドは `c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio` から実行する
