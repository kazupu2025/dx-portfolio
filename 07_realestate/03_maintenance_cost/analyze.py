"""
C-23: 分析スクリプト
output/cleaned_maintenance_202401.csv を読み込み、コスト分析レポートとサマリーCSVを出力
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_maintenance_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["occurrence_date"] = pd.to_datetime(df["occurrence_date"])
    return df


def area_cost_summary(df: pd.DataFrame) -> pd.DataFrame:
    """エリア別コスト合計"""
    return (
        df.groupby("area")
        .agg(
            total_cost=("cost_amount", "sum"),
            record_count=("cost_amount", "count"),
            avg_cost=("cost_amount", "mean"),
        )
        .round(0)
        .reset_index()
        .sort_values("total_cost", ascending=False)
    )


def property_type_cost_summary(df: pd.DataFrame) -> pd.DataFrame:
    """物件種別別コスト合計"""
    return (
        df.groupby("property_type")
        .agg(
            total_cost=("cost_amount", "sum"),
            record_count=("cost_amount", "count"),
            avg_cost=("cost_amount", "mean"),
        )
        .round(0)
        .reset_index()
        .sort_values("total_cost", ascending=False)
    )


def cost_category_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """費用区分別コスト構成比"""
    cat_cost = df.groupby("cost_category")["cost_amount"].sum().reset_index()
    cat_cost.columns = ["cost_category", "total_cost"]
    total = cat_cost["total_cost"].sum()
    cat_cost["ratio_pct"] = (cat_cost["total_cost"] / total * 100).round(2)
    return cat_cost.sort_values("total_cost", ascending=False)


def high_cost_property_ranking(df: pd.DataFrame, threshold: int = 500000, top_n: int = 10) -> pd.DataFrame:
    """高額修繕（50万超）物件ランキング"""
    high_df = df[df["cost_amount"] > threshold].copy()
    return (
        high_df.groupby(["property_id", "property_name", "area", "property_type"])
        .agg(
            high_cost_total=("cost_amount", "sum"),
            high_cost_count=("cost_amount", "count"),
        )
        .round(0)
        .reset_index()
        .sort_values("high_cost_total", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def urgent_cost_summary(df: pd.DataFrame) -> dict:
    """緊急対応コスト合計・比率"""
    urgent_df = df[df["is_urgent"] == True]
    urgent_total = urgent_df["cost_amount"].sum()
    all_total = df["cost_amount"].sum()
    ratio = urgent_total / all_total if all_total > 0 else 0
    return {
        "urgent_cost_total": round(urgent_total, 0),
        "all_cost_total": round(all_total, 0),
        "urgent_ratio": round(ratio, 4),
        "urgent_count": len(urgent_df),
    }


def monthly_cost_trend(df: pd.DataFrame) -> pd.DataFrame:
    """月間コスト推移（日別）"""
    return (
        df.groupby(df["occurrence_date"].dt.strftime("%Y-%m-%d"))
        .agg(daily_total_cost=("cost_amount", "sum"))
        .round(0)
        .reset_index()
        .rename(columns={"occurrence_date": "date"})
    )


def property_summary(df: pd.DataFrame) -> pd.DataFrame:
    """物件ID別集計 (property_summary_202401.csv 用)"""
    return (
        df.groupby(["property_id", "property_name", "area", "property_type"])
        .agg(
            total_cost=("cost_amount", "sum"),
            record_count=("cost_amount", "count"),
            avg_cost=("cost_amount", "mean"),
            repair_cost=("cost_amount", lambda x: x[df.loc[x.index, "is_repair"]].sum()),
            urgent_count=("is_urgent", "sum"),
            high_cost_count=("cost_per_unit_flag", lambda x: (x == "高額").sum()),
        )
        .round(0)
        .reset_index()
        .sort_values("total_cost", ascending=False)
    )


def build_report(
    df: pd.DataFrame,
    area_df: pd.DataFrame,
    type_df: pd.DataFrame,
    cat_df: pd.DataFrame,
    high_df: pd.DataFrame,
    urgent_info: dict,
    daily_df: pd.DataFrame,
) -> str:
    lines = [
        "# 不動産 管理費・修繕費コスト分析レポート（2024年1月）",
        "",
        "## 1. 概要",
        "",
        f"- 分析対象レコード数: {len(df):,} 件",
        f"- 対象物件数: {df['property_id'].nunique()} 棟",
        f"- 対象エリア数: {df['area'].nunique()} エリア",
        f"- 総コスト: {df['cost_amount'].sum():,.0f} 円",
        f"- 修繕費合計: {df[df['is_repair']]['cost_amount'].sum():,.0f} 円",
        "",
        "## 2. エリア別コスト合計",
        "",
        "| エリア | コスト合計(円) | 件数 | 平均コスト(円) |",
        "|--------|----------------|------|----------------|",
    ]
    for _, row in area_df.iterrows():
        lines.append(
            f"| {row['area']} | {row['total_cost']:,.0f} | {int(row['record_count'])} | {row['avg_cost']:,.0f} |"
        )

    lines += [
        "",
        "## 3. 物件種別別コスト合計",
        "",
        "| 物件種別 | コスト合計(円) | 件数 | 平均コスト(円) |",
        "|----------|----------------|------|----------------|",
    ]
    for _, row in type_df.iterrows():
        lines.append(
            f"| {row['property_type']} | {row['total_cost']:,.0f} | {int(row['record_count'])} | {row['avg_cost']:,.0f} |"
        )

    lines += [
        "",
        "## 4. 費用区分別コスト構成比",
        "",
        "| 費用区分 | コスト合計(円) | 構成比(%) |",
        "|----------|----------------|-----------|",
    ]
    for _, row in cat_df.iterrows():
        lines.append(
            f"| {row['cost_category']} | {row['total_cost']:,.0f} | {row['ratio_pct']:.2f}% |"
        )

    lines += [
        "",
        "## 5. 高額修繕（50万超）物件ランキング（上位10棟）",
        "",
        "| 順位 | 物件ID | 物件名 | エリア | 種別 | 高額コスト合計(円) | 件数 |",
        "|------|--------|--------|--------|------|-------------------|------|",
    ]
    for rank, (_, row) in enumerate(high_df.iterrows(), 1):
        lines.append(
            f"| {rank} | {row['property_id']} | {row['property_name']} | {row['area']} | {row['property_type']} | {row['high_cost_total']:,.0f} | {int(row['high_cost_count'])} |"
        )

    urgent_ratio_pct = urgent_info["urgent_ratio"] * 100
    lines += [
        "",
        "## 6. 緊急対応コスト",
        "",
        f"- 緊急対応コスト合計: {urgent_info['urgent_cost_total']:,.0f} 円",
        f"- 総コストに占める割合: {urgent_ratio_pct:.2f}%",
        f"- 緊急対応件数: {urgent_info['urgent_count']} 件",
        "",
        "### インサイト",
        "",
        f"緊急対応コストは総コストの {urgent_ratio_pct:.1f}% を占める。"
        "予防保全の強化により緊急修繕費の削減余地がある。",
        "",
        "## 7. 月間コスト推移（上位5日）",
        "",
        "| 日付 | 日別コスト(円) |",
        "|------|----------------|",
    ]
    top5_daily = daily_df.sort_values("daily_total_cost", ascending=False).head(5)
    for _, row in top5_daily.iterrows():
        lines.append(f"| {row['date']} | {row['daily_total_cost']:,.0f} |")

    total_cost = df["cost_amount"].sum()
    repair_cost = df[df["is_repair"]]["cost_amount"].sum()
    repair_ratio = repair_cost / total_cost * 100 if total_cost > 0 else 0
    top_area = area_df.iloc[0]["area"] if len(area_df) > 0 else "N/A"

    lines += [
        "",
        "## 8. まとめ・インサイト",
        "",
        f"1. 物件{df['property_id'].nunique()}棟の月間総コストは {total_cost:,.0f} 円",
        f"2. 修繕費（定期・緊急）の合計は {repair_cost:,.0f} 円（全体の {repair_ratio:.1f}%）",
        f"3. コスト最多エリアは {top_area} であり、集中的な管理計画の見直しを推奨",
        f"4. 緊急対応コストは総コストの {urgent_ratio_pct:.1f}% を占め、計画修繕への移行が有効",
        "5. 高額案件の物件は優先的な予防保全投資の検討対象とすること",
        "",
    ]

    return "\n".join(lines)


def main():
    df = load_data()

    area_df = area_cost_summary(df)
    type_df = property_type_cost_summary(df)
    cat_df = cost_category_ratio(df)
    high_df = high_cost_property_ranking(df)
    urgent_info = urgent_cost_summary(df)
    daily_df = monthly_cost_trend(df)
    prop_summary_df = property_summary(df)

    # レポート出力
    report = build_report(df, area_df, type_df, cat_df, high_df, urgent_info, daily_df)
    report_path = OUTPUT_DIR / "analysis_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"レポート出力: {report_path}")

    # サマリーCSV出力
    summary_path = OUTPUT_DIR / "property_summary_202401.csv"
    prop_summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"サマリーCSV出力: {summary_path}")
    print(f"  -> {len(prop_summary_df)} 行")


if __name__ == "__main__":
    main()
