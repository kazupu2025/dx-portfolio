"""
B-15 分析スクリプト
- カテゴリ別サマリー
- 担当者別パフォーマンス
- チャネル別分析
- 対応時間アラート
- 時間帯別受付傾向
- ビジネスインサイト
"""
import sys
from pathlib import Path
import pandas as pd
import yaml

BASE = Path(__file__).resolve().parent.parent
OUT  = Path(__file__).resolve().parent
CFG_PATH = BASE / "config.yml"
CSV_PATH = OUT / "cleaned_inquiry_202401.csv"
RPT_PATH = OUT / "analysis_report.md"

with open(CFG_PATH, encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

if not CSV_PATH.exists():
    print(f"ERROR: {CSV_PATH} が見つかりません。cleanse.py を先に実行してください。")
    sys.exit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["received_at"] = pd.to_datetime(df["received_at"], format="%Y-%m-%d %H:%M", errors="coerce")
df["response_minutes"] = pd.to_numeric(df["response_minutes"], errors="coerce")
df["is_resolved"]  = df["is_resolved"].astype(int)
df["is_escalated"] = df["is_escalated"].astype(int)

total = len(df)
alert_minutes = cfg["response_time_alert_minutes"]
resolution_alert = cfg["resolution_rate_alert"]

lines = []

def h2(title: str):
    lines.append(f"\n## {title}\n")

def h3(title: str):
    lines.append(f"\n### {title}\n")

lines.append("# B-15 問い合わせログ分析レポート\n")
lines.append(f"**分析対象期間:** 2024年1月  \n**総問い合わせ件数:** {total}件\n")

# 全体サマリー
overall_resolution_rate = df["is_resolved"].mean() * 100
overall_escalation_rate = df["is_escalated"].mean() * 100
avg_response = df["response_minutes"].mean()
lines.append(f"**全体解決率:** {overall_resolution_rate:.1f}%  \n")
lines.append(f"**エスカレ率:** {overall_escalation_rate:.1f}%  \n")
lines.append(f"**平均対応時間:** {avg_response:.1f}分\n")

# 1. カテゴリ別問い合わせサマリー
h2("カテゴリ別問い合わせサマリー")
cat_grp = df.groupby("category").agg(
    件数=("inquiry_id", "count"),
    平均対応時間=("response_minutes", "mean"),
    解決率=("is_resolved", "mean"),
    エスカレ率=("is_escalated", "mean"),
).reset_index()
cat_grp["割合(%)"] = (cat_grp["件数"] / total * 100).round(1)
cat_grp["平均対応時間"] = cat_grp["平均対応時間"].round(1)
cat_grp["解決率(%)"] = (cat_grp["解決率"] * 100).round(1)
cat_grp["エスカレ率(%)"] = (cat_grp["エスカレ率"] * 100).round(1)
cat_grp = cat_grp.sort_values("件数", ascending=False)

lines.append("| カテゴリ | 件数 | 割合(%) | 平均対応時間(分) | 解決率(%) | エスカレ率(%) |")
lines.append("|---------|------|--------|----------------|----------|-------------|")
for _, r in cat_grp.iterrows():
    lines.append(f"| {r['category']} | {r['件数']} | {r['割合(%)']} | {r['平均対応時間']} | {r['解決率(%)']} | {r['エスカレ率(%)']} |")

# 2. 担当者別パフォーマンス
h2("担当者別パフォーマンス")
op_grp = df.groupby(["operator_id", "operator_name"]).agg(
    担当件数=("inquiry_id", "count"),
    平均対応時間=("response_minutes", "mean"),
    解決率=("is_resolved", "mean"),
    エスカレ率=("is_escalated", "mean"),
).reset_index()
op_grp["平均対応時間(分)"] = op_grp["平均対応時間"].round(1)
op_grp["解決率(%)"] = (op_grp["解決率"] * 100).round(1)
op_grp["エスカレ率(%)"] = (op_grp["エスカレ率"] * 100).round(1)
op_grp = op_grp.sort_values("operator_id")

lines.append("| 担当者ID | 担当者名 | 担当件数 | 平均対応時間(分) | 解決率(%) | エスカレ率(%) |")
lines.append("|---------|--------|--------|----------------|----------|-------------|")
for _, r in op_grp.iterrows():
    flag = " ⚠" if r["解決率(%)"] < resolution_alert * 100 else ""
    lines.append(f"| {r['operator_id']} | {r['operator_name']} | {r['担当件数']} | {r['平均対応時間(分)']} | {r['解決率(%)']} {flag}| {r['エスカレ率(%)']} |")

# 3. チャネル別分析
h2("チャネル別分析")
ch_grp = df.groupby("channel").agg(
    件数=("inquiry_id", "count"),
    平均対応時間=("response_minutes", "mean"),
).reset_index()
ch_grp["割合(%)"] = (ch_grp["件数"] / total * 100).round(1)
ch_grp["平均対応時間(分)"] = ch_grp["平均対応時間"].round(1)
ch_grp = ch_grp.sort_values("件数", ascending=False)

lines.append("| チャネル | 件数 | 割合(%) | 平均対応時間(分) |")
lines.append("|--------|------|--------|----------------|")
for _, r in ch_grp.iterrows():
    lines.append(f"| {r['channel']} | {r['件数']} | {r['割合(%)']} | {r['平均対応時間(分)']} |")

# 4. 対応時間アラート
h2("対応時間アラート（長時間対応分析）")
alert_df = df[df["response_minutes"] > alert_minutes]
alert_count = len(alert_df)
alert_rate  = alert_count / total * 100
lines.append(f"**アラート基準:** {alert_minutes}分超  \n")
lines.append(f"**長時間対応件数:** {alert_count}件 ({alert_rate:.1f}%)  \n")
lines.append(f"**最大対応時間:** {df['response_minutes'].max():.0f}分  \n")
lines.append(f"**中央値:** {df['response_minutes'].median():.0f}分\n")

if alert_count > 0:
    alert_by_cat = alert_df.groupby("category")["inquiry_id"].count().sort_values(ascending=False)
    lines.append("\n**要改善カテゴリ別内訳（長時間対応）:**\n")
    for cat, cnt in alert_by_cat.items():
        lines.append(f"- {cat}: {cnt}件")

# 5. 時間帯別受付傾向
h2("時間帯別受付傾向")
df["hour"] = df["received_at"].dt.hour
hour_grp = df.groupby("hour")["inquiry_id"].count().reindex(range(9, 18), fill_value=0)
peak_hour = int(hour_grp.idxmax())
lines.append(f"**ピーク時間帯:** {peak_hour}時 ({hour_grp[peak_hour]}件)\n")
lines.append("\n| 時間帯 | 問い合わせ件数 |")
lines.append("|-------|------------|")
for h, cnt in hour_grp.items():
    peak_mark = " ← ピーク" if h == peak_hour else ""
    lines.append(f"| {h}時 | {cnt}{peak_mark} |")

# 6. ビジネスインサイト
h2("ビジネスインサイト・改善提案")

# 解決率が低いカテゴリ
low_res = cat_grp[cat_grp["解決率(%)"] < resolution_alert * 100].sort_values("解決率(%)")
if not low_res.empty:
    h3("解決率が低いカテゴリ（要改善）")
    for _, r in low_res.iterrows():
        lines.append(f"- **{r['category']}**: 解決率 {r['解決率(%)']}% — 対応フローの見直しが必要")

# 対応時間が長い担当者
long_op = op_grp[op_grp["平均対応時間(分)"] > avg_response * 1.2].sort_values("平均対応時間(分)", ascending=False)
if not long_op.empty:
    h3("平均対応時間が長い担当者（サポート検討）")
    for _, r in long_op.iterrows():
        lines.append(f"- **{r['operator_id']} {r['operator_name']}**: 平均 {r['平均対応時間(分)']}分 (全体平均 {avg_response:.1f}分)")

# エスカレ率が高いカテゴリ
high_esc = cat_grp[cat_grp["エスカレ率(%)"] > cfg["escalation_rate_alert"] * 100].sort_values("エスカレ率(%)", ascending=False)
if not high_esc.empty:
    h3("エスカレ率が高いカテゴリ")
    for _, r in high_esc.iterrows():
        lines.append(f"- **{r['category']}**: エスカレ率 {r['エスカレ率(%)']}% — 一次対応スキル強化が必要")

h3("総合提言")
lines.append(f"1. 長時間対応（{alert_minutes}分超）が全体の **{alert_rate:.1f}%** を占める。対応時間短縮に向けたFAQ整備を推奨。")
lines.append(f"2. ピーク時間帯 **{peak_hour}時** の人員配置を強化し、平均対応時間 {avg_response:.1f}分 の削減を目指す。")
lines.append(f"3. 解決率 {overall_resolution_rate:.1f}% を {resolution_alert*100:.0f}% 以上に引き上げるため、担当者トレーニングの実施を検討する。")

# レポート出力
with open(RPT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"分析レポート出力: {RPT_PATH}")
print(f"総問い合わせ: {total}件")
print(f"解決率: {overall_resolution_rate:.1f}%")
print(f"エスカレ率: {overall_escalation_rate:.1f}%")
print(f"平均対応時間: {avg_response:.1f}分")
