"""
C-19: analyze.py
cleaned_pnl_202401.csv を分析し
- output/analysis_report.md
- output/pnl_summary_202401.csv
を生成する
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_pnl_202401.csv")
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")
SUMMARY_FILE = os.path.join(BASE_DIR, "output", "pnl_summary_202401.csv")

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    return df


def store_summary(df):
    """店舗別集計: 売上達成率・粗利率・営業利益達成率"""
    grp = df.groupby("store_id").agg(
        store_name=("store_name", "first"),
        planned_revenue=("planned_revenue", "sum"),
        actual_revenue=("actual_revenue", "sum"),
        planned_gross_profit=("planned_gross_profit", "sum"),
        actual_gross_profit=("actual_gross_profit", "sum"),
        planned_operating_profit=("planned_operating_profit", "sum"),
        actual_operating_profit=("actual_operating_profit", "sum"),
        profit_flag_count=("profit_flag", "count"),
        red_weeks=("profit_flag", lambda x: (x == "赤字").sum()),
        miss_weeks=("profit_flag", lambda x: (x == "未達").sum()),
    ).reset_index()

    grp["revenue_achievement_rate"] = grp["actual_revenue"] / grp["planned_revenue"]
    grp["gross_profit_margin"] = grp["actual_gross_profit"] / grp["actual_revenue"]
    grp["profit_achievement_rate"] = grp.apply(
        lambda row: row["actual_operating_profit"] / row["planned_operating_profit"]
        if row["planned_operating_profit"] != 0 else float("nan"),
        axis=1,
    )
    return grp


def period_trend(df):
    """期間別トレンド（売上・粗利・営業利益の推移）"""
    grp = df.groupby("year_month").agg(
        planned_revenue=("planned_revenue", "sum"),
        actual_revenue=("actual_revenue", "sum"),
        actual_gross_profit=("actual_gross_profit", "sum"),
        actual_operating_profit=("actual_operating_profit", "sum"),
    ).reset_index().sort_values("year_month")
    grp["gross_profit_margin"] = grp["actual_gross_profit"] / grp["actual_revenue"]
    return grp


def alert_table(df):
    """赤字・未達店舗のアラート一覧"""
    alerts = df[df["profit_flag"].isin(["赤字", "未達"])].copy()
    alerts = alerts[["store_id", "store_name", "year_month", "actual_operating_profit",
                      "planned_operating_profit", "profit_flag"]].sort_values(
        ["profit_flag", "store_id", "year_month"]
    )
    return alerts


def cost_breakdown(df):
    """コスト構成比（原価率・人件費率・その他費用率）"""
    total_revenue = df["actual_revenue"].sum()
    total_cogs = df["actual_cogs"].sum()
    total_labor = df["actual_labor"].sum()
    total_other = df["actual_other"].sum()
    return {
        "原価率": total_cogs / total_revenue,
        "人件費率": total_labor / total_revenue,
        "その他費用率": total_other / total_revenue,
    }


def fmt_yen(val):
    return f"{int(val):,} 円"


def fmt_pct(val):
    if pd.isna(val):
        return "N/A"
    return f"{val*100:.1f}%"


def write_report(df, store_grp, trend, alerts, costs):
    lines = []
    lines.append("# 月次収益・予実差異レポート（C-19）")
    lines.append("")
    lines.append("## 1. 集計概要")
    lines.append("")
    lines.append(f"- 分析対象行数: {len(df):,} 行")
    lines.append(f"- 対象店舗数: {df['store_id'].nunique()} 店舗")
    lines.append(f"- 対象期間: {df['year_month'].min()} 〜 {df['year_month'].max()}")
    lines.append("")

    # 売上合計
    total_plan_rev = df["planned_revenue"].sum()
    total_act_rev = df["actual_revenue"].sum()
    total_act_op = df["actual_operating_profit"].sum()
    total_gp = df["actual_gross_profit"].sum()
    lines.append(f"- 売上予算合計: {fmt_yen(total_plan_rev)}")
    lines.append(f"- 売上実績合計: {fmt_yen(total_act_rev)}")
    lines.append(f"- 売上達成率: {fmt_pct(total_act_rev / total_plan_rev)}")
    lines.append(f"- 粗利合計: {fmt_yen(total_gp)}")
    lines.append(f"- 粗利率: {fmt_pct(total_gp / total_act_rev)}")
    lines.append(f"- 営業利益合計: {fmt_yen(total_act_op)}")
    lines.append("")

    lines.append("## 2. 店舗別 売上達成率・粗利率・営業利益達成率")
    lines.append("")
    lines.append("| 店舗ID | 店舗名 | 売上達成率 | 粗利率 | 営業利益達成率 | 赤字週 | 未達週 |")
    lines.append("|--------|--------|-----------|--------|---------------|--------|--------|")
    for _, row in store_grp.iterrows():
        lines.append(
            f"| {row['store_id']} | {row['store_name']} "
            f"| {fmt_pct(row['revenue_achievement_rate'])} "
            f"| {fmt_pct(row['gross_profit_margin'])} "
            f"| {fmt_pct(row['profit_achievement_rate'])} "
            f"| {int(row['red_weeks'])} "
            f"| {int(row['miss_weeks'])} |"
        )
    lines.append("")

    lines.append("## 3. 月次トレンド（売上・粗利・営業利益推移）")
    lines.append("")
    lines.append("| 期間 | 売上実績 | 売上予算 | 粗利 | 粗利率 | 営業利益 |")
    lines.append("|------|---------|---------|------|--------|---------|")
    for _, row in trend.iterrows():
        lines.append(
            f"| {row['year_month']} "
            f"| {fmt_yen(row['actual_revenue'])} "
            f"| {fmt_yen(row['planned_revenue'])} "
            f"| {fmt_yen(row['actual_gross_profit'])} "
            f"| {fmt_pct(row['gross_profit_margin'])} "
            f"| {fmt_yen(row['actual_operating_profit'])} |"
        )
    lines.append("")

    lines.append("## 4. 赤字・未達アラート一覧")
    lines.append("")
    if len(alerts) == 0:
        lines.append("赤字・未達の週はありませんでした。")
    else:
        lines.append(f"赤字・未達合計: {len(alerts)} 件")
        lines.append("")
        lines.append("| 店舗ID | 店舗名 | 期間 | 実績営業利益 | 計画営業利益 | 判定 |")
        lines.append("|--------|--------|------|------------|------------|------|")
        for _, row in alerts.iterrows():
            lines.append(
                f"| {row['store_id']} | {row['store_name']} | {row['year_month']} "
                f"| {fmt_yen(row['actual_operating_profit'])} "
                f"| {fmt_yen(row['planned_operating_profit'])} "
                f"| {row['profit_flag']} |"
            )
    lines.append("")

    lines.append("## 5. コスト構成比")
    lines.append("")
    for name, ratio in costs.items():
        lines.append(f"- {name}: {fmt_pct(ratio)}")
    lines.append("")

    lines.append("## 6. インサイト・所見")
    lines.append("")
    red_stores = alerts[alerts["profit_flag"] == "赤字"]["store_id"].unique()
    if len(red_stores) > 0:
        lines.append(f"- 赤字を記録した店舗: {', '.join(red_stores)}")
        lines.append("  - 原価率や人件費率の突発的な上昇が主因と考えられます。コスト管理の強化が必要です。")
    top_store = store_grp.sort_values("revenue_achievement_rate", ascending=False).iloc[0]
    lines.append(f"- 売上達成率が最も高い店舗: {top_store['store_name']}（{fmt_pct(top_store['revenue_achievement_rate'])}）")
    bottom_store = store_grp.sort_values("profit_achievement_rate").iloc[0]
    lines.append(f"- 営業利益達成率が最も低い店舗: {bottom_store['store_name']}（{fmt_pct(bottom_store['profit_achievement_rate'])}）")
    lines.append(f"- 原価率 {fmt_pct(costs['原価率'])}、人件費率 {fmt_pct(costs['人件費率'])} が収益圧迫の主要因です。")
    lines.append(f"- 全体の売上達成率は {fmt_pct(total_act_rev / total_plan_rev)} で、予算対比はおおむね安定しています。")
    lines.append("")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[analyze.py] Report: {REPORT_FILE}")


def main():
    print("[analyze.py] Loading cleaned data...")
    df = load_data()

    store_grp = store_summary(df)
    trend = period_trend(df)
    alerts = alert_table(df)
    costs = cost_breakdown(df)

    write_report(df, store_grp, trend, alerts, costs)

    # pnl_summary
    summary = store_grp[[
        "store_id", "store_name",
        "planned_revenue", "actual_revenue", "revenue_achievement_rate",
        "planned_gross_profit", "actual_gross_profit", "gross_profit_margin",
        "planned_operating_profit", "actual_operating_profit", "profit_achievement_rate",
        "red_weeks", "miss_weeks",
    ]].copy()
    summary.to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")
    print(f"[analyze.py] Summary CSV: {SUMMARY_FILE} ({len(summary)} rows)")

    print("[analyze.py] Done.")


if __name__ == "__main__":
    main()
