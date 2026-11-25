# -*- coding: utf-8 -*-
"""
C-54: 店舗別損益・原価率管理パイプライン
分析スクリプト
- 店舗別売上合計・食材費率・人件費率・利益率・黒字/赤字判定
- 日別売上トレンド
出力: output/analysis_report.md, output/store_pl_summary_202401.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "cleaned_pl_202401.csv"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
SUMMARY_FILE = OUTPUT_DIR / "store_pl_summary_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["food_cost"] = pd.to_numeric(df["food_cost"], errors="coerce")
    df["labor_cost"] = pd.to_numeric(df["labor_cost"], errors="coerce")
    df["other_cost"] = pd.to_numeric(df["other_cost"], errors="coerce")
    df["total_cost"] = pd.to_numeric(df["total_cost"], errors="coerce")
    df["gross_profit"] = pd.to_numeric(df["gross_profit"], errors="coerce")
    df["food_cost_rate"] = pd.to_numeric(df["food_cost_rate"], errors="coerce")
    df["labor_cost_rate"] = pd.to_numeric(df["labor_cost_rate"], errors="coerce")
    df["profit_margin"] = pd.to_numeric(df["profit_margin"], errors="coerce")
    df["record_date"] = pd.to_datetime(
        df["record_date"].str.replace("/", "-", regex=False),
        format="%Y-%m-%d",
        errors="coerce"
    )
    return df


def store_pl_summary(df: pd.DataFrame) -> pd.DataFrame:
    """店舗別損益サマリー"""
    grp = df.groupby("store_name", as_index=False)
    summary = grp.agg(
        total_revenue=("revenue", "sum"),
        total_food_cost=("food_cost", "sum"),
        total_labor_cost=("labor_cost", "sum"),
        total_other_cost=("other_cost", "sum"),
        total_cost=("total_cost", "sum"),
        total_gross_profit=("gross_profit", "sum"),
        avg_food_cost_rate=("food_cost_rate", "mean"),
        avg_labor_cost_rate=("labor_cost_rate", "mean"),
        avg_profit_margin=("profit_margin", "mean"),
        record_count=("revenue", "count"),
    )
    # 黒字/赤字判定
    summary["pl_status"] = summary["total_gross_profit"].apply(
        lambda x: "黒字" if x > 0 else "赤字"
    )
    # 利益率を整合（合計ベース）
    summary["total_profit_margin_pct"] = (
        summary["total_gross_profit"] / summary["total_revenue"] * 100
    ).round(2)
    summary["avg_food_cost_rate_pct"] = (summary["avg_food_cost_rate"] * 100).round(2)
    summary["avg_labor_cost_rate_pct"] = (summary["avg_labor_cost_rate"] * 100).round(2)
    return summary.sort_values("total_revenue", ascending=False).reset_index(drop=True)


def daily_revenue_trend(df: pd.DataFrame) -> pd.DataFrame:
    """日別売上トレンド（全店合計）"""
    grp = df.groupby("record_date", as_index=False).agg(
        daily_revenue=("revenue", "sum"),
        daily_gross_profit=("gross_profit", "sum"),
        store_count=("store_name", "nunique"),
    )
    grp = grp.sort_values("record_date").reset_index(drop=True)
    grp["record_date"] = grp["record_date"].dt.strftime("%Y-%m-%d")
    return grp


def write_report(df: pd.DataFrame, summary: pd.DataFrame, daily: pd.DataFrame):
    """分析レポートをMarkdownで出力"""
    lines = []
    lines.append("# 店舗別損益・原価率管理 分析レポート")
    lines.append("")
    lines.append("## 1. 全体サマリー")
    lines.append("")
    total_rev = df["revenue"].sum()
    total_gp = df["gross_profit"].sum()
    total_margin = total_gp / total_rev * 100 if total_rev > 0 else 0
    avg_fcr = df["food_cost_rate"].mean() * 100
    avg_lcr = df["labor_cost_rate"].mean() * 100
    lines.append(f"- 総売上: {total_rev:,.0f} 円")
    lines.append(f"- 総粗利: {total_gp:,.0f} 円")
    lines.append(f"- 全体利益率: {total_margin:.2f}%")
    lines.append(f"- 平均食材費率: {avg_fcr:.2f}%")
    lines.append(f"- 平均人件費率: {avg_lcr:.2f}%")
    lines.append(f"- 総レコード数: {len(df)} 件")
    lines.append("")
    lines.append("## 2. 店舗別損益サマリー")
    lines.append("")
    lines.append("| 店舗名 | 総売上(円) | 総粗利(円) | 利益率(%) | 食材費率(%) | 人件費率(%) | 損益 |")
    lines.append("|--------|-----------|-----------|----------|------------|------------|------|")
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['store_name']} "
            f"| {row['total_revenue']:,.0f} "
            f"| {row['total_gross_profit']:,.0f} "
            f"| {row['total_profit_margin_pct']:.2f} "
            f"| {row['avg_food_cost_rate_pct']:.2f} "
            f"| {row['avg_labor_cost_rate_pct']:.2f} "
            f"| {row['pl_status']} |"
        )
    lines.append("")
    lines.append("## 3. 日別売上トレンド（全店合計・上位10日）")
    lines.append("")
    top_daily = daily.sort_values("daily_revenue", ascending=False).head(10)
    lines.append("| 日付 | 売上合計(円) | 粗利合計(円) |")
    lines.append("|------|------------|------------|")
    for _, row in top_daily.iterrows():
        lines.append(
            f"| {row['record_date']} "
            f"| {row['daily_revenue']:,.0f} "
            f"| {row['daily_gross_profit']:,.0f} |"
        )
    lines.append("")
    lines.append("## 4. 損益フラグ集計")
    lines.append("")
    flag_counts = df["pl_flag"].value_counts()
    for flag, cnt in flag_counts.items():
        lines.append(f"- {flag}: {cnt} 件")
    lines.append("")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Report -> {REPORT_FILE}")


def main():
    print("[INFO] Analysis start ...")
    df = load_data()

    summary = store_pl_summary(df)
    daily = daily_revenue_trend(df)

    # CSVサマリー出力
    summary.to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")
    print(f"[OK] Store summary -> {SUMMARY_FILE}")

    # レポート出力
    write_report(df, summary, daily)
    print("[INFO] Analysis complete")


if __name__ == "__main__":
    main()
