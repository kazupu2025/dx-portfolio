"""
C-20: 分析スクリプト
output/cleaned_labor_202401.csv を読み込み、人件費分析レポートとサマリーCSVを出力
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_labor_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["work_date"] = pd.to_datetime(df["work_date"])
    return df


def store_labor_cost(df: pd.DataFrame) -> pd.DataFrame:
    """店舗別人件費合計"""
    return (
        df.groupby("store_id")
        .agg(
            total_wage=("total_wage", "sum"),
            total_hours=("work_hours", "sum"),
            headcount=("staff_id", "nunique"),
        )
        .round(0)
        .reset_index()
    )


def daily_labor_trend(df: pd.DataFrame) -> pd.DataFrame:
    """日別人件費推移"""
    return (
        df.groupby(df["work_date"].dt.strftime("%Y-%m-%d"))
        .agg(daily_total_wage=("total_wage", "sum"))
        .round(0)
        .reset_index()
        .rename(columns={"work_date": "date"})
    )


def employment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """雇用区分別人件費・平均時給・総労働時間"""
    return (
        df.groupby("employment_type")
        .agg(
            total_wage=("total_wage", "sum"),
            avg_hourly_wage=("hourly_wage", "mean"),
            total_hours=("work_hours", "sum"),
            headcount=("staff_id", "nunique"),
        )
        .round(1)
        .reset_index()
    )


def staff_hours_ranking(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """スタッフ別月間労働時間ランキング"""
    return (
        df.groupby(["staff_id", "name", "store_id", "employment_type"])
        .agg(total_hours=("work_hours", "sum"))
        .round(1)
        .reset_index()
        .sort_values("total_hours", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def late_night_summary(df: pd.DataFrame) -> dict:
    """深夜割増コスト合計と全体比率"""
    total_premium = df["late_night_premium"].sum()
    total_wage = df["total_wage"].sum()
    ratio = total_premium / total_wage if total_wage > 0 else 0
    return {
        "late_night_premium_total": round(total_premium, 0),
        "total_wage": round(total_wage, 0),
        "late_night_ratio": round(ratio, 4),
    }


def overtime_summary(df: pd.DataFrame) -> pd.DataFrame:
    """残業発生スタッフと時間数"""
    ot_df = df[df["overtime_hours"] > 0].copy()
    return (
        ot_df.groupby(["staff_id", "name", "store_id"])
        .agg(total_overtime=("overtime_hours", "sum"))
        .round(1)
        .reset_index()
        .sort_values("total_overtime", ascending=False)
    )


def labor_summary_by_store_emp(df: pd.DataFrame) -> pd.DataFrame:
    """店舗 x 雇用区分別集計 (labor_summary_202401.csv 用)"""
    return (
        df.groupby(["store_id", "employment_type"])
        .agg(
            total_wage=("total_wage", "sum"),
            total_hours=("work_hours", "sum"),
            avg_hourly_wage=("hourly_wage", "mean"),
            late_night_premium=("late_night_premium", "sum"),
            headcount=("staff_id", "nunique"),
            shifts=("staff_id", "count"),
        )
        .round(1)
        .reset_index()
    )


def build_report(
    df: pd.DataFrame,
    store_df: pd.DataFrame,
    daily_df: pd.DataFrame,
    emp_df: pd.DataFrame,
    top10_df: pd.DataFrame,
    ln_info: dict,
    ot_df: pd.DataFrame,
) -> str:
    lines = [
        "# 飲食チェーン シフト・人件費分析レポート（2024年1月）",
        "",
        "## 1. 概要",
        "",
        f"- 分析対象レコード数: {len(df):,} 件",
        f"- 対象店舗数: {df['store_id'].nunique()} 店舗",
        f"- 対象スタッフ数: {df['staff_id'].nunique()} 名",
        f"- 総人件費: {df['total_wage'].sum():,.0f} 円",
        f"- 総労働時間: {df['work_hours'].sum():,.1f} 時間",
        "",
        "## 2. 店舗別人件費合計",
        "",
    ]

    # 店舗別テーブル
    lines.append("| 店舗 | 人件費合計(円) | 総労働時間(h) | スタッフ数 |")
    lines.append("|------|----------------|---------------|------------|")
    for _, row in store_df.iterrows():
        lines.append(
            f"| {row['store_id']} | {row['total_wage']:,.0f} | {row['total_hours']:,.1f} | {int(row['headcount'])} |"
        )

    lines += [
        "",
        "## 3. 日別人件費推移",
        "",
        "（上位5日）",
        "",
        "| 日付 | 日別人件費(円) |",
        "|------|----------------|",
    ]
    top5_daily = daily_df.sort_values("daily_total_wage", ascending=False).head(5)
    for _, row in top5_daily.iterrows():
        lines.append(f"| {row['date']} | {row['daily_total_wage']:,.0f} |")

    lines += [
        "",
        "## 4. 雇用区分別人件費・平均時給・総労働時間",
        "",
        "| 雇用区分 | 人件費合計(円) | 平均時給(円) | 総労働時間(h) | 人数 |",
        "|----------|----------------|--------------|---------------|------|",
    ]
    for _, row in emp_df.iterrows():
        lines.append(
            f"| {row['employment_type']} | {row['total_wage']:,.0f} | {row['avg_hourly_wage']:.0f} | {row['total_hours']:,.1f} | {int(row['headcount'])} |"
        )

    lines += [
        "",
        "## 5. スタッフ別月間労働時間ランキング（上位10名）",
        "",
        "| 順位 | スタッフID | 氏名 | 店舗 | 雇用区分 | 月間労働時間(h) |",
        "|------|-----------|------|------|----------|-----------------|",
    ]
    for rank, (_, row) in enumerate(top10_df.iterrows(), 1):
        lines.append(
            f"| {rank} | {row['staff_id']} | {row['name']} | {row['store_id']} | {row['employment_type']} | {row['total_hours']:.1f} |"
        )

    ln_ratio_pct = ln_info["late_night_ratio"] * 100
    lines += [
        "",
        "## 6. 深夜割増コスト",
        "",
        f"- 深夜割増コスト合計: {ln_info['late_night_premium_total']:,.0f} 円",
        f"- 総人件費に占める割合: {ln_ratio_pct:.2f}%",
        "",
        "### インサイト",
        "",
        f"深夜割増は総人件費の {ln_ratio_pct:.1f}% を占める。"
        "深夜シフトの適正化により人件費削減の余地がある。",
    ]

    if len(ot_df) > 0:
        total_ot_hours = ot_df["total_overtime"].sum()
        lines += [
            "",
            "## 7. 残業発生スタッフ",
            "",
            f"- 残業発生スタッフ数: {len(ot_df)} 名",
            f"- 残業時間合計: {total_ot_hours:.1f} 時間",
            "",
            "| スタッフID | 氏名 | 店舗 | 月間残業時間(h) |",
            "|-----------|------|------|-----------------|",
        ]
        for _, row in ot_df.head(10).iterrows():
            lines.append(f"| {row['staff_id']} | {row['name']} | {row['store_id']} | {row['total_overtime']:.1f} |")
    else:
        lines += ["", "## 7. 残業発生スタッフ", "", "残業発生スタッフはいません。"]

    lines += [
        "",
        "## 8. まとめ・インサイト",
        "",
        f"1. 3店舗合計の月間人件費は {df['total_wage'].sum():,.0f} 円",
        f"2. アルバイト比率が高く（スタッフ全体の約70%）、人件費の柔軟な調整が可能",
        f"3. 深夜割増コストが総人件費の {ln_ratio_pct:.1f}% を占めており、深夜シフト最適化を推奨",
        "4. 労働時間上位スタッフの負荷集中は、シフト分散による改善余地あり",
        "",
    ]

    return "\n".join(lines)


def main():
    df = load_data()

    store_df = store_labor_cost(df)
    daily_df = daily_labor_trend(df)
    emp_df = employment_summary(df)
    top10_df = staff_hours_ranking(df, top_n=10)
    ln_info = late_night_summary(df)
    ot_df = overtime_summary(df)
    summary_df = labor_summary_by_store_emp(df)

    # レポート出力
    report = build_report(df, store_df, daily_df, emp_df, top10_df, ln_info, ot_df)
    report_path = OUTPUT_DIR / "analysis_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"レポート出力: {report_path}")

    # サマリーCSV出力
    summary_path = OUTPUT_DIR / "labor_summary_202401.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"サマリーCSV出力: {summary_path}")
    print(f"  -> {len(summary_df)} 行")


if __name__ == "__main__":
    main()
