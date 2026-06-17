# -*- coding: utf-8 -*-
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_orders_202401.csv")
REPORT_PATH = os.path.join(OUTPUT_DIR, "analysis_report.md")
SHOP_CSV_PATH = os.path.join(OUTPUT_DIR, "shop_summary_202401.csv")


def main():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    lines = []
    lines.append("# 車両整備依頼・完了率分析レポート\n")
    lines.append(f"対象期間: 2024年01月  総件数: {len(df)}件\n")

    # --- 店舗別分析 ---
    lines.append("## 1. 店舗別サマリー\n")
    shop_grp = df.groupby("shop_name")
    shop_summary = pd.DataFrame({
        "完了件数": shop_grp.apply(lambda x: (x["status"] == "完了").sum()),
        "平均遅延日数": shop_grp["delay_days"].mean().round(2),
        "再入庫率": shop_grp["is_returned"].mean().round(4),
        "売上合計": shop_grp["total_cost"].sum(),
    }).reset_index()

    lines.append("| 店舗名 | 完了件数 | 平均遅延日数 | 再入庫率 | 売上合計 |")
    lines.append("|--------|---------|------------|--------|---------|")
    for _, row in shop_summary.iterrows():
        lines.append(
            f"| {row['shop_name']} | {int(row['完了件数'])} | {row['平均遅延日数']:.2f} | "
            f"{row['再入庫率']:.2%} | {int(row['売上合計']):,} |"
        )
    lines.append("")

    shop_summary.to_csv(SHOP_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] shop_summary saved -> {SHOP_CSV_PATH}")

    # --- 作業区分別分析 ---
    lines.append("## 2. 作業区分別分析\n")
    wtype_grp = df.groupby("work_type")
    wtype_summary = pd.DataFrame({
        "件数": wtype_grp.size(),
        "平均工賃": wtype_grp["labor_cost"].mean().round(0),
        "平均部品代": wtype_grp["parts_cost"].mean().round(0),
        "平均遅延日数": wtype_grp["delay_days"].mean().round(2),
    }).reset_index()

    lines.append("| 作業区分 | 件数 | 平均工賃 | 平均部品代 | 平均遅延日数 |")
    lines.append("|---------|-----|--------|---------|-----------|")
    for _, row in wtype_summary.iterrows():
        lines.append(
            f"| {row['work_type']} | {int(row['件数'])} | {int(row['平均工賃']):,} | "
            f"{int(row['平均部品代']):,} | {row['平均遅延日数']:.2f} |"
        )
    lines.append("")

    # --- 技術者別分析 ---
    lines.append("## 3. 技術者別分析\n")
    tech_grp = df.groupby("tech_id")
    tech_summary = pd.DataFrame({
        "担当件数": tech_grp.size(),
        "遅延率": tech_grp["is_delayed"].mean().round(4),
        "平均遅延日数": tech_grp["delay_days"].mean().round(2),
    }).reset_index().sort_values("遅延率", ascending=False)

    lines.append("| 技術者ID | 担当件数 | 遅延率 | 平均遅延日数 |")
    lines.append("|---------|---------|------|-----------|")
    for _, row in tech_summary.iterrows():
        lines.append(
            f"| {row['tech_id']} | {int(row['担当件数'])} | {row['遅延率']:.2%} | {row['平均遅延日数']:.2f} |"
        )
    lines.append("")

    # --- 全体KPI ---
    lines.append("## 4. 全体KPI\n")
    total_completed = (df["status"] == "完了").sum()
    completion_rate = total_completed / len(df)
    avg_delay = df["delay_days"].mean()
    returned_rate = df["is_returned"].mean()
    total_revenue = df["total_cost"].sum()

    lines.append(f"- 完了件数: {total_completed}件 (完了率: {completion_rate:.2%})")
    lines.append(f"- 平均遅延日数: {avg_delay:.2f}日")
    lines.append(f"- 再入庫率: {returned_rate:.2%}")
    lines.append(f"- 総売上: {total_revenue:,}円")
    lines.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Report saved -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
