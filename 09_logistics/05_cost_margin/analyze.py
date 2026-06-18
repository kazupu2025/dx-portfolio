# -*- coding: utf-8 -*-
"""配送コスト・利益率分析 -> analysis_report.md + delivery_summary_202401.csv"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUTPUT_DIR / "cleaned_deliveries_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# 1. 配送区分別集計
type_agg = df.groupby("delivery_type").agg(
    avg_profit_margin=("profit_margin", "mean"),
    avg_delivery_charge=("delivery_charge", "mean"),
    total_gross_profit=("gross_profit", "sum"),
    record_count=("delivery_id", "count"),
).reset_index().sort_values("avg_profit_margin", ascending=False)

type_agg["avg_profit_margin"] = type_agg["avg_profit_margin"].round(4)
type_agg["avg_delivery_charge"] = type_agg["avg_delivery_charge"].round(0)
type_agg["total_gross_profit"] = type_agg["total_gross_profit"].round(0)

# 2. エリア別集計
area_agg = df.groupby("area").agg(
    avg_total_cost=("total_cost", "mean"),
    avg_profit_margin=("profit_margin", "mean"),
    total_gross_profit=("gross_profit", "sum"),
    record_count=("delivery_id", "count"),
).reset_index().sort_values("avg_profit_margin", ascending=False)

area_agg["avg_total_cost"] = area_agg["avg_total_cost"].round(0)
area_agg["avg_profit_margin"] = area_agg["avg_profit_margin"].round(4)
area_agg["total_gross_profit"] = area_agg["total_gross_profit"].round(0)

# 3. 車両別km単価集計
vehicle_agg = df.groupby("vehicle_type").agg(
    avg_cost_per_km=("cost_per_km", "mean"),
    avg_profit_margin=("profit_margin", "mean"),
    total_distance=("distance_km", "sum"),
    record_count=("delivery_id", "count"),
).reset_index().sort_values("avg_cost_per_km", ascending=True)

vehicle_agg["avg_cost_per_km"] = vehicle_agg["avg_cost_per_km"].round(2)
vehicle_agg["avg_profit_margin"] = vehicle_agg["avg_profit_margin"].round(4)

# 4. 全体KPI
total_deliveries = len(df)
overall_avg_margin = df["profit_margin"].mean()
overall_total_profit = df["gross_profit"].sum()
overall_avg_cpkm = df["cost_per_km"].mean()
margin_grade_counts = df["margin_grade"].value_counts()

# レポート出力
lines_out = []
lines_out.append("# 配送コスト・利益率分析レポート（2024年1月）\n")
lines_out.append(
    f"分析対象レコード数: {total_deliveries:,}件  |  "
    f"平均利益率: {overall_avg_margin*100:.1f}%  |  "
    f"総粗利: {overall_total_profit:,.0f}円\n"
)

lines_out.append("## 1. 配送区分別利益率・平均配送料・件数\n")
lines_out.append("| 配送区分 | 平均利益率 | 平均配送料(円) | 総粗利(円) | 件数 |")
lines_out.append("|---------|-----------|--------------|-----------|------|")
for _, r in type_agg.iterrows():
    lines_out.append(
        f"| {r['delivery_type']} | {r['avg_profit_margin']*100:.1f}% "
        f"| {r['avg_delivery_charge']:,.0f} "
        f"| {r['total_gross_profit']:,.0f} "
        f"| {r['record_count']} |"
    )
lines_out.append("")

lines_out.append("## 2. エリア別コスト・利益率\n")
lines_out.append("| エリア | 平均総コスト(円) | 平均利益率 | 総粗利(円) | 件数 |")
lines_out.append("|-------|---------------|-----------|-----------|------|")
for _, r in area_agg.iterrows():
    lines_out.append(
        f"| {r['area']} | {r['avg_total_cost']:,.0f} "
        f"| {r['avg_profit_margin']*100:.1f}% "
        f"| {r['total_gross_profit']:,.0f} "
        f"| {r['record_count']} |"
    )
lines_out.append("")

lines_out.append("## 3. 車両タイプ別km単価\n")
lines_out.append("| 車両タイプ | 平均km単価(円/km) | 平均利益率 | 総走行距離(km) | 件数 |")
lines_out.append("|----------|----------------|-----------|--------------|------|")
for _, r in vehicle_agg.iterrows():
    lines_out.append(
        f"| {r['vehicle_type']} | {r['avg_cost_per_km']:.2f} "
        f"| {r['avg_profit_margin']*100:.1f}% "
        f"| {r['total_distance']:,} "
        f"| {r['record_count']} |"
    )
lines_out.append("")

lines_out.append("## 4. 利益グレード分布\n")
lines_out.append("| グレード | 件数 |")
lines_out.append("|---------|------|")
for grade in ["高利益", "普通", "低利益"]:
    count = margin_grade_counts.get(grade, 0)
    lines_out.append(f"| {grade} | {count} |")
lines_out.append("")

lines_out.append("## 5. インサイトと改善示唆\n")
best_type = type_agg.iloc[0]["delivery_type"]
worst_type = type_agg.iloc[-1]["delivery_type"]
best_area = area_agg.iloc[0]["area"]
cheapest_vehicle = vehicle_agg.iloc[0]["vehicle_type"]

lines_out.append(
    f"- 配送区分別では「{best_type}」が最も高い利益率を示し、"
    f"「{worst_type}」の改善が優先課題となる。"
)
lines_out.append(
    f"- エリア別では「{best_area}」の利益率が最も高く、"
    "他エリアとの配送コスト差分を分析してルート最適化を検討すること。"
)
lines_out.append(
    f"- 車両タイプ別では「{cheapest_vehicle}」のkm単価が最も低く、"
    "短距離配送への積極投入が収益改善に寄与する可能性がある。"
)
lines_out.append(
    "- 低利益グレードの配送については、配送料の見直しまたはコスト削減施策の実施を推奨する。"
)
lines_out.append(
    "- 大型配送は燃料費・人件費が高い傾向があるため、積載効率の向上が重要課題である。\n"
)

report_path = OUTPUT_DIR / "analysis_report.md"
report_path.write_text("\n".join(lines_out), encoding="utf-8")
print(f"[OK] レポート出力完了: {report_path}")

# delivery_summary_202401.csv (配送区分別サマリ)
summary_path = OUTPUT_DIR / "delivery_summary_202401.csv"
type_agg.to_csv(summary_path, index=False, encoding="utf-8-sig")
print(f"[OK] サマリCSV出力完了: {summary_path} ({len(type_agg)}行)")
