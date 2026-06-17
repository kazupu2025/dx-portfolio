# -*- coding: utf-8 -*-
"""
C-52: 保険契約問い合わせ・対応履歴分析パイプライン 分析スクリプト
問い合わせ区分別/チャネル別/オペレーター別の分析結果を出力する。
print文にバックスラッシュY記号・絵文字・em-dash を使わないこと。
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_inquiries_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
TYPE_CSV_PATH = OUTPUT_DIR / "type_summary_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["handling_minutes", "is_resolved", "recontact_flag", "satisfaction"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

if "inquiry_date" in df.columns:
    df["inquiry_date"] = pd.to_datetime(df["inquiry_date"], errors="coerce")

lines = ["# 保険問い合わせ・対応履歴分析レポート（2024年1月）\n"]

# ===== 1. 全体サマリー =====
lines.append("## 1. 全体サマリー\n")

total_rows = len(df)
resolution_rate = df["is_resolved"].mean() * 100 if "is_resolved" in df.columns else 0
recontact_rate = df["recontact_flag"].mean() * 100 if "recontact_flag" in df.columns else 0
avg_minutes = df["handling_minutes"].mean() if "handling_minutes" in df.columns else 0
avg_satisfaction = df["satisfaction"].mean() if "satisfaction" in df.columns else 0

lines.append(f"- 総問い合わせ件数: **{total_rows:,} 件**")
lines.append(f"- 解決率: **{resolution_rate:.1f}%**")
lines.append(f"- 再問い合わせ率: **{recontact_rate:.1f}%**")
lines.append(f"- 平均対応時間: **{avg_minutes:.1f} 分**")
lines.append(f"- 平均満足度: **{avg_satisfaction:.2f} 点** (5点満点)")
lines.append("")

# ===== 2. 問い合わせ区分別件数・解決率・平均対応時間 =====
lines.append("## 2. 問い合わせ区分別分析\n")

if "inquiry_type" in df.columns:
    type_summary = df.groupby("inquiry_type").agg(
        件数=("inquiry_id", "count"),
        解決件数=("is_resolved", "sum"),
        平均対応時間=("handling_minutes", "mean"),
        平均満足度=("satisfaction", "mean"),
        再問い合わせ件数=("recontact_flag", "sum"),
    )
    type_summary["解決率(%)"] = (type_summary["解決件数"] / type_summary["件数"] * 100).round(1)
    type_summary["再問い合わせ率(%)"] = (type_summary["再問い合わせ件数"] / type_summary["件数"] * 100).round(1)
    type_summary["平均対応時間"] = type_summary["平均対応時間"].round(1)
    type_summary["平均満足度"] = type_summary["平均満足度"].round(2)
    type_summary = type_summary.sort_values("件数", ascending=False)
    lines.append(type_summary[["件数", "解決率(%)", "平均対応時間", "平均満足度", "再問い合わせ率(%)"]].to_markdown())
    lines.append("")

    # CSVに出力
    type_summary_out = type_summary.reset_index()
    type_summary_out.to_csv(TYPE_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] Type summary CSV: {TYPE_CSV_PATH}")

# ===== 3. チャネル別件数・満足度平均 =====
lines.append("## 3. チャネル別分析\n")

if "channel" in df.columns:
    channel_summary = df.groupby("channel").agg(
        件数=("inquiry_id", "count"),
        解決件数=("is_resolved", "sum"),
        平均満足度=("satisfaction", "mean"),
        平均対応時間=("handling_minutes", "mean"),
        再問い合わせ件数=("recontact_flag", "sum"),
    )
    channel_summary["解決率(%)"] = (channel_summary["解決件数"] / channel_summary["件数"] * 100).round(1)
    channel_summary["再問い合わせ率(%)"] = (channel_summary["再問い合わせ件数"] / channel_summary["件数"] * 100).round(1)
    channel_summary["平均満足度"] = channel_summary["平均満足度"].round(2)
    channel_summary["平均対応時間"] = channel_summary["平均対応時間"].round(1)
    channel_summary = channel_summary.sort_values("件数", ascending=False)
    lines.append(channel_summary[["件数", "解決率(%)", "平均満足度", "平均対応時間", "再問い合わせ率(%)"]].to_markdown())
    lines.append("")

# ===== 4. オペレーター別担当件数・解決率 =====
lines.append("## 4. オペレーター別分析\n")

if "operator_id" in df.columns:
    op_summary = df.groupby("operator_id").agg(
        担当件数=("inquiry_id", "count"),
        解決件数=("is_resolved", "sum"),
        平均対応時間=("handling_minutes", "mean"),
        平均満足度=("satisfaction", "mean"),
    )
    op_summary["解決率(%)"] = (op_summary["解決件数"] / op_summary["担当件数"] * 100).round(1)
    op_summary["平均対応時間"] = op_summary["平均対応時間"].round(1)
    op_summary["平均満足度"] = op_summary["平均満足度"].round(2)
    op_summary = op_summary.sort_values("担当件数", ascending=False)
    lines.append(op_summary[["担当件数", "解決率(%)", "平均対応時間", "平均満足度"]].to_markdown())
    lines.append("")

# ===== 5. efficiency_flag 別集計 =====
lines.append("## 5. 対応効率別集計\n")

if "efficiency_flag" in df.columns:
    eff_summary = df.groupby("efficiency_flag").agg(
        件数=("inquiry_id", "count"),
        解決件数=("is_resolved", "sum"),
        平均満足度=("satisfaction", "mean"),
    )
    eff_summary["解決率(%)"] = (eff_summary["解決件数"] / eff_summary["件数"] * 100).round(1)
    eff_summary["平均満足度"] = eff_summary["平均満足度"].round(2)
    eff_order = ["迅速", "標準", "長時間"]
    eff_summary = eff_summary.reindex([e for e in eff_order if e in eff_summary.index])
    lines.append(eff_summary[["件数", "解決率(%)", "平均満足度"]].to_markdown())
    lines.append("")

# ===== 6. ビジネスインサイト・改善示唆 =====
lines.append("## 6. ビジネスインサイト・改善示唆\n")

lines.append(f"- 総問い合わせ件数: **{total_rows:,} 件**、解決率: **{resolution_rate:.1f}%**")
lines.append(f"- 再問い合わせ率: **{recontact_rate:.1f}%** — 一次解決率向上が重要課題")
lines.append(f"- 平均対応時間: **{avg_minutes:.1f} 分** / 平均満足度: **{avg_satisfaction:.2f} 点**")

if "inquiry_type" in df.columns and "is_resolved" in df.columns:
    worst_type = (
        df.groupby("inquiry_type")["is_resolved"].mean().idxmin()
    )
    worst_rate = df.groupby("inquiry_type")["is_resolved"].mean()[worst_type] * 100
    lines.append(f"- 解決率が最低の問い合わせ区分: **{worst_type}** ({worst_rate:.1f}%) -- 対応フローの見直しを推奨")

if "channel" in df.columns and "satisfaction" in df.columns:
    best_channel = df.groupby("channel")["satisfaction"].mean().idxmax()
    best_sat = df.groupby("channel")["satisfaction"].mean()[best_channel]
    lines.append(f"- 満足度が最高のチャネル: **{best_channel}** (平均 {best_sat:.2f} 点) -- 優良事例の横展開を推奨")

if "operator_id" in df.columns and "is_resolved" in df.columns:
    top_op = df.groupby("operator_id")["is_resolved"].mean().idxmax()
    top_op_rate = df.groupby("operator_id")["is_resolved"].mean()[top_op] * 100
    lines.append(f"- 解決率トップオペレーター: **{top_op}** ({top_op_rate:.1f}%) -- ベストプラクティス共有を推奨")

lines.append("")
lines.append("### まとめ\n")
lines.append(f"2024年1月の保険問い合わせ対応履歴 {total_rows:,} 件を分析しました。")
lines.append(f"解決率 {resolution_rate:.1f}% を達成していますが、再問い合わせ率 {recontact_rate:.1f}% の低減が課題です。")
lines.append("問い合わせ区分別の対応フロー改善とオペレーター間のスキル共有により、顧客満足度のさらなる向上が期待できます。")
lines.append("")

REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
print(f"[OK] Analysis report: {REPORT_PATH}")
print(f"     Resolution rate: {resolution_rate:.1f}% ({int(df['is_resolved'].sum())}/{total_rows})")
