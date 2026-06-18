# -*- coding: utf-8 -*-
"""
C-58: 分析スクリプト
output/cleaned_costs_202401.csv を読み込み、工事原価分析レポートとサマリーCSVを出力
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_costs_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["record_date"] = pd.to_datetime(df["record_date"])
    return df


def project_summary(df: pd.DataFrame) -> pd.DataFrame:
    """工事番号別予算額合計・実績合計・差異率・超過件数"""
    return (
        df.groupby("project_no")
        .agg(
            budget_total=("budget_amount", "sum"),
            actual_total=("actual_amount", "sum"),
            over_count=("is_over_budget", "sum"),
            record_count=("record_id", "count"),
        )
        .reset_index()
        .assign(
            variance_rate=lambda d: ((d["actual_total"] - d["budget_total"]) / d["budget_total"]).round(4)
        )
        .sort_values("project_no")
    )


def worktype_variance(df: pd.DataFrame) -> pd.DataFrame:
    """工種別差異率"""
    return (
        df.groupby("work_type")
        .agg(
            budget_total=("budget_amount", "sum"),
            actual_total=("actual_amount", "sum"),
            record_count=("record_id", "count"),
        )
        .reset_index()
        .assign(
            variance_rate=lambda d: ((d["actual_total"] - d["budget_total"]) / d["budget_total"]).round(4)
        )
        .sort_values("variance_rate", ascending=False)
    )


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """費目別実績額"""
    return (
        df.groupby("cost_category")
        .agg(
            budget_total=("budget_amount", "sum"),
            actual_total=("actual_amount", "sum"),
            record_count=("record_id", "count"),
        )
        .reset_index()
        .assign(
            variance_rate=lambda d: ((d["actual_total"] - d["budget_total"]) / d["budget_total"]).round(4)
        )
        .sort_values("actual_total", ascending=False)
    )


def build_report(
    df: pd.DataFrame,
    proj_df: pd.DataFrame,
    wt_df: pd.DataFrame,
    cat_df: pd.DataFrame,
) -> str:
    total_budget = df["budget_amount"].sum()
    total_actual = df["actual_amount"].sum()
    overall_rate = (total_actual - total_budget) / total_budget if total_budget > 0 else 0
    over_count = (df["is_over_budget"] == 1).sum()
    within_count = (df["is_over_budget"] == 0).sum()

    lines = [
        "# 建設業 工事原価・予算実績管理レポート（2024年1月）",
        "",
        "## 1. 概要",
        "",
        f"- 分析対象レコード数: {len(df):,} 件",
        f"- 対象工事件数: {df['project_no'].nunique()} 件",
        f"- 対象期間: {df['record_date'].min().strftime('%Y-%m-%d')} ~ {df['record_date'].max().strftime('%Y-%m-%d')}",
        f"- 総予算額: {total_budget:,.0f} 円",
        f"- 総実績額: {total_actual:,.0f} 円",
        f"- 全体差異率: {overall_rate:.2%}",
        f"- 予算超過件数: {over_count:,} 件 / 予算内件数: {within_count:,} 件",
        "",
        "## 2. 工事番号別 予算・実績・差異率",
        "",
        "| 工事番号 | 予算額合計(円) | 実績額合計(円) | 差異率 | 超過件数 |",
        "|---------|----------------|----------------|--------|----------|",
    ]

    for _, row in proj_df.iterrows():
        rate_pct = f"{row['variance_rate']:.2%}"
        lines.append(
            f"| {row['project_no']} | {row['budget_total']:,.0f} | {row['actual_total']:,.0f}"
            f" | {rate_pct} | {int(row['over_count'])} |"
        )

    lines += [
        "",
        "## 3. 工種別 差異率",
        "",
        "| 工種 | 予算額合計(円) | 実績額合計(円) | 差異率 | 件数 |",
        "|------|----------------|----------------|--------|------|",
    ]

    for _, row in wt_df.iterrows():
        rate_pct = f"{row['variance_rate']:.2%}"
        lines.append(
            f"| {row['work_type']} | {row['budget_total']:,.0f} | {row['actual_total']:,.0f}"
            f" | {rate_pct} | {int(row['record_count'])} |"
        )

    lines += [
        "",
        "## 4. 費目別 実績額",
        "",
        "| 費目 | 予算額合計(円) | 実績額合計(円) | 差異率 | 件数 |",
        "|------|----------------|----------------|--------|------|",
    ]

    for _, row in cat_df.iterrows():
        rate_pct = f"{row['variance_rate']:.2%}"
        lines.append(
            f"| {row['cost_category']} | {row['budget_total']:,.0f} | {row['actual_total']:,.0f}"
            f" | {rate_pct} | {int(row['record_count'])} |"
        )

    lines += [
        "",
        "## 5. まとめ・インサイト",
        "",
        f"1. 総実績額は総予算額に対して {overall_rate:.2%} の差異",
        f"2. 予算超過件数は {over_count} 件（全体の {over_count/len(df):.1%}）",
        f"3. 最も差異率が大きい工種: {wt_df.iloc[0]['work_type']} ({wt_df.iloc[0]['variance_rate']:.2%})",
        f"4. 最も実績額が大きい費目: {cat_df.iloc[0]['cost_category']} ({cat_df.iloc[0]['actual_total']:,.0f} 円)",
        "5. 予算超過プロジェクトの原価管理強化と早期アラートの仕組みづくりを推奨",
        "",
    ]

    return "\n".join(lines)


def main():
    df = load_data()

    proj_df = project_summary(df)
    wt_df = worktype_variance(df)
    cat_df = category_summary(df)

    # レポート出力
    report = build_report(df, proj_df, wt_df, cat_df)
    report_path = OUTPUT_DIR / "analysis_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"レポート出力: {report_path}")

    # サマリーCSV出力
    summary_path = OUTPUT_DIR / "project_summary_202401.csv"
    proj_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"サマリーCSV出力: {summary_path}")
    print(f"  -> {len(proj_df)} 行")


if __name__ == "__main__":
    main()
