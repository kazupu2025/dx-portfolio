"""
C-30: 分析スクリプト
output/cleaned_labor_cost_202401.csv を読み込み、人件費分析レポートとサマリーCSVを出力
print文に記号(YEN記号等)は使用しない。
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_labor_cost_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def dept_variance_summary(df: pd.DataFrame) -> pd.DataFrame:
    """部門別予実差異サマリー（金額・率）"""
    summary = (
        df.groupby("department")
        .agg(
            budget_total=("budget_cost", "sum"),
            actual_total=("actual_cost", "sum"),
            variance_total=("variance_amount", "sum"),
            over_count=("variance_flag", lambda x: (x == "超過").sum()),
        )
        .reset_index()
    )
    summary["variance_rate_avg"] = (
        summary["variance_total"] / summary["budget_total"]
    ).round(4)
    return summary.sort_values("variance_total", ascending=False).reset_index(drop=True)


def employment_cost_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """雇用区分別人件費構成"""
    return (
        df.groupby("employment_type")
        .agg(
            budget_total=("budget_cost", "sum"),
            actual_total=("actual_cost", "sum"),
            overtime_total=("overtime_cost", "sum"),
            head_count_avg=("head_count", "mean"),
        )
        .round(0)
        .reset_index()
    )


def overdept_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """差異超過部門ランキング（超過回数の多い順）"""
    over_df = df[df["variance_flag"] == "超過"].copy()
    if over_df.empty:
        return pd.DataFrame(columns=["department", "over_count", "avg_variance_rate"])
    ranking = (
        over_df.groupby("department")
        .agg(
            over_count=("variance_flag", "count"),
            avg_variance_rate=("variance_rate", "mean"),
        )
        .round(4)
        .reset_index()
        .sort_values("over_count", ascending=False)
        .reset_index(drop=True)
    )
    return ranking


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """月別人件費トレンド（予算 vs 実績）"""
    return (
        df.groupby("year_month")
        .agg(
            budget_total=("budget_cost", "sum"),
            actual_total=("actual_cost", "sum"),
            overtime_total=("overtime_cost", "sum"),
        )
        .round(0)
        .reset_index()
        .sort_values("year_month")
    )


def build_report(
    df: pd.DataFrame,
    dept_df: pd.DataFrame,
    emp_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    trend_df: pd.DataFrame,
) -> str:
    total_budget = df["budget_cost"].sum()
    total_actual = df["actual_cost"].sum()
    total_variance = df["variance_amount"].sum()
    total_overtime = df["overtime_cost"].sum()
    over_count = (df["variance_flag"] == "超過").sum()
    save_count = (df["variance_flag"] == "節約").sum()
    over_depts = dept_df[dept_df["variance_total"] > 0]["department"].tolist()

    lines = [
        "# 人件費推移・予実差異レポート（2024年度）",
        "",
        "## 1. 概要",
        "",
        f"- 分析対象レコード数: {len(df):,} 件",
        f"- 対象部門数: {df['department'].nunique()} 部門",
        f"- 対象期間: {df['year_month'].min()} 〜 {df['year_month'].max()}",
        f"- 予算人件費合計: {total_budget:,.0f} 円",
        f"- 実績人件費合計: {total_actual:,.0f} 円",
        f"- 差異合計: {total_variance:+,.0f} 円",
        f"- 残業代合計: {total_overtime:,.0f} 円",
        f"- 超過件数: {over_count} 件 / 節約件数: {save_count} 件",
        "",
        "## 2. 部門別予実差異サマリー",
        "",
        "| 部門 | 予算合計(円) | 実績合計(円) | 差異額(円) | 差異率 | 超過回数 |",
        "|------|------------|------------|----------|--------|--------|",
    ]

    for _, row in dept_df.iterrows():
        lines.append(
            f"| {row['department']} | {row['budget_total']:,.0f} | {row['actual_total']:,.0f}"
            f" | {row['variance_total']:+,.0f} | {row['variance_rate_avg']:.2%} | {int(row['over_count'])} |"
        )

    lines += [
        "",
        "## 3. 雇用区分別人件費構成",
        "",
        "| 雇用区分 | 予算合計(円) | 実績合計(円) | 残業代合計(円) | 平均人員数 |",
        "|---------|------------|------------|-------------|---------|",
    ]
    for _, row in emp_df.iterrows():
        lines.append(
            f"| {row['employment_type']} | {row['budget_total']:,.0f} | {row['actual_total']:,.0f}"
            f" | {row['overtime_total']:,.0f} | {row['head_count_avg']:.1f} |"
        )

    lines += [
        "",
        "## 4. 差異超過部門ランキング",
        "",
    ]
    if ranking_df.empty:
        lines.append("超過部門はありません。")
    else:
        lines += [
            "| 順位 | 部門 | 超過回数 | 平均差異率 |",
            "|-----|------|--------|---------|",
        ]
        for rank, (_, row) in enumerate(ranking_df.iterrows(), 1):
            lines.append(
                f"| {rank} | {row['department']} | {int(row['over_count'])} | {row['avg_variance_rate']:.2%} |"
            )

    lines += [
        "",
        "## 5. 月別人件費推移（予算 vs 実績）",
        "",
        "| 年月 | 予算合計(円) | 実績合計(円) | 残業代(円) |",
        "|-----|------------|------------|---------|",
    ]
    for _, row in trend_df.iterrows():
        lines.append(
            f"| {row['year_month']} | {row['budget_total']:,.0f} | {row['actual_total']:,.0f} | {row['overtime_total']:,.0f} |"
        )

    # インサイト・まとめ
    variance_pct = total_variance / total_budget * 100 if total_budget > 0 else 0
    overtime_ratio = total_overtime / total_actual * 100 if total_actual > 0 else 0
    worst_dept = dept_df.iloc[0]["department"] if not dept_df.empty else "N/A"
    worst_rate = dept_df.iloc[0]["variance_rate_avg"] if not dept_df.empty else 0.0

    lines += [
        "",
        "## 6. インサイト・改善示唆",
        "",
        f"### 予実差異の傾向",
        "",
        f"全体の予実差異率は {variance_pct:+.1f}% で、"
        f"実績が予算を {'上回っています' if variance_pct > 0 else '下回っています'}。",
        f"超過件数は {over_count} 件発生しており、"
        f"特に **{worst_dept}** の差異率が {worst_rate:.2%} と最も大きい。",
        "",
        f"### 残業代の占める割合",
        "",
        f"残業代は実績人件費合計の {overtime_ratio:.1f}% を占めています。",
        "残業代が高い部門については、業務プロセスの見直しや採用強化を検討してください。",
        "",
        f"### 超過部門への対策",
        "",
        f"超過フラグが立った部門 ({', '.join(over_depts) if over_depts else 'なし'}) については、"
        "予算の見直しまたは業務効率化による人件費抑制が必要です。",
        "",
        "## 7. まとめ",
        "",
        f"1. 2024年度の人件費は予算に対して {variance_pct:+.1f}% の差異が生じました。",
        f"2. 超過発生件数が最も多い部門は **{worst_dept}** です。改善策の優先実施を推奨します。",
        f"3. 残業代が実績人件費の {overtime_ratio:.1f}% を占めており、残業削減が人件費管理の重要課題です。",
        "4. 正社員・契約社員・パートの雇用区分別コスト構成を定期的にモニタリングし、最適な人員配置を維持してください。",
        "",
    ]

    return "\n".join(lines)


def main():
    df = load_data()

    dept_df = dept_variance_summary(df)
    emp_df = employment_cost_breakdown(df)
    ranking_df = overdept_ranking(df)
    trend_df = monthly_trend(df)

    # レポート出力
    report = build_report(df, dept_df, emp_df, ranking_df, trend_df)
    report_path = OUTPUT_DIR / "analysis_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"レポート出力: {report_path}")

    # サマリーCSV出力
    summary_path = OUTPUT_DIR / "dept_summary_202401.csv"
    dept_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"サマリーCSV出力: {summary_path}")
    print(f"  -> {len(dept_df)} 行")


if __name__ == "__main__":
    main()
