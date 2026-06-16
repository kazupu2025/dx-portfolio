# -*- coding: utf-8 -*-
"""
配送ルート効率化分析スクリプト
クレンジング済みCSVを読み込み、ルート・エリア・車両別の分析を行い
analysis_report.md と route_summary_202401.csv を出力する
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CLEANED_CSV = OUTPUT_DIR / "cleaned_route_202401.csv"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
ROUTE_SUMMARY_CSV = OUTPUT_DIR / "route_summary_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["distance_km", "duration_min", "fuel_cost", "delivery_count",
                "cost_per_km", "cost_per_delivery", "km_per_delivery"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["delay_flag"] = pd.to_numeric(df["delay_flag"], errors="coerce").fillna(0).astype(int)
    return df


def analyze_by_route(df: pd.DataFrame) -> pd.DataFrame:
    """ルート別コスト効率ランキング"""
    summary = df.groupby("route_id").agg(
        total_deliveries=("delivery_count", "sum"),
        total_distance_km=("distance_km", "sum"),
        total_fuel_cost=("fuel_cost", "sum"),
        avg_cost_per_delivery=("cost_per_delivery", "mean"),
        avg_cost_per_km=("cost_per_km", "mean"),
        avg_km_per_delivery=("km_per_delivery", "mean"),
        delay_count=("delay_flag", "sum"),
        run_count=("date", "count"),
    ).reset_index()
    summary["delay_rate"] = summary["delay_count"] / summary["run_count"]
    summary = summary.sort_values("avg_cost_per_delivery").reset_index(drop=True)
    summary["rank"] = summary.index + 1
    return summary


def analyze_by_area(df: pd.DataFrame) -> pd.DataFrame:
    """エリア別配送効率"""
    summary = df.groupby("area").agg(
        total_deliveries=("delivery_count", "sum"),
        total_distance_km=("distance_km", "sum"),
        avg_km_per_delivery=("km_per_delivery", "mean"),
        delay_count=("delay_flag", "sum"),
        run_count=("date", "count"),
    ).reset_index()
    summary["delay_rate"] = summary["delay_count"] / summary["run_count"]
    summary = summary.sort_values("delay_rate", ascending=False)
    return summary


def analyze_by_vehicle(df: pd.DataFrame) -> pd.DataFrame:
    """車両タイプ別コスト比較"""
    summary = df.groupby("vehicle_type").agg(
        run_count=("date", "count"),
        avg_cost_per_delivery=("cost_per_delivery", "mean"),
        avg_cost_per_km=("cost_per_km", "mean"),
        avg_distance_km=("distance_km", "mean"),
        total_fuel_cost=("fuel_cost", "sum"),
        delay_count=("delay_flag", "sum"),
    ).reset_index()
    summary["delay_rate"] = summary["delay_count"] / summary["run_count"]
    return summary


def analyze_delay(df: pd.DataFrame):
    """遅延の多いルート分析"""
    delay_by_route = df.groupby("route_id").agg(
        delay_count=("delay_flag", "sum"),
        run_count=("date", "count"),
    ).reset_index()
    delay_by_route["delay_rate"] = delay_by_route["delay_count"] / delay_by_route["run_count"]
    delay_by_route = delay_by_route.sort_values("delay_rate", ascending=False)

    # 月内の日次遅延傾向
    if "date" in df.columns:
        df2 = df.copy()
        df2["day_of_week"] = df2["date"].dt.day_name()
        delay_by_dow = df2.groupby("day_of_week").agg(
            delay_count=("delay_flag", "sum"),
            run_count=("date", "count"),
        ).reset_index()
        delay_by_dow["delay_rate"] = delay_by_dow["delay_count"] / delay_by_dow["run_count"]
        delay_by_dow = delay_by_dow.sort_values("delay_rate", ascending=False)
    else:
        delay_by_dow = pd.DataFrame()

    return delay_by_route, delay_by_dow


def fmt_float(val, decimals=1) -> str:
    if pd.isna(val):
        return "N/A"
    return f"{val:.{decimals}f}"


def build_report(df: pd.DataFrame, route_summary: pd.DataFrame,
                 area_summary: pd.DataFrame, vehicle_summary: pd.DataFrame,
                 delay_route: pd.DataFrame, delay_dow: pd.DataFrame) -> str:
    lines = []
    lines.append("# 配送ルート効率化分析レポート")
    lines.append("")
    lines.append(f"分析対象期間: {df['date'].min().strftime('%Y-%m-%d')} ～ {df['date'].max().strftime('%Y-%m-%d')}")
    lines.append(f"総レコード数: {len(df):,}件")
    lines.append(f"対象ルート数: {df['route_id'].nunique()}本")
    lines.append(f"対象エリア数: {df['area'].nunique()}エリア")
    lines.append("")

    # KPI
    total_deliveries = int(df["delivery_count"].sum())
    total_fuel = df["fuel_cost"].sum()
    avg_cpd = df["cost_per_delivery"].mean()
    delay_rate = df["delay_flag"].mean()

    lines.append("## 全体KPI")
    lines.append("")
    lines.append(f"- 総配送件数: {total_deliveries:,}件")
    lines.append(f"- 総燃料費: {total_fuel:,.0f}円")
    lines.append(f"- 平均1件当たりコスト: {fmt_float(avg_cpd, 1)}円/件")
    lines.append(f"- 全体遅延率: {delay_rate:.1%}")
    lines.append("")

    # ルート別分析
    lines.append("## ルート別コスト効率ランキング")
    lines.append("")
    lines.append("| ランク | ルートID | 平均1件コスト(円) | 平均距離効率(km/件) | 遅延率 | 総配送件数 |")
    lines.append("|--------|----------|-------------------|---------------------|--------|-----------|")
    for _, row in route_summary.iterrows():
        lines.append(
            f"| {int(row['rank'])} "
            f"| {row['route_id']} "
            f"| {fmt_float(row['avg_cost_per_delivery'], 1)} "
            f"| {fmt_float(row['avg_km_per_delivery'], 2)} "
            f"| {row['delay_rate']:.1%} "
            f"| {int(row['total_deliveries']):,} |"
        )
    lines.append("")

    best_route = route_summary.iloc[0]
    worst_route = route_summary.iloc[-1]
    lines.append("### インサイト（ルート別）")
    lines.append("")
    lines.append(
        f"- 最もコスト効率が高いルートは **{best_route['route_id']}** で、"
        f"1件当たりコストが {fmt_float(best_route['avg_cost_per_delivery'], 1)}円 です。"
    )
    lines.append(
        f"- 最もコストが高いルートは **{worst_route['route_id']}** で、"
        f"1件当たり {fmt_float(worst_route['avg_cost_per_delivery'], 1)}円 となっており、"
        f"改善余地があります。"
    )
    lines.append(
        f"- コスト差は最大 "
        f"{fmt_float(worst_route['avg_cost_per_delivery'] - best_route['avg_cost_per_delivery'], 1)}円/件 あり、"
        f"ルート最適化により大幅なコスト削減が見込めます。"
    )
    lines.append("")

    # エリア別分析
    lines.append("## エリア別配送効率")
    lines.append("")
    lines.append("| エリア | 平均km/件 | 遅延率 | 総配送件数 |")
    lines.append("|--------|-----------|--------|-----------|")
    for _, row in area_summary.iterrows():
        lines.append(
            f"| {row['area']} "
            f"| {fmt_float(row['avg_km_per_delivery'], 2)} "
            f"| {row['delay_rate']:.1%} "
            f"| {int(row['total_deliveries']):,} |"
        )
    lines.append("")

    worst_area = area_summary.iloc[0]
    best_area = area_summary.iloc[-1]
    lines.append("### インサイト（エリア別）")
    lines.append("")
    lines.append(
        f"- 遅延率が最も高いエリアは **{worst_area['area']}** ({worst_area['delay_rate']:.1%}) です。"
        f"渋滞・道路状況・距離の長さが主因と考えられます。"
    )
    lines.append(
        f"- 遅延率が最も低いエリアは **{best_area['area']}** ({best_area['delay_rate']:.1%}) です。"
    )
    lines.append("")

    # 車両タイプ別分析
    lines.append("## 車両タイプ別コスト比較")
    lines.append("")
    lines.append("| 車両タイプ | 平均1件コスト(円) | 平均km単価(円/km) | 遅延率 | 稼働回数 |")
    lines.append("|------------|-------------------|-------------------|--------|---------|")
    for _, row in vehicle_summary.iterrows():
        lines.append(
            f"| {row['vehicle_type']} "
            f"| {fmt_float(row['avg_cost_per_delivery'], 1)} "
            f"| {fmt_float(row['avg_cost_per_km'], 1)} "
            f"| {row['delay_rate']:.1%} "
            f"| {int(row['run_count'])} |"
        )
    lines.append("")
    lines.append("### インサイト（車両別）")
    lines.append("")
    lines.append("- 軽バンは短距離・小口配送に適しているが、件数当たりコストが高い傾向があります。")
    lines.append("- 4tトラックは大量輸送時に1件当たりコストを大幅に低減できます。")
    lines.append("- 配送ボリュームと距離に応じた適切な車両選択がコスト最適化の鍵です。")
    lines.append("")

    # 遅延分析
    lines.append("## 遅延分析")
    lines.append("")
    lines.append("### 遅延の多いルート TOP5")
    lines.append("")
    lines.append("| ルートID | 遅延件数 | 遅延率 |")
    lines.append("|----------|----------|--------|")
    for _, row in delay_route.head(5).iterrows():
        lines.append(
            f"| {row['route_id']} "
            f"| {int(row['delay_count'])} "
            f"| {row['delay_rate']:.1%} |"
        )
    lines.append("")

    if not delay_dow.empty:
        lines.append("### 曜日別遅延率")
        lines.append("")
        lines.append("| 曜日 | 遅延率 |")
        lines.append("|------|--------|")
        for _, row in delay_dow.head(7).iterrows():
            lines.append(f"| {row['day_of_week']} | {row['delay_rate']:.1%} |")
        lines.append("")

    # まとめと改善示唆
    high_delay_routes = delay_route[delay_route["delay_rate"] > 0.25]["route_id"].tolist()
    lines.append("## まとめと改善示唆")
    lines.append("")
    lines.append("### 主要な発見事項")
    lines.append("")
    lines.append(f"1. 全体遅延率は {delay_rate:.1%} であり、改善余地があります。")
    if high_delay_routes:
        lines.append(
            f"2. 高遅延ルート（25%超）: {', '.join(high_delay_routes)} については"
            f"ルート見直しまたは出発時刻の調整を検討してください。"
        )
    lines.append(
        f"3. コスト最優秀ルート {best_route['route_id']} の運行パターンを他ルートへ横展開することで"
        f"全体コストの削減が期待できます。"
    )
    lines.append(
        f"4. {worst_area['area']} エリアの遅延対策として、出発時刻の前倒しや"
        f"代替ルートの検討を推奨します。"
    )
    lines.append("")
    lines.append("### 優先改善アクション")
    lines.append("")
    lines.append(f"- 高コストルート（{worst_route['route_id']}）の配送先統合・ルート再設計")
    lines.append(f"- {worst_area['area']} エリアへの配送時間帯の最適化")
    lines.append("- 軽バンと2tトラックの配送区域の最適配分")
    lines.append("- 遅延発生時のリアルタイム通知システムの導入")
    lines.append("")

    return "\n".join(lines)


def main():
    if not CLEANED_CSV.exists():
        print(f"[ERROR] クレンジング済みCSVが見つかりません: {CLEANED_CSV}")
        return

    print(f"[LOAD] {CLEANED_CSV}")
    df = load_data()
    print(f"[INFO] {len(df)}行 読み込み完了")

    route_summary = analyze_by_route(df)
    area_summary = analyze_by_area(df)
    vehicle_summary = analyze_by_vehicle(df)
    delay_route, delay_dow = analyze_delay(df)

    # ルート別サマリーCSV出力
    route_summary.to_csv(ROUTE_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    print(f"[OUT] ルート別サマリー: {ROUTE_SUMMARY_CSV}")

    # レポートMarkdown出力
    report = build_report(df, route_summary, area_summary, vehicle_summary, delay_route, delay_dow)
    REPORT_MD.write_text(report, encoding="utf-8")
    print(f"[OUT] 分析レポート: {REPORT_MD}")
    print("[DONE] 分析完了")


if __name__ == "__main__":
    main()
