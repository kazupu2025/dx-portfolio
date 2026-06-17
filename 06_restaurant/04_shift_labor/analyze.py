# -*- coding: utf-8 -*-
"""
C-40: アルバイトシフト管理・人件費集計パイプライン
分析スクリプト
- 店舗別総人件費・平均時給・残業率
- スタッフ別月間労働時間ランキング
- 役職別平均日次賃金
- 日次人件費推移
出力: output/analysis_report.md, output/store_summary_202401.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "cleaned_shift_202401.csv"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
STORE_SUMMARY_FILE = OUTPUT_DIR / "store_summary_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    df["hourly_rate"] = pd.to_numeric(df["hourly_rate"], errors="coerce")
    df["daily_wage"] = pd.to_numeric(df["daily_wage"], errors="coerce")
    df["is_overtime"] = pd.to_numeric(df["is_overtime"], errors="coerce")
    df["work_date"] = pd.to_datetime(df["work_date"], format="%Y-%m-%d", errors="coerce")
    return df


def store_summary(df: pd.DataFrame) -> pd.DataFrame:
    """店舗別総人件費・平均時給・残業率"""
    grp = df.groupby("store_name", as_index=False)
    summary = grp.agg(
        total_labor_cost=("daily_wage", "sum"),
        avg_hourly_rate=("hourly_rate", "mean"),
        total_shifts=("daily_wage", "count"),
        overtime_shifts=("is_overtime", "sum"),
        total_work_hours=("work_hours", "sum"),
    )
    summary["overtime_rate_pct"] = (
        summary["overtime_shifts"] / summary["total_shifts"] * 100
    ).round(2)
    summary["avg_hourly_rate"] = summary["avg_hourly_rate"].round(0)
    summary["total_labor_cost"] = summary["total_labor_cost"].round(0)
    return summary


def staff_hours_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """スタッフ別月間労働時間ランキング"""
    grp = df.groupby("staff_id", as_index=False).agg(
        total_hours=("work_hours", "sum"),
        shift_count=("work_hours", "count"),
        avg_wage=("daily_wage", "mean"),
    )
    grp = grp.sort_values("total_hours", ascending=False).reset_index(drop=True)
    grp.index = grp.index + 1
    grp["avg_wage"] = grp["avg_wage"].round(0)
    return grp


def role_avg_wage(df: pd.DataFrame) -> pd.DataFrame:
    """役職別平均日次賃金"""
    grp = df.groupby("role", as_index=False).agg(
        avg_daily_wage=("daily_wage", "mean"),
        avg_work_hours=("work_hours", "mean"),
        shift_count=("daily_wage", "count"),
    )
    grp["avg_daily_wage"] = grp["avg_daily_wage"].round(0)
    grp["avg_work_hours"] = grp["avg_work_hours"].round(2)
    return grp.sort_values("avg_daily_wage", ascending=False)


def daily_labor_cost(df: pd.DataFrame) -> pd.DataFrame:
    """日次人件費推移"""
    grp = df.groupby("work_date", as_index=False).agg(
        daily_total=("daily_wage", "sum"),
        shift_count=("daily_wage", "count"),
    )
    grp = grp.sort_values("work_date")
    grp["daily_total"] = grp["daily_total"].round(0)
    return grp


def build_report(
    df: pd.DataFrame,
    store_df: pd.DataFrame,
    staff_df: pd.DataFrame,
    role_df: pd.DataFrame,
    daily_df: pd.DataFrame,
) -> str:
    total_cost = df["daily_wage"].sum()
    total_hours = df["work_hours"].sum()
    total_shifts = len(df)
    overtime_rate = df["is_overtime"].mean() * 100
    avg_rate = df["hourly_rate"].mean()

    top_cost_store = store_df.sort_values("total_labor_cost", ascending=False).iloc[0]
    top_hours_staff = staff_df.iloc[0]

    lines = [
        "# C-40 アルバイトシフト管理・人件費集計 分析レポート",
        "",
        "## 概要",
        "",
        f"- 集計期間: 2024年1月",
        f"- 総シフト数: {total_shifts:,} 件",
        f"- 総労働時間: {total_hours:,.1f} 時間",
        f"- 総人件費: {total_cost:,.0f} 円",
        f"- 平均時給: {avg_rate:,.0f} 円",
        f"- 残業率: {overtime_rate:.1f}%",
        "",
        "---",
        "",
        "## 1. 店舗別サマリー",
        "",
        "| 店舗名 | 総人件費(円) | 平均時給(円) | 総シフト数 | 残業率(%) | 総労働時間(h) |",
        "|--------|-------------|-------------|-----------|----------|--------------|",
    ]

    for _, row in store_df.iterrows():
        lines.append(
            f"| {row['store_name']} | {int(row['total_labor_cost']):,} | "
            f"{int(row['avg_hourly_rate']):,} | {int(row['total_shifts']):,} | "
            f"{row['overtime_rate_pct']:.1f} | {row['total_work_hours']:.1f} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 2. スタッフ別月間労働時間 上位10名",
        "",
        "| 順位 | スタッフID | 総労働時間(h) | シフト数 | 平均日次賃金(円) |",
        "|------|-----------|-------------|---------|----------------|",
    ]

    for rank, row in staff_df.head(10).iterrows():
        lines.append(
            f"| {rank} | {row['staff_id']} | {row['total_hours']:.1f} | "
            f"{int(row['shift_count'])} | {int(row['avg_wage']):,} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 3. 役職別平均日次賃金",
        "",
        "| 役職 | 平均日次賃金(円) | 平均労働時間(h) | シフト数 |",
        "|------|----------------|---------------|---------|",
    ]

    for _, row in role_df.iterrows():
        lines.append(
            f"| {row['role']} | {int(row['avg_daily_wage']):,} | "
            f"{row['avg_work_hours']:.2f} | {int(row['shift_count'])} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 4. 日次人件費推移（上位5日）",
        "",
        "| 日付 | 日次人件費(円) | シフト数 |",
        "|------|--------------|---------|",
    ]

    daily_top = daily_df.sort_values("daily_total", ascending=False).head(5)
    for _, row in daily_top.iterrows():
        date_str = row["work_date"].strftime("%Y-%m-%d") if hasattr(row["work_date"], "strftime") else str(row["work_date"])
        lines.append(
            f"| {date_str} | {int(row['daily_total']):,} | {int(row['shift_count'])} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 5. Insights & 改善示唆",
        "",
        f"### 高コスト集中リスク",
        f"- 最高人件費店舗は **{top_cost_store['store_name']}** で "
        f"総額 {int(top_cost_store['total_labor_cost']):,} 円。",
        f"  他店舗との差異を確認し、シフト配置の均衡を図ることを推奨する。",
        "",
        f"### 残業管理",
        f"- 全体の残業率は {overtime_rate:.1f}%。"
        f"残業が集中するスタッフ・店舗を特定し、シフト分散を検討する。",
        "",
        f"### 高稼働スタッフ",
        f"- 最多労働時間スタッフ: {top_hours_staff['staff_id']}（"
        f"{top_hours_staff['total_hours']:.1f} 時間）。"
        f"燃え尽き防止のため上限時間のルール設定を推奨する。",
        "",
        f"### 役職別コスト最適化",
        f"- 平均日次賃金の高い役職に高時給スタッフが集中していないか定期確認が必要。",
        f"  役職ごとに適切な時給バンドを設定することでコスト予測精度が向上する。",
        "",
        f"### シフト計画改善",
        f"- 日次人件費の変動幅を確認し、繁忙日と閑散日のシフト差を最小化することで"
        f"固定費の平準化が見込める。",
    ]

    return "\n".join(lines)


def main():
    print("[INFO] 分析開始 ...")
    df = load_data()

    s_df = store_summary(df)
    staff_df = staff_hours_ranking(df)
    r_df = role_avg_wage(df)
    d_df = daily_labor_cost(df)

    # store_summary CSV出力
    s_df.to_csv(STORE_SUMMARY_FILE, index=False, encoding="utf-8-sig")
    print(f"[OK] 店舗別サマリー -> {STORE_SUMMARY_FILE}")

    # マークダウンレポート出力
    report = build_report(df, s_df, staff_df, r_df, d_df)
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"[OK] 分析レポート -> {REPORT_FILE}")

    print(f"[INFO] 総人件費: {df['daily_wage'].sum():,.0f} 円")
    print(f"[INFO] 残業率: {df['is_overtime'].mean() * 100:.1f}%")


if __name__ == "__main__":
    main()
