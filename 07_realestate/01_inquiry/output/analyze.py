import pandas as pd
import numpy as np
from pathlib import Path
import yaml

BASE = Path(__file__).parent.parent
CONFIG_PATH = BASE / "config.yml"
with open(CONFIG_PATH, encoding="utf-8") as f:
    config = yaml.safe_load(f)

CONV_ALERT = config.get("conversion_alert_threshold", 0.10)
STAGES = config.get("stages", ["問い合わせ", "内見", "申し込み", "成約"])

OUTPUT_DIR = Path(__file__).parent
df = pd.read_csv(OUTPUT_DIR / "cleaned_inquiry_202401.csv", encoding="utf-8-sig")
for col in ["is_contracted", "contract_amount"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

lines = ["# 物件問い合わせ・成約率分析レポート（2024年1月）\n"]

# 1. ファネル分析
lines.append("## 1. ファネル分析（問い合わせ → 成約）\n")
total = len(df)
stage_counts = {}
for stage in STAGES:
    stage_idx = STAGES.index(stage)
    reached = df[df["status"].isin(STAGES[stage_idx:])].shape[0]
    stage_counts[stage] = reached

funnel_rows = []
for i, stage in enumerate(STAGES):
    cnt = stage_counts[stage]
    rate_from_top = cnt / total * 100 if total > 0 else 0
    if i == 0:
        stage_conv = 100.0
    else:
        prev = stage_counts[STAGES[i-1]]
        stage_conv = cnt / prev * 100 if prev > 0 else 0
    funnel_rows.append({
        "ステージ": stage, "件数": cnt,
        "全体比(%)": round(rate_from_top, 1),
        "前段階転換率(%)": round(stage_conv, 1),
    })

funnel_df = pd.DataFrame(funnel_rows)
lines.append(funnel_df.to_markdown(index=False))
lines.append(f"\n- 総問い合わせ数: **{total}件**")
lines.append(f"- 最終成約件数: **{stage_counts.get('成約', 0)}件**")
lines.append(f"- 総合成約率: **{stage_counts.get('成約', 0)/total*100:.1f}%**")
lines.append("")

# 2. エリア別成約率
lines.append("## 2. エリア別成約率\n")
area_summary = df.groupby("area").agg(
    問い合わせ数=("inquiry_id", "count"),
    成約数=("is_contracted", "sum"),
    成約金額合計=("contract_amount", "sum"),
).copy()
area_summary["成約率(%)"] = (area_summary["成約数"] / area_summary["問い合わせ数"] * 100).round(1)
area_summary["平均成約金額(万円)"] = (
    area_summary["成約金額合計"] / area_summary["成約数"].replace(0, 1)
).round(0)
area_summary["アラート"] = area_summary["成約率(%)"].apply(
    lambda x: "⚠ 低成約率" if x < CONV_ALERT * 100 else "✅ 正常"
)
area_summary = area_summary.sort_values("成約率(%)", ascending=False)
fmt = area_summary.copy()
fmt["成約金額合計"] = fmt["成約金額合計"].map("{:,.0f}万円".format)
fmt["平均成約金額(万円)"] = fmt["平均成約金額(万円)"].map("{:,.0f}万円".format)
lines.append(fmt.to_markdown())
lines.append("")

# 3. 担当者別成約率
lines.append("## 3. 担当者別成約率\n")
agent_summary = df.groupby("agent").agg(
    問い合わせ数=("inquiry_id", "count"),
    成約数=("is_contracted", "sum"),
    成約金額合計=("contract_amount", "sum"),
).copy()
agent_summary["成約率(%)"] = (agent_summary["成約数"] / agent_summary["問い合わせ数"] * 100).round(1)
agent_summary = agent_summary.sort_values("成約率(%)", ascending=False)
lines.append(agent_summary.to_markdown())
lines.append("")

# 4. 経路別分析
lines.append("## 4. 問い合わせ経路別分析\n")
channel_summary = df.groupby("channel").agg(
    問い合わせ数=("inquiry_id", "count"),
    成約数=("is_contracted", "sum"),
).copy()
channel_summary["成約率(%)"] = (channel_summary["成約数"] / channel_summary["問い合わせ数"] * 100).round(1)
channel_summary["構成比(%)"] = (channel_summary["問い合わせ数"] / total * 100).round(1)
channel_summary = channel_summary.sort_values("問い合わせ数", ascending=False)
lines.append(channel_summary.to_markdown())
lines.append("")

# 5. 物件種別分析
lines.append("## 5. 物件種別成約率\n")
prop_summary = df.groupby("property_type").agg(
    問い合わせ数=("inquiry_id", "count"),
    成約数=("is_contracted", "sum"),
).copy()
prop_summary["成約率(%)"] = (prop_summary["成約数"] / prop_summary["問い合わせ数"] * 100).round(1)
prop_summary = prop_summary.sort_values("成約率(%)", ascending=False)
lines.append(prop_summary.to_markdown())
lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total_contracts = int(df["is_contracted"].sum())
total_revenue = df["contract_amount"].sum()
overall_conv = total_contracts / total * 100 if total > 0 else 0
best_area = area_summary["成約率(%)"].idxmax() if not area_summary.empty else "不明"
best_agent = agent_summary["成約率(%)"].idxmax() if not agent_summary.empty else "不明"
best_channel = channel_summary.nlargest(1, "成約率(%)").index[0] if not channel_summary.empty else "不明"
low_areas = area_summary[area_summary["成約率(%)"] < CONV_ALERT * 100]

lines.append(f"- 総問い合わせ: **{total}件** → 成約: **{total_contracts}件**（成約率: {overall_conv:.1f}%）")
lines.append(f"- 総成約金額: **{total_revenue:,.0f}万円**")
lines.append(f"- 成約率最高エリア: **{best_area}**（{area_summary.loc[best_area,'成約率(%)']:.1f}%）")
lines.append(f"- 成約率最高担当者: **{best_agent}**（{agent_summary.loc[best_agent,'成約率(%)']:.1f}%）")
lines.append(f"- 成約率最高経路: **{best_channel}**（{channel_summary.loc[best_channel,'成約率(%)']:.1f}%）")
if len(low_areas) > 0:
    lines.append(f"- **{len(low_areas)}エリアが成約率{CONV_ALERT*100:.0f}%未満 — アプローチ改善が必要です**")
lines.append("")

(OUTPUT_DIR / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print(f"分析完了: {total}件, 成約率 {overall_conv:.1f}%, 総成約金額 {total_revenue:,.0f}万円")
