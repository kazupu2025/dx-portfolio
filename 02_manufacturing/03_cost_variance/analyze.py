"""原価差異分析 → analysis_report.md + variance_summary_202401.csv"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_production_cost_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# ── 1. ライン別原価差異 ──
line_var = df.groupby("line_id")[["material_variance","labor_variance","overhead_variance","total_variance"]].sum().reset_index()
line_var["total_variance_M"] = line_var["total_variance"] / 1_000_000

# ── 2. 製品別コスト超過率ランキング ──
prod_var = df.groupby(["product_id","product_name"]).agg(
    avg_variance_ratio=("variance_ratio","mean"),
    total_variance=("total_variance","sum"),
    planned_total=("planned_total_cost","sum"),
).reset_index()
prod_var = prod_var.sort_values("avg_variance_ratio", ascending=False)
top10 = prod_var.head(10)

# ── 3. 差異フラグ分布 ──
flag_dist = df["variance_flag"].value_counts().reset_index()
flag_dist.columns = ["variance_flag","count"]
flag_dist["pct"] = (flag_dist["count"] / len(df) * 100).round(1)

# ── 4. 月間総コスト ──
total_planned = df["planned_total_cost"].sum()
total_actual = df["actual_total_cost"].sum()
total_var_amt = total_actual - total_planned
total_var_pct = total_var_amt / total_planned * 100

# ── 5. 主因分析 ──
mat_var_total = df["material_variance"].sum()
lab_var_total = df["labor_variance"].sum()
ohd_var_total = df["overhead_variance"].sum()
abs_total = abs(mat_var_total) + abs(lab_var_total) + abs(ohd_var_total)
main_cause = max([("材料費", mat_var_total),("労務費", lab_var_total),("間接費", ohd_var_total)], key=lambda x: abs(x[1]))

# ── レポート出力 ──
lines = []
lines.append("# 原価差異分析レポート（2024年1月）\n")
lines.append(f"分析対象レコード数: {len(df):,}件\n")

lines.append("## 1. 月間総コスト差異\n")
lines.append(f"| 項目 | 金額 |")
lines.append(f"|------|------|")
lines.append(f"| 計画総コスト | ¥{total_planned:,.0f} |")
lines.append(f"| 実績総コスト | ¥{total_actual:,.0f} |")
lines.append(f"| 差異額 | ¥{total_var_amt:,.0f} |")
lines.append(f"| 差異率 | {total_var_pct:.2f}% |\n")

lines.append("## 2. ライン別原価差異（材料費・労務費・間接費）\n")
lines.append("| ライン | 材料費差異 | 労務費差異 | 間接費差異 | 合計差異 |")
lines.append("|--------|-----------|-----------|-----------|---------|")
for _, r in line_var.iterrows():
    lines.append(f"| {r['line_id']} | ¥{r['material_variance']:,.0f} | ¥{r['labor_variance']:,.0f} | ¥{r['overhead_variance']:,.0f} | ¥{r['total_variance']:,.0f} |")
lines.append("")

lines.append("## 3. 製品別コスト超過率ランキング（上位10製品）\n")
lines.append("| 順位 | 製品ID | 製品名 | 平均差異率 | 合計差異額 |")
lines.append("|------|--------|--------|-----------|-----------|")
for i, (_, r) in enumerate(top10.iterrows(), 1):
    lines.append(f"| {i} | {r['product_id']} | {r['product_name']} | {r['avg_variance_ratio']*100:.2f}% | ¥{r['total_variance']:,.0f} |")
lines.append("")

lines.append("## 4. 差異フラグ分布\n")
lines.append("| フラグ | 件数 | 割合 |")
lines.append("|--------|------|------|")
for _, r in flag_dist.iterrows():
    lines.append(f"| {r['variance_flag']} | {r['count']:,}件 | {r['pct']}% |")
lines.append("")

lines.append("## 5. コスト超過の主因分析\n")
lines.append(f"| 費目 | 差異額合計 |")
lines.append(f"|------|-----------|")
lines.append(f"| 材料費 | ¥{mat_var_total:,.0f} |")
lines.append(f"| 労務費 | ¥{lab_var_total:,.0f} |")
lines.append(f"| 間接費 | ¥{ohd_var_total:,.0f} |")
lines.append(f"\n**主因: {main_cause[0]}差異が最大（¥{main_cause[1]:,.0f}）**\n")

lines.append("## 6. インサイトと改善提案\n")
lines.append("- 差異率が10%を超える製品については、個別原価計算の精度向上と計画見直しが必要。")
lines.append("- 材料費差異が最大の場合は、仕入先との価格交渉または代替材料の検討を推奨する。")
lines.append("- ラインごとの差異分布を確認し、特定ラインへの設備投資・人員配置最適化を検討すること。")
lines.append("- 数量差異（実績数量 < 計画数量）のケースは不良品率または設備稼働率の低下が疑われる。")
lines.append("- 月次でのPDCAサイクルを回し、差異原因を早期に特定・是正することが重要。\n")

report_path = OUTPUT_DIR / "analysis_report.md"
report_path.write_text("\n".join(lines), encoding="utf-8")
print(f"レポート出力完了: {report_path}")

# variance_summary_202401.csv
summary = df.groupby(["product_id","product_name","line_id"]).agg(
    avg_variance_ratio=("variance_ratio","mean"),
    total_variance=("total_variance","sum"),
    variance_flag_最頻値=("variance_flag", lambda x: x.mode()[0] if len(x) > 0 else "正常"),
).reset_index()
summary_path = OUTPUT_DIR / "variance_summary_202401.csv"
summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
print(f"サマリCSV出力完了: {summary_path} ({len(summary)}行)")
