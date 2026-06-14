import pandas as pd
import numpy as np
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

SIGMA = config.get("sigma_threshold", 3.0)
DEFECT_ALERT = config.get("defect_rate_alert_threshold", 0.05)

df = pd.read_csv("output/cleaned_inspection_202401.csv", encoding="utf-8-sig")
for col in ["inspection_value", "lower_limit", "upper_limit"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
if "is_defect" in df.columns:
    df["is_defect"] = df["is_defect"].astype(bool)

lines = ["# 品質検査データ分析レポート（2024年1月）\n"]

# 1. 工程別不良率サマリー
lines.append("## 1. 工程別不良率サマリー\n")
proc_summary = df.groupby("process").agg(
    検査件数=("is_defect", "count"),
    不良件数=("is_defect", "sum"),
).copy()
proc_summary["不良率(%)"] = (proc_summary["不良件数"] / proc_summary["検査件数"] * 100).round(2)
proc_summary["アラート"] = proc_summary["不良率(%)"].apply(
    lambda x: "⚠ 要対応" if x > DEFECT_ALERT * 100 else "✅ 正常"
)
proc_summary = proc_summary.sort_values("不良率(%)", ascending=False)
lines.append(proc_summary.to_markdown())
lines.append("")

# 2. 異常値アラート（工程別 ±Nσ）
lines.append(f"## 2. 異常値検出（±{SIGMA:.0f}σ）\n")
anomalies = []
sigma_stats = {}
for proc, grp in df.groupby("process"):
    vals = grp["inspection_value"].dropna()
    if len(vals) > 2:
        mu = vals.mean()
        std = vals.std()
        sigma_stats[proc] = (mu, std)
        if std > 0:
            outliers = grp[np.abs(grp["inspection_value"] - mu) > SIGMA * std]
            for _, row in outliers.iterrows():
                date_str = str(row["date"])[:10] if pd.notna(row.get("date")) else "N/A"
                z = (row["inspection_value"] - mu) / std
                anomalies.append(
                    f"- {proc} | {row.get('product_code','?')} | {date_str} | "
                    f"検査値: {row['inspection_value']:.3f}"
                    f"（平均 {mu:.3f}±{std:.3f}、{z:+.1f}σ）"
                )

if anomalies:
    lines.append(f"**{len(anomalies)}件の統計的外れ値を検出:**")
    lines.extend(anomalies[:20])  # 上位20件
    if len(anomalies) > 20:
        lines.append(f"… 他 {len(anomalies)-20} 件")
else:
    lines.append(f"- ±{SIGMA:.0f}σ 外れ値は検出されませんでした")
lines.append("")

# 3. 製品別不良率（上位10製品）
lines.append("## 3. 製品別不良率（上位10）\n")
prod_summary = df.groupby(["product_code", "product_name", "process"]).agg(
    検査件数=("is_defect", "count"),
    不良件数=("is_defect", "sum"),
).copy()
prod_summary["不良率(%)"] = (prod_summary["不良件数"] / prod_summary["検査件数"] * 100).round(2)
prod_summary = prod_summary.sort_values("不良率(%)", ascending=False).head(10)
lines.append(prod_summary.to_markdown())
lines.append("")

# 4. 日次不良率トレンド
lines.append("## 4. 日次不良率トレンド\n")
if "date" in df.columns:
    daily = df.groupby("date").agg(
        検査件数=("is_defect", "count"),
        不良件数=("is_defect", "sum"),
    ).copy()
    daily["不良率(%)"] = (daily["不良件数"] / daily["検査件数"] * 100).round(2)
    peak_date = daily["不良率(%)"].idxmax()
    min_date = daily["不良率(%)"].idxmin()
    lines.append(f"- 月平均不良率: **{daily['不良率(%)'].mean():.2f}%**")
    lines.append(f"- 最悪日: {str(peak_date)[:10]}（{daily.loc[peak_date,'不良率(%)']:.2f}%）")
    lines.append(f"- 最良日: {str(min_date)[:10]}（{daily.loc[min_date,'不良率(%)']:.2f}%）")
lines.append("")

# 5. 検査員別不良検出率
lines.append("## 5. 検査員別不良検出率\n")
if "inspector" in df.columns:
    insp_summary = df.groupby("inspector").agg(
        検査件数=("is_defect", "count"),
        不良検出数=("is_defect", "sum"),
    ).copy()
    insp_summary["検出率(%)"] = (insp_summary["不良検出数"] / insp_summary["検査件数"] * 100).round(2)
    insp_summary = insp_summary.sort_values("検出率(%)", ascending=False)
    lines.append(insp_summary.to_markdown())
lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total = len(df)
total_defects = int(df["is_defect"].sum())
overall_rate = total_defects / total * 100 if total > 0 else 0
worst_proc = proc_summary["不良率(%)"].idxmax() if not proc_summary.empty else "不明"
alert_procs = proc_summary[proc_summary["不良率(%)"] > DEFECT_ALERT * 100]

lines.append(f"- 総検査件数: **{total:,}件**（不良: {total_defects}件、不良率: {overall_rate:.2f}%）")
lines.append(f"- 不良率最高工程: **{worst_proc}**")
lines.append(f"- 統計的外れ値: **{len(anomalies)}件**（±{SIGMA:.0f}σ基準）")
if len(alert_procs) > 0:
    lines.append(f"- **{len(alert_procs)}工程が不良率{DEFECT_ALERT*100:.0f}%超 — 原因分析が必要です**")
else:
    lines.append(f"- 全工程の不良率は{DEFECT_ALERT*100:.0f}%以内で正常範囲")
lines.append("")

Path("output/analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print(f"分析完了: {total}件検査, 不良率 {overall_rate:.2f}%, 異常値 {len(anomalies)}件")
