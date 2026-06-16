"""
C-26: 請求書突合・差異検出パイプライン 分析スクリプト
突合結果サマリー / 得意先別差異ランキング / 支払区分別 / 月次トレンド を出力する。
print文にバックスラッシュY記号・絵文字・em-dash を使わないこと。
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_invoice_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CLIENT_CSV_PATH = OUTPUT_DIR / "client_summary_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["invoice_amount", "received_amount", "variance_amount", "variance_rate"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

if "invoice_date" in df.columns:
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

lines = ["# 請求書突合分析レポート（2024年1月）\n"]

# ===== 1. 突合結果サマリー =====
lines.append("## 1. 突合結果サマリー\n")

total_rows = len(df)
total_invoice = df["invoice_amount"].sum()
total_received = df["received_amount"].sum()
total_variance = df["variance_amount"].sum()

if "match_status" in df.columns:
    status_summary = df.groupby("match_status").agg(
        件数=("invoice_no", "count"),
        請求金額合計=("invoice_amount", "sum"),
        入金金額合計=("received_amount", "sum"),
        差異金額合計=("variance_amount", "sum"),
    ).reindex(["一致", "差異", "過払", "未入金"]).fillna(0)
    status_summary["構成比(%)"] = (status_summary["件数"] / total_rows * 100).round(1)

    fmt = status_summary.copy()
    fmt["請求金額合計"] = fmt["請求金額合計"].map("{:,.0f}".format)
    fmt["入金金額合計"] = fmt["入金金額合計"].map("{:,.0f}".format)
    fmt["差異金額合計"] = fmt["差異金額合計"].map("{:,.0f}".format)
    lines.append(fmt.to_markdown())
    lines.append("")

match_count = (df["match_status"] == "一致").sum() if "match_status" in df.columns else 0
match_rate = match_count / total_rows * 100 if total_rows > 0 else 0
lines.append(f"- 総請求件数: **{total_rows:,} 件**")
lines.append(f"- 請求総額: **{total_invoice:,.0f} 円**")
lines.append(f"- 入金総額: **{total_received:,.0f} 円**")
lines.append(f"- 差異総額: **{total_variance:,.0f} 円**")
lines.append(f"- 突合一致率: **{match_rate:.1f}%**")
lines.append("")

# ===== 2. 得意先別差異ランキング =====
lines.append("## 2. 得意先別差異ランキング\n")

if "client_code" in df.columns:
    client_summary = df.groupby("client_code").agg(
        請求件数=("invoice_no", "count"),
        請求金額合計=("invoice_amount", "sum"),
        入金金額合計=("received_amount", "sum"),
        差異金額合計=("variance_amount", "sum"),
        差異件数=("match_status", lambda x: (x != "一致").sum()),
    )
    client_summary["差異発生率(%)"] = (
        client_summary["差異件数"] / client_summary["請求件数"] * 100
    ).round(1)
    client_summary = client_summary.sort_values("差異金額合計", key=abs, ascending=False)

    # 上位10社
    top10 = client_summary.head(10).copy()
    fmt2 = top10.copy()
    fmt2["請求金額合計"] = fmt2["請求金額合計"].map("{:,.0f}".format)
    fmt2["入金金額合計"] = fmt2["入金金額合計"].map("{:,.0f}".format)
    fmt2["差異金額合計"] = fmt2["差異金額合計"].map("{:,.0f}".format)
    lines.append("### 差異金額上位10社\n")
    lines.append(fmt2.to_markdown())
    lines.append("")

    # 全得意先サマリーCSV出力
    client_summary_out = client_summary.reset_index()
    client_summary_out.to_csv(CLIENT_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] 得意先サマリーCSV出力: {CLIENT_CSV_PATH}")

# ===== 3. 支払区分別差異発生率 =====
lines.append("## 3. 支払区分別差異分析\n")

if "payment_type" in df.columns:
    pay_summary = df.groupby("payment_type").agg(
        件数=("invoice_no", "count"),
        請求金額合計=("invoice_amount", "sum"),
        差異件数=("match_status", lambda x: (x != "一致").sum()),
        差異金額合計=("variance_amount", lambda x: x[df.loc[x.index, "match_status"] != "一致"].sum()),
    )
    pay_summary["差異発生率(%)"] = (
        pay_summary["差異件数"] / pay_summary["件数"] * 100
    ).round(1)
    pay_summary = pay_summary.sort_values("差異発生率(%)", ascending=False)
    fmt3 = pay_summary.copy()
    fmt3["請求金額合計"] = fmt3["請求金額合計"].map("{:,.0f}".format)
    fmt3["差異金額合計"] = fmt3["差異金額合計"].map("{:,.0f}".format)
    lines.append(fmt3.to_markdown())
    lines.append("")

# ===== 4. 月次入金状況トレンド =====
lines.append("## 4. 月次入金状況トレンド\n")

if "invoice_date" in df.columns and not df["invoice_date"].isna().all():
    df["year_month"] = df["invoice_date"].dt.to_period("M").astype(str)
    trend = df.groupby("year_month").agg(
        件数=("invoice_no", "count"),
        請求金額合計=("invoice_amount", "sum"),
        入金金額合計=("received_amount", "sum"),
        差異件数=("match_status", lambda x: (x != "一致").sum()),
    )
    trend["入金率(%)"] = (
        trend["入金金額合計"] / trend["請求金額合計"].replace(0, np.nan) * 100
    ).round(1)
    fmt4 = trend.copy()
    fmt4["請求金額合計"] = fmt4["請求金額合計"].map("{:,.0f}".format)
    fmt4["入金金額合計"] = fmt4["入金金額合計"].map("{:,.0f}".format)
    lines.append(fmt4.to_markdown())
    lines.append("")
else:
    lines.append("- 日付データなし\n")

# ===== 5. 未入金・差異明細（上位件数） =====
lines.append("## 5. 未入金・差異明細（上位20件）\n")

if "match_status" in df.columns:
    problem_df = df[df["match_status"] != "一致"].sort_values("variance_amount", key=abs, ascending=False)
    if len(problem_df) > 0:
        disp = problem_df.head(20)[
            ["invoice_no", "client_code", "invoice_date", "invoice_amount",
             "received_amount", "variance_amount", "match_status"]
        ].copy()
        disp["invoice_amount"] = disp["invoice_amount"].map("{:,.0f}".format)
        disp["received_amount"] = disp["received_amount"].map("{:,.0f}".format)
        disp["variance_amount"] = disp["variance_amount"].map("{:,.0f}".format)
        lines.append(disp.to_markdown(index=False))
        lines.append("")
    else:
        lines.append("- 差異件数: 0\n")

# ===== 6. ビジネスインサイト・改善示唆 =====
lines.append("## 6. ビジネスインサイト・改善示唆\n")

unpaid_count = (df["match_status"] == "未入金").sum() if "match_status" in df.columns else 0
over_count   = (df["match_status"] == "過払").sum()   if "match_status" in df.columns else 0
diff_count   = (df["match_status"] == "差異").sum()   if "match_status" in df.columns else 0
unpaid_amount = df.loc[df["match_status"] == "未入金", "invoice_amount"].sum() if "match_status" in df.columns else 0

lines.append(f"- 請求総額: **{total_invoice:,.0f} 円**, 入金総額: **{total_received:,.0f} 円**")
lines.append(f"- 突合一致率: **{match_rate:.1f}%** ({match_count:,} 件 / {total_rows:,} 件)")
lines.append(f"- 差異件数: {diff_count} 件 / 過払件数: {over_count} 件 / 未入金件数: {unpaid_count} 件")
lines.append(f"- 未入金の合計請求額: **{unpaid_amount:,.0f} 円** — 督促対応を優先してください")

if "client_code" in df.columns and "match_status" in df.columns:
    top_diff_client = (
        df[df["match_status"] != "一致"]
        .groupby("client_code")["variance_amount"]
        .apply(lambda x: x.abs().sum())
        .idxmax()
    )
    lines.append(f"- 差異金額最大の得意先: **{top_diff_client}** — 契約条件・振込先の再確認を推奨")

if "payment_type" in df.columns and "match_status" in df.columns:
    pay_diff_rate = (
        df.groupby("payment_type")["match_status"]
        .apply(lambda x: (x != "一致").sum() / len(x) * 100)
    )
    worst_pay = pay_diff_rate.idxmax()
    lines.append(f"- 差異発生率が最高の支払区分: **{worst_pay}** ({pay_diff_rate[worst_pay]:.1f}%) — 処理フローの見直しを検討")

lines.append("")
lines.append("### まとめ\n")
lines.append(f"2024年1月の突合処理において {total_rows:,} 件を処理しました。")
lines.append(f"一致率 {match_rate:.1f}% を達成しており、{diff_count + unpaid_count + over_count} 件に何らかの差異が発生しています。")
lines.append("未入金案件については速やかに督促対応を実施し、過払・差異案件については取引先と照合調整を行うことを推奨します。")
lines.append("")

REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
print(f"[OK] 分析レポート出力完了: {REPORT_PATH}")
print(f"     突合一致率: {match_rate:.1f}% ({match_count}/{total_rows})")
