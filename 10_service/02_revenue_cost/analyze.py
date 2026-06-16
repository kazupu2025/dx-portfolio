"""
C-21: サービス別売上・原価分析
output/analysis_report.md と output/service_summary_202401.csv を生成する
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_revenue_cost_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_PATH = OUTPUT_DIR / "service_summary_202401.csv"


def load_data():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["is_completed"] = df["is_completed"].astype(str).map(
        lambda x: True if x.lower() in ("true", "1") else False
    )
    return df


def analyze_service(df):
    """サービス区分別 粗利率・営業利益率ランキング"""
    grp = df.groupby("service_type").agg(
        案件数=("project_id", "count"),
        売上合計=("revenue", "sum"),
        直接原価合計=("direct_cost", "sum"),
        総原価合計=("total_cost", "sum"),
        粗利合計=("gross_profit", "sum"),
        営業利益合計=("operating_profit", "sum"),
        工数合計=("hours_spent", "sum"),
        赤字件数=("profit_flag", lambda x: (x == "赤字").sum()),
        低収益件数=("profit_flag", lambda x: (x == "低収益").sum()),
    ).reset_index()

    grp["粗利率"] = (grp["粗利合計"] / grp["売上合計"].replace(0, np.nan)).round(4)
    grp["営業利益率"] = (grp["営業利益合計"] / grp["売上合計"].replace(0, np.nan)).round(4)
    grp["時間当たり売上"] = (grp["売上合計"] / grp["工数合計"].replace(0, np.nan)).round(0)
    grp = grp.sort_values("粗利率", ascending=False)
    return grp


def analyze_department(df):
    """部門別 売上・原価・工数効率"""
    grp = df.groupby("department").agg(
        案件数=("project_id", "count"),
        売上合計=("revenue", "sum"),
        直接原価合計=("direct_cost", "sum"),
        粗利合計=("gross_profit", "sum"),
        工数合計=("hours_spent", "sum"),
    ).reset_index()
    grp["粗利率"] = (grp["粗利合計"] / grp["売上合計"].replace(0, np.nan)).round(4)
    grp["時間当たり売上"] = (grp["売上合計"] / grp["工数合計"].replace(0, np.nan)).round(0)
    grp = grp.sort_values("売上合計", ascending=False)
    return grp


def analyze_monthly(df):
    """月次売上・利益トレンド"""
    grp = df.groupby("contract_month").agg(
        案件数=("project_id", "count"),
        売上合計=("revenue", "sum"),
        粗利合計=("gross_profit", "sum"),
        営業利益合計=("operating_profit", "sum"),
    ).reset_index()
    grp["粗利率"] = (grp["粗利合計"] / grp["売上合計"].replace(0, np.nan)).round(4)
    grp = grp.sort_values("contract_month")
    return grp


def analyze_alerts(df):
    """赤字・低収益案件のアラート一覧"""
    alert = df[df["profit_flag"].isin(["赤字", "低収益"])].copy()
    alert = alert[["project_id", "client_name", "service_type", "department",
                   "contract_month", "revenue", "operating_profit",
                   "operating_margin_ratio", "profit_flag"]].copy()
    alert = alert.sort_values("operating_margin_ratio")
    return alert


def fmt_yen(v):
    return f"¥{v:,.0f}"


def fmt_pct(v):
    if pd.isna(v):
        return "N/A"
    return f"{v * 100:.1f}%"


def write_report(df, svc_df, dept_df, month_df, alert_df):
    total_revenue = df["revenue"].sum()
    total_gross = df["gross_profit"].sum()
    total_op = df["operating_profit"].sum()
    avg_gm = total_gross / total_revenue if total_revenue > 0 else 0
    avg_om = total_op / total_revenue if total_revenue > 0 else 0
    red_count = (df["profit_flag"] == "赤字").sum()
    low_count = (df["profit_flag"] == "低収益").sum()

    lines = []
    lines.append("# サービス別売上・原価分析レポート")
    lines.append("")
    lines.append("## サマリー")
    lines.append("")
    lines.append(f"- 分析対象期間: 2024年1月〜3月")
    lines.append(f"- 総案件数: {len(df):,}件")
    lines.append(f"- 売上合計: {fmt_yen(total_revenue)}")
    lines.append(f"- 粗利合計: {fmt_yen(total_gross)}（粗利率: {fmt_pct(avg_gm)}）")
    lines.append(f"- 営業利益合計: {fmt_yen(total_op)}（営業利益率: {fmt_pct(avg_om)}）")
    lines.append(f"- 赤字案件: {red_count}件 / 低収益案件: {low_count}件")
    lines.append("")

    lines.append("## サービス区分別 粗利率・営業利益率ランキング")
    lines.append("")
    lines.append("| サービス区分 | 案件数 | 売上合計 | 粗利率 | 営業利益率 | 時間当たり売上 | 赤字件数 |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, row in svc_df.iterrows():
        lines.append(
            f"| {row['service_type']} | {int(row['案件数'])} | {fmt_yen(row['売上合計'])} "
            f"| {fmt_pct(row['粗利率'])} | {fmt_pct(row['営業利益率'])} "
            f"| {fmt_yen(row['時間当たり売上'])} | {int(row['赤字件数'])} |"
        )
    lines.append("")

    lines.append("## 部門別 売上・工数効率")
    lines.append("")
    lines.append("| 担当部門 | 案件数 | 売上合計 | 粗利率 | 時間当たり売上 |")
    lines.append("|---|---|---|---|---|")
    for _, row in dept_df.iterrows():
        lines.append(
            f"| {row['department']} | {int(row['案件数'])} | {fmt_yen(row['売上合計'])} "
            f"| {fmt_pct(row['粗利率'])} | {fmt_yen(row['時間当たり売上'])} |"
        )
    lines.append("")

    lines.append("## 月次売上・利益トレンド")
    lines.append("")
    lines.append("| 月 | 案件数 | 売上合計 | 粗利合計 | 粗利率 | 営業利益合計 |")
    lines.append("|---|---|---|---|---|---|")
    for _, row in month_df.iterrows():
        lines.append(
            f"| {row['contract_month']} | {int(row['案件数'])} | {fmt_yen(row['売上合計'])} "
            f"| {fmt_yen(row['粗利合計'])} | {fmt_pct(row['粗利率'])} | {fmt_yen(row['営業利益合計'])} |"
        )
    lines.append("")

    lines.append("## 赤字・低収益案件アラート")
    lines.append("")
    if len(alert_df) == 0:
        lines.append("アラート案件はありません。")
    else:
        lines.append(f"要注意案件: {len(alert_df)}件")
        lines.append("")
        lines.append("| 案件ID | 顧客名 | サービス区分 | 月 | 売上 | 営業利益 | 営業利益率 | 判定 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for _, row in alert_df.head(20).iterrows():
            lines.append(
                f"| {row['project_id']} | {row['client_name']} | {row['service_type']} "
                f"| {row['contract_month']} | {fmt_yen(row['revenue'])} "
                f"| {fmt_yen(row['operating_profit'])} | {fmt_pct(row['operating_margin_ratio'])} "
                f"| {row['profit_flag']} |"
            )
    lines.append("")

    lines.append("## インサイト・考察")
    lines.append("")

    # 粗利率最高サービス
    best_svc = svc_df.iloc[0]
    worst_svc = svc_df.iloc[-1]
    lines.append(
        f"- 粗利率最高サービスは「{best_svc['service_type']}」（{fmt_pct(best_svc['粗利率'])}）、"
        f"最低は「{worst_svc['service_type']}」（{fmt_pct(worst_svc['粗利率'])}）"
    )

    # 売上最大部門
    top_dept = dept_df.iloc[0]
    lines.append(f"- 売上最大部門は「{top_dept['department']}」（{fmt_yen(top_dept['売上合計'])}）")

    # 月次トレンド
    if len(month_df) >= 2:
        first_month = month_df.iloc[0]
        last_month = month_df.iloc[-1]
        rev_change = last_month["売上合計"] - first_month["売上合計"]
        direction = "増加" if rev_change >= 0 else "減少"
        lines.append(
            f"- {first_month['contract_month']}から{last_month['contract_month']}にかけて"
            f"売上が{fmt_yen(abs(rev_change))}{direction}"
        )

    # 赤字アラート
    if red_count > 0:
        lines.append(f"- 赤字案件が{red_count}件存在。原価率の見直しと契約単価の引き上げを検討が必要")
    else:
        lines.append("- 赤字案件なし。収益管理は概ね良好")

    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] {REPORT_PATH}")


def main():
    print("=== 分析開始 ===")
    df = load_data()

    svc_df = analyze_service(df)
    dept_df = analyze_department(df)
    month_df = analyze_monthly(df)
    alert_df = analyze_alerts(df)

    # レポート出力
    write_report(df, svc_df, dept_df, month_df, alert_df)

    # サービス別サマリーCSV
    svc_df.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] {SUMMARY_PATH}")

    print(f"\n=== 分析完了 ===")
    print(f"案件数: {len(df)}")
    print(f"売上合計: {fmt_yen(df['revenue'].sum())}")
    print(f"赤字案件: {(df['profit_flag'] == '赤字').sum()}件")


if __name__ == "__main__":
    main()
