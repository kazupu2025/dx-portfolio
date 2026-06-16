"""
C-31: 契約更新アラート・期限管理パイプライン 分析スクリプト
更新ステータス別サマリー / 担当者別アラート / 保険種別 / 期限切れ・緊急明細 を出力する。
print文にバックスラッシュY記号・絵文字・em-dash を使わないこと。
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_contracts_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV_PATH = OUTPUT_DIR / "contract_summary_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

for col in ["annual_premium", "days_to_expiry", "contract_years"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

if "start_date" in df.columns:
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
if "end_date" in df.columns:
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

STATUS_ORDER = ["期限切れ", "緊急", "警告", "正常"]

lines = ["# 契約更新アラート分析レポート（基準日: 2024年2月1日）\n"]

# ===== 1. 更新ステータス別件数・保険料サマリー =====
lines.append("## 1. 更新ステータス別サマリー\n")

total_rows = len(df)
total_premium = df["annual_premium"].sum() if "annual_premium" in df.columns else 0

if "renewal_status" in df.columns:
    status_summary = df.groupby("renewal_status").agg(
        件数=("contract_no", "count"),
        年間保険料合計=("annual_premium", "sum"),
        年間保険料平均=("annual_premium", "mean"),
    ).reindex(STATUS_ORDER).fillna(0)
    status_summary["構成比(%)"] = (status_summary["件数"] / total_rows * 100).round(1)

    fmt = status_summary.copy()
    fmt["年間保険料合計"] = fmt["年間保険料合計"].map("{:,.0f}".format)
    fmt["年間保険料平均"] = fmt["年間保険料平均"].map("{:,.0f}".format)
    lines.append(fmt.to_markdown())
    lines.append("")

expired_count = (df["renewal_status"] == "期限切れ").sum() if "renewal_status" in df.columns else 0
urgent_count  = (df["renewal_status"] == "緊急").sum()    if "renewal_status" in df.columns else 0
warning_count = (df["renewal_status"] == "警告").sum()    if "renewal_status" in df.columns else 0
normal_count  = (df["renewal_status"] == "正常").sum()    if "renewal_status" in df.columns else 0

lines.append(f"- 総契約件数: **{total_rows:,} 件**")
lines.append(f"- 年間保険料合計: **{total_premium:,.0f} 円**")
lines.append(f"- 期限切れ: **{expired_count:,} 件** / 緊急（30日以内）: **{urgent_count:,} 件** / 警告（31〜90日）: **{warning_count:,} 件** / 正常: **{normal_count:,} 件**")
lines.append(f"- アラート対象（期限切れ+緊急）: **{expired_count + urgent_count:,} 件** ({(expired_count + urgent_count) / total_rows * 100:.1f}%)")
lines.append("")

# ===== 2. 担当者別アラート件数ランキング =====
lines.append("## 2. 担当者別アラート件数ランキング\n")

if "agent_name" in df.columns and "renewal_status" in df.columns:
    agent_summary = df.groupby("agent_name").agg(
        担当契約数=("contract_no", "count"),
        期限切れ=("renewal_status", lambda x: (x == "期限切れ").sum()),
        緊急=("renewal_status", lambda x: (x == "緊急").sum()),
        警告=("renewal_status", lambda x: (x == "警告").sum()),
        正常=("renewal_status", lambda x: (x == "正常").sum()),
        年間保険料合計=("annual_premium", "sum"),
    )
    agent_summary["アラート件数"] = agent_summary["期限切れ"] + agent_summary["緊急"]
    agent_summary["アラート率(%)"] = (
        agent_summary["アラート件数"] / agent_summary["担当契約数"] * 100
    ).round(1)
    agent_summary = agent_summary.sort_values("アラート件数", ascending=False)

    fmt2 = agent_summary.copy()
    fmt2["年間保険料合計"] = fmt2["年間保険料合計"].map("{:,.0f}".format)
    lines.append(fmt2.to_markdown())
    lines.append("")

    # 担当者別サマリーCSV出力
    agent_summary_out = agent_summary.reset_index()
    agent_summary_out.to_csv(SUMMARY_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] 担当者別サマリーCSV出力: {SUMMARY_CSV_PATH}")

# ===== 3. 保険種別更新状況 =====
lines.append("## 3. 保険種別更新状況\n")

if "insurance_type" in df.columns and "renewal_status" in df.columns:
    ins_summary = df.groupby("insurance_type").agg(
        件数=("contract_no", "count"),
        期限切れ=("renewal_status", lambda x: (x == "期限切れ").sum()),
        緊急=("renewal_status", lambda x: (x == "緊急").sum()),
        警告=("renewal_status", lambda x: (x == "警告").sum()),
        正常=("renewal_status", lambda x: (x == "正常").sum()),
        年間保険料合計=("annual_premium", "sum"),
    )
    ins_summary["アラート件数"] = ins_summary["期限切れ"] + ins_summary["緊急"]
    ins_summary["アラート率(%)"] = (
        ins_summary["アラート件数"] / ins_summary["件数"] * 100
    ).round(1)
    ins_summary = ins_summary.sort_values("アラート率(%)", ascending=False)

    fmt3 = ins_summary.copy()
    fmt3["年間保険料合計"] = fmt3["年間保険料合計"].map("{:,.0f}".format)
    lines.append(fmt3.to_markdown())
    lines.append("")

# ===== 4. 期限切れ・緊急契約の詳細リスト（上位30件）=====
lines.append("## 4. 期限切れ・緊急契約 明細（上位30件）\n")

if "renewal_status" in df.columns:
    alert_df = df[df["renewal_status"].isin(["期限切れ", "緊急"])].copy()
    if len(alert_df) > 0:
        alert_df_sorted = alert_df.sort_values("days_to_expiry")
        disp_cols = ["contract_no", "customer_code", "insurance_type",
                     "end_date", "days_to_expiry", "annual_premium",
                     "agent_name", "renewal_status"]
        disp = alert_df_sorted.head(30)[disp_cols].copy()
        disp["end_date"] = disp["end_date"].dt.strftime("%Y-%m-%d")
        disp["annual_premium"] = disp["annual_premium"].map("{:,.0f}".format)
        lines.append(disp.to_markdown(index=False))
        lines.append("")
    else:
        lines.append("- アラート対象件数: 0\n")

# ===== 5. ビジネスインサイト・改善示唆 =====
lines.append("## 5. ビジネスインサイト・改善示唆\n")

alert_total = expired_count + urgent_count
alert_premium = df.loc[df["renewal_status"].isin(["期限切れ", "緊急"]), "annual_premium"].sum() \
    if "renewal_status" in df.columns else 0

lines.append(f"- 総契約件数: **{total_rows:,} 件**, 年間保険料合計: **{total_premium:,.0f} 円**")
lines.append(f"- アラート対象（期限切れ+緊急）: **{alert_total:,} 件** ({alert_total / total_rows * 100:.1f}%) -- 即時対応が必要")
lines.append(f"- アラート対象の保険料リスク額: **{alert_premium:,.0f} 円**")

if "agent_name" in df.columns and "renewal_status" in df.columns:
    top_agent = agent_summary["アラート件数"].idxmax()
    top_alert = agent_summary.loc[top_agent, "アラート件数"]
    lines.append(f"- アラート件数が最多の担当者: **{top_agent}** ({top_alert:,} 件) -- 優先的にフォローアップを実施してください")

if "insurance_type" in df.columns and "renewal_status" in df.columns:
    top_ins = ins_summary["アラート率(%)"].idxmax()
    top_rate = ins_summary.loc[top_ins, "アラート率(%)"]
    lines.append(f"- アラート率が最高の保険種別: **{top_ins}** ({top_rate:.1f}%) -- 更新促進施策の優先対象です")

lines.append("")
lines.append("### まとめ\n")
lines.append(f"基準日2024年2月1日時点で {total_rows:,} 件の契約を分析しました。")
lines.append(f"期限切れ {expired_count:,} 件・緊急アラート {urgent_count:,} 件、合計 {alert_total:,} 件が即時対応を要します。")
lines.append(f"担当者別では {top_agent if 'agent_name' in df.columns and 'renewal_status' in df.columns else '(要分析)'} が最多アラートを抱えており、")
lines.append("早期の顧客コンタクトと更新手続きの開始を推奨します。")
lines.append("")

REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
print(f"[OK] 分析レポート出力完了: {REPORT_PATH}")
print(f"     期限切れ: {expired_count} 件 / 緊急: {urgent_count} 件 / 警告: {warning_count} 件 / 正常: {normal_count} 件")
