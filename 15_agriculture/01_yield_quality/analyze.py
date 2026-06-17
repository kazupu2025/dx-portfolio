# -*- coding: utf-8 -*-
"""
C-49 作物収量・品質検査レポートパイプライン
分析スクリプト
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_harvest_202401.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    df["harvest_date"] = pd.to_datetime(
        df["harvest_date"].astype(str).str.replace("/", "-"),
        format="%Y-%m-%d",
        errors="coerce",
    )
    return df


def farm_summary(df):
    grp = df.groupby("farm_name").agg(
        total_harvest=("harvest_qty", "sum"),
        mean_grade_a_rate=("grade_a_rate", "mean"),
        mean_defect_rate=("defect_rate", "mean"),
        record_count=("record_id", "count"),
    ).reset_index()
    grp["total_harvest"] = grp["total_harvest"].round(1)
    grp["mean_grade_a_rate"] = grp["mean_grade_a_rate"].round(4)
    grp["mean_defect_rate"] = grp["mean_defect_rate"].round(4)
    return grp


def crop_summary(df):
    grp = df.groupby("crop").agg(
        mean_harvest=("harvest_qty", "mean"),
        total_harvest=("harvest_qty", "sum"),
    ).reset_index()
    grp["mean_harvest"] = grp["mean_harvest"].round(1)
    grp["total_harvest"] = grp["total_harvest"].round(1)

    flag_dist = df.groupby(["crop", "quality_flag"]).size().unstack(fill_value=0).reset_index()
    result = grp.merge(flag_dist, on="crop", how="left")
    return result


def inspector_summary(df):
    grp = df.groupby("inspector_id").agg(
        record_count=("record_id", "count"),
        mean_grade_a_rate=("grade_a_rate", "mean"),
    ).reset_index()
    grp["mean_grade_a_rate"] = grp["mean_grade_a_rate"].round(4)
    return grp


def write_report(df, farm_df, crop_df, insp_df):
    lines = []
    lines.append("# 作物収量・品質検査レポート 2024年1月")
    lines.append("")
    lines.append("## 全体サマリー")
    lines.append("")
    lines.append(f"- 総レコード数: {len(df)}")
    lines.append(f"- 総収穫量: {df['harvest_qty'].sum():.1f} kg")
    lines.append(f"- 平均A等級率: {df['grade_a_rate'].mean():.2%}")
    lines.append(f"- 平均不合格率: {df['defect_rate'].mean():.2%}")
    lines.append(f"- 優良件数: {(df['quality_flag']=='優良').sum()}")
    lines.append(f"- 合格件数: {(df['quality_flag']=='合格').sum()}")
    lines.append(f"- 要改善件数: {(df['quality_flag']=='要改善').sum()}")
    lines.append("")

    lines.append("## 農場別集計")
    lines.append("")
    lines.append("| 農場名 | 総収穫量(kg) | 平均A等級率 | 平均不合格率 | 件数 |")
    lines.append("|--------|-------------|------------|-------------|------|")
    for _, row in farm_df.iterrows():
        lines.append(
            f"| {row['farm_name']} | {row['total_harvest']:.1f} | "
            f"{row['mean_grade_a_rate']:.2%} | {row['mean_defect_rate']:.2%} | {int(row['record_count'])} |"
        )
    lines.append("")

    lines.append("## 作物別集計")
    lines.append("")
    lines.append("| 作物 | 平均収穫量(kg) | 総収穫量(kg) |")
    lines.append("|------|--------------|-------------|")
    for _, row in crop_df.iterrows():
        lines.append(f"| {row['crop']} | {row['mean_harvest']:.1f} | {row['total_harvest']:.1f} |")
    lines.append("")

    lines.append("## 検査員別担当件数")
    lines.append("")
    lines.append("| 検査員ID | 担当件数 | 平均A等級率 |")
    lines.append("|---------|---------|------------|")
    for _, row in insp_df.iterrows():
        lines.append(f"| {row['inspector_id']} | {int(row['record_count'])} | {row['mean_grade_a_rate']:.2%} |")
    lines.append("")

    report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Report saved: {report_path}")


def main():
    df = load_data()
    print(f"[OK] Loaded {len(df)} rows")

    farm_df = farm_summary(df)
    crop_df = crop_summary(df)
    insp_df = inspector_summary(df)

    # Save farm summary CSV
    farm_out = os.path.join(OUTPUT_DIR, "farm_summary_202401.csv")
    farm_df.to_csv(farm_out, index=False, encoding="utf-8-sig")
    print(f"[OK] Farm summary saved: {farm_out}")

    write_report(df, farm_df, crop_df, insp_df)
    print("[OK] Analysis complete")


if __name__ == "__main__":
    main()
