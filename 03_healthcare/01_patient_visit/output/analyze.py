import pandas as pd
import numpy as np
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent

with open(BASE_DIR / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

PEAK_THRESHOLD = config.get("peak_hour_threshold", 1.5)
WAIT_ALERT = config.get("wait_alert_minutes", 60)

df = pd.read_csv(OUTPUT_DIR / "cleaned_visit_202401.csv", encoding="utf-8-sig")
for col in ["wait_minutes", "hour_slot"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
if "is_long_wait" in df.columns:
    df["is_long_wait"] = df["is_long_wait"].astype(bool)

lines = ["# 患者来院データ分析レポート（2024年1月）\n"]

# 1. 時間帯別来院数
lines.append("## 1. 時間帯別来院数\n")
hour_counts = df.groupby("hour_slot").size().reindex(range(9, 18), fill_value=0)
avg = hour_counts.mean()
peak_hours = hour_counts[hour_counts > avg * PEAK_THRESHOLD].index.tolist()
hourly_tbl = hour_counts.reset_index()
hourly_tbl.columns = ["時間帯", "来院数"]
hourly_tbl["ピーク"] = hourly_tbl["時間帯"].apply(lambda h: "ピーク" if h in peak_hours else "")
lines.append(hourly_tbl.to_markdown(index=False))
lines.append(f"\n- 全体平均: {avg:.1f}件/時")
lines.append(f"- ピーク時間帯（平均×{PEAK_THRESHOLD}倍超）: {[f'{h}時台' for h in peak_hours]}")
lines.append("")

# 2. 曜日別来院数
lines.append("## 2. 曜日別来院数\n")
WEEKDAY_ORDER = ["月", "火", "水", "木", "金", "土", "日"]
if "weekday" in df.columns:
    wd_counts = df.groupby("weekday").size()
    wd_sorted = wd_counts.reindex([w for w in WEEKDAY_ORDER if w in wd_counts.index])
    wd_tbl = wd_sorted.reset_index()
    wd_tbl.columns = ["曜日", "来院数"]
    lines.append(wd_tbl.to_markdown(index=False))
    peak_wd = wd_sorted.idxmax()
    lines.append(f"\n- 来院数最多曜日: **{peak_wd}曜日**（{wd_sorted.max()}件）")
lines.append("")

# 3. 診療科別サマリー
lines.append("## 3. 診療科別来院サマリー\n")
dept_summary = df.groupby("department").agg(
    来院数=("patient_id", "count"),
    平均待ち時間=("wait_minutes", "mean"),
    長時間待ち件数=("is_long_wait", "sum"),
).round(1).sort_values("来院数", ascending=False)
dept_summary["長時間待ち率(%)"] = (
    dept_summary["長時間待ち件数"] / dept_summary["来院数"] * 100
).round(1)
dept_summary["アラート"] = dept_summary["平均待ち時間"].apply(
    lambda x: "要改善" if x > WAIT_ALERT else "正常"
)
lines.append(dept_summary.to_markdown())
lines.append("")

# 4. 曜日×時間帯 来院数マトリクス
lines.append("## 4. 曜日×時間帯 来院数マトリクス（上位ピーク）\n")
if "weekday" in df.columns and "hour_slot" in df.columns:
    pivot = df.groupby(["weekday", "hour_slot"]).size().unstack(fill_value=0)
    pivot = pivot.reindex([w for w in WEEKDAY_ORDER if w in pivot.index])
    # ピーク上位5セルを抽出
    flat = pivot.stack().sort_values(ascending=False).head(5)
    lines.append("**来院集中 TOP5（曜日×時間帯）:**")
    for (wd, h), cnt in flat.items():
        lines.append(f"- {wd}曜日 {h}時台: {cnt}件")
lines.append("")

# 5. 長時間待ち分析
lines.append("## 5. 長時間待ち分析\n")
long_wait_df = df[df["is_long_wait"]]
total_long = len(long_wait_df)
long_rate = total_long / len(df) * 100 if len(df) > 0 else 0
lines.append(f"- 長時間待ち件数: **{total_long}件**（全体の{long_rate:.1f}%）")
if total_long > 0 and "department" in long_wait_df.columns:
    by_dept = long_wait_df.groupby("department").size().sort_values(ascending=False)
    lines.append(f"- 長時間待ち最多診療科: **{by_dept.index[0]}**（{by_dept.iloc[0]}件）")
    if "hour_slot" in long_wait_df.columns:
        by_hour = long_wait_df.groupby("hour_slot").size().sort_values(ascending=False)
        lines.append(f"- 長時間待ち最多時間帯: **{by_hour.index[0]}時台**（{by_hour.iloc[0]}件）")
lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total_visits = len(df)
avg_wait = df["wait_minutes"].mean()
busiest_dept = dept_summary["来院数"].idxmax() if not dept_summary.empty else "不明"
lines.append(f"- 月次総来院数: **{total_visits:,}件**")
lines.append(f"- 平均待ち時間: **{avg_wait:.1f}分**")
lines.append(f"- 最多来院診療科: **{busiest_dept}**")
lines.append(f"- ピーク時間帯: **{[f'{h}時台' for h in peak_hours]}**")
lines.append(f"- 長時間待ち（{WAIT_ALERT}分超）: **{total_long}件**（{long_rate:.1f}%）")
if peak_hours:
    lines.append(f"- ピーク時間帯に受付スタッフを重点配置することで待ち時間短縮が期待できます")
lines.append("")

(OUTPUT_DIR / "analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print(f"分析完了: {total_visits}件来院, 平均待ち {avg_wait:.1f}分, ピーク: {peak_hours}")
