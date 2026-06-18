# -*- coding: utf-8 -*-
"""
C-59 農場スタッフ勤怠・作業効率分析パイプライン
分析スクリプト
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_farm_work_202401.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    df["work_date"] = pd.to_datetime(
        df["work_date"].astype(str).str.replace("/", "-"),
        format="%Y-%m-%d",
        errors="coerce",
    )
    return df


def crop_summary(df):
    grp = df.groupby("crop").agg(
        achievement_rate_mean=("achievement_rate", "mean"),
        productivity_mean=("productivity", "mean"),
        work_hours_sum=("work_hours", "sum"),
        record_count=("record_id", "count"),
    ).reset_index()
    grp["achievement_rate_mean"] = grp["achievement_rate_mean"].round(4)
    grp["productivity_mean"] = grp["productivity_mean"].round(2)
    grp["work_hours_sum"] = grp["work_hours_sum"].round(1)
    return grp


def worktype_summary(df):
    grp = df.groupby("work_type").agg(
        record_count=("record_id", "count"),
        achievement_rate_mean=("achievement_rate", "mean"),
        productivity_mean=("productivity", "mean"),
    ).reset_index()
    grp["achievement_rate_mean"] = grp["achievement_rate_mean"].round(4)
    grp["productivity_mean"] = grp["productivity_mean"].round(2)
    return grp


def staff_summary(df):
    grp = df.groupby("staff_id").agg(
        productivity_mean=("productivity", "mean"),
        work_hours_sum=("work_hours", "sum"),
        record_count=("record_id", "count"),
    ).reset_index()
    grp["productivity_mean"] = grp["productivity_mean"].round(2)
    grp["work_hours_sum"] = grp["work_hours_sum"].round(1)
    grp = grp.sort_values("productivity_mean", ascending=False)
    return grp


def write_report(df, crop_df, wt_df, staff_df):
    lines = []
    lines.append("# 農場スタッフ勤怠・作業効率分析レポート 2024年1月")
    lines.append("")
    lines.append("## 全体サマリー")
    lines.append("")
    lines.append(f"- 総記録数: {len(df)}")
    met_rate = df["is_target_met"].mean()
    lines.append(f"- 目標達成率: {met_rate:.2%}")
    avg_prod = df["productivity"].mean()
    lines.append(f"- 平均生産性: {avg_prod:.2f} 単位/時間")
    avg_hours = df["work_hours"].mean()
    lines.append(f"- 平均作業時間: {avg_hours:.2f} 時間")
    lines.append(f"- 高効率件数: {(df['efficiency_grade']=='高効率').sum()}")
    lines.append(f"- 中効率件数: {(df['efficiency_grade']=='中効率').sum()}")
    lines.append(f"- 低効率件数: {(df['efficiency_grade']=='低効率').sum()}")
    lines.append("")

    lines.append("## 作物別集計")
    lines.append("")
    lines.append("| 作物 | 平均達成率 | 平均生産性 | 作業時間合計 | 件数 |")
    lines.append("|------|-----------|-----------|------------|------|")
    for _, row in crop_df.iterrows():
        lines.append(
            f"| {row['crop']} | {row['achievement_rate_mean']:.2%} | "
            f"{row['productivity_mean']:.2f} | {row['work_hours_sum']:.1f} | {int(row['record_count'])} |"
        )
    lines.append("")

    lines.append("## 作業区分別集計")
    lines.append("")
    lines.append("| 作業区分 | 件数 | 平均達成率 | 平均生産性 |")
    lines.append("|---------|------|-----------|-----------|")
    for _, row in wt_df.iterrows():
        lines.append(
            f"| {row['work_type']} | {int(row['record_count'])} | "
            f"{row['achievement_rate_mean']:.2%} | {row['productivity_mean']:.2f} |"
        )
    lines.append("")

    lines.append("## スタッフ別生産性 (上位10名)")
    lines.append("")
    lines.append("| スタッフID | 平均生産性 | 作業時間合計 | 件数 |")
    lines.append("|-----------|-----------|------------|------|")
    for _, row in staff_df.head(10).iterrows():
        lines.append(
            f"| {row['staff_id']} | {row['productivity_mean']:.2f} | "
            f"{row['work_hours_sum']:.1f} | {int(row['record_count'])} |"
        )
    lines.append("")

    report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Report saved: {report_path}")


def main():
    df = load_data()
    print(f"[OK] Loaded {len(df)} rows")

    crop_df = crop_summary(df)
    wt_df = worktype_summary(df)
    staff_df = staff_summary(df)

    # Save crop summary CSV
    crop_out = os.path.join(OUTPUT_DIR, "crop_summary_202401.csv")
    crop_df.to_csv(crop_out, index=False, encoding="utf-8-sig")
    print(f"[OK] Crop summary saved: {crop_out}")

    write_report(df, crop_df, wt_df, staff_df)
    print("[OK] Analysis complete")


if __name__ == "__main__":
    main()
