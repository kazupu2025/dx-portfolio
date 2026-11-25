# -*- coding: utf-8 -*-
"""
C-45: サービス別売上・原価レポート
分析スクリプト
"""

import os
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SRC = os.path.join(OUTPUT_DIR, "cleaned_revenue_202401.csv")
OUT_MD = os.path.join(OUTPUT_DIR, "analysis_report.md")
OUT_CSV = os.path.join(OUTPUT_DIR, "service_summary_202401.csv")
OUT_JSON = os.path.join(OUTPUT_DIR, "result_analysis.json")


def main():
    df = pd.read_csv(SRC, encoding="utf-8-sig")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df["gross_profit"] = pd.to_numeric(df["gross_profit"], errors="coerce")
    df["gross_margin"] = pd.to_numeric(df["gross_margin"], errors="coerce")

    # --- サービス別集計 ---
    svc_agg = df.groupby("service_name").agg(
        revenue_total=("revenue", "sum"),
        cost_total=("cost", "sum"),
        gross_profit_total=("gross_profit", "sum"),
        gross_margin_mean=("gross_margin", "mean"),
        row_count=("revenue", "count"),
    ).reset_index()
    svc_agg = svc_agg.sort_values("gross_profit_total", ascending=False).reset_index(drop=True)
    svc_agg["revenue_rank"] = svc_agg["revenue_total"].rank(ascending=False).astype(int)

    # --- カテゴリ別集計 ---
    cat_agg = df.groupby("category").agg(
        revenue_total=("revenue", "sum"),
        gross_margin_mean=("gross_margin", "mean"),
        row_count=("revenue", "count"),
    ).reset_index()

    # --- 日別売上推移 ---
    df["sale_date"] = pd.to_datetime(df["sale_date"], format="%Y-%m-%d")
    daily = df.groupby("sale_date").agg(
        revenue_total=("revenue", "sum"),
        cost_total=("cost", "sum"),
        gross_profit_total=("gross_profit", "sum"),
    ).reset_index()
    daily["sale_date"] = daily["sale_date"].dt.strftime("%Y-%m-%d")

    # --- サービスサマリ CSV 出力 ---
    svc_agg.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"[OK] service_summary -> {OUT_CSV}")

    # --- Markdown レポート ---
    lines = []
    lines.append("# サービス別売上・原価レポート (2024年01月)")
    lines.append("")
    lines.append("## 1. サービス別分析")
    lines.append("")
    lines.append("| サービス名 | 売上合計 | 原価合計 | 粗利合計 | 粗利率 | 貢献ランク |")
    lines.append("|-----------|---------|---------|---------|--------|----------|")
    for _, r in svc_agg.iterrows():
        lines.append(
            f"| {r['service_name']} | {r['revenue_total']:,.0f} | {r['cost_total']:,.0f} "
            f"| {r['gross_profit_total']:,.0f} | {r['gross_margin_mean']:.1%} | {r['revenue_rank']} |"
        )
    lines.append("")
    lines.append("## 2. カテゴリ別分析")
    lines.append("")
    lines.append("| カテゴリ | 売上合計 | 平均粗利率 | 件数 |")
    lines.append("|---------|---------|----------|-----|")
    for _, r in cat_agg.iterrows():
        lines.append(
            f"| {r['category']} | {r['revenue_total']:,.0f} | {r['gross_margin_mean']:.1%} | {r['row_count']} |"
        )
    lines.append("")
    lines.append("## 3. 月次トレンド (日別売上推移)")
    lines.append("")
    lines.append("| 日付 | 売上合計 | 原価合計 | 粗利合計 |")
    lines.append("|-----|---------|---------|---------|")
    for _, r in daily.iterrows():
        lines.append(
            f"| {r['sale_date']} | {r['revenue_total']:,.0f} | {r['cost_total']:,.0f} | {r['gross_profit_total']:,.0f} |"
        )
    lines.append("")

    total_revenue = int(df["revenue"].sum())
    total_gross = int(df["gross_profit"].sum())
    avg_margin = float(df["gross_margin"].mean())
    deficit_svc = int((df["profit_flag"] == "赤字").sum())

    lines.append("## 4. KPIサマリ")
    lines.append("")
    lines.append(f"- 総売上: {total_revenue:,} 円")
    lines.append(f"- 総粗利: {total_gross:,} 円")
    lines.append(f"- 平均粗利率: {avg_margin:.1%}")
    lines.append(f"- 赤字レコード数: {deficit_svc}")
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] analysis_report -> {OUT_MD}")

    # --- JSON出力 ---
    result = {
        "total_revenue": total_revenue,
        "total_gross_profit": total_gross,
        "avg_gross_margin": round(avg_margin, 4),
        "deficit_records": deficit_svc,
        "service_count": len(svc_agg),
        "category_count": len(cat_agg),
        "daily_rows": len(daily),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[OK] result_analysis.json -> {OUT_JSON}")
    print("[OK] Analysis complete.")


if __name__ == "__main__":
    main()
