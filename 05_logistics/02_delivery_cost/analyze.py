"""
C-17 配送コスト分析パイプライン
分析スクリプト
- ルート別コスト効率
- 車種別コスト
- 月間内訳
- 遅延・キャンセル率
- コスト削減余地
出力: output/analysis_report.md, output/cost_analysis_202401.csv
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_delivery_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
ANALYSIS_CSV_PATH = OUTPUT_DIR / "cost_analysis_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def route_cost_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("route_id").agg(
        avg_cost_per_km=("cost_per_km", "mean"),
        avg_total_cost=("total_cost", "mean"),
        total_deliveries=("delivery_count", "sum"),
        record_count=("delivery_id", "count"),
    ).round(2).reset_index()
    grp["cost_efficiency_rank"] = grp["avg_cost_per_km"].rank().astype(int)
    return grp.sort_values("avg_cost_per_km")


def vehicle_cost_analysis(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("vehicle_type").agg(
        avg_fuel_cost=("fuel_cost", "mean"),
        avg_toll_cost=("toll_cost", "mean"),
        avg_driver_cost=("driver_cost", "mean"),
        avg_total_cost=("total_cost", "mean"),
        total_deliveries=("delivery_count", "sum"),
        record_count=("delivery_id", "count"),
    ).round(0).reset_index()
    grp["avg_cost_per_delivery"] = (grp["avg_total_cost"] / grp["avg_total_cost"].count()).round(0)
    # 正しい計算
    vehicle_cpd = df.groupby("vehicle_type")["cost_per_delivery"].mean().round(0).reset_index()
    vehicle_cpd.columns = ["vehicle_type", "avg_cost_per_delivery"]
    grp = grp.drop(columns=["avg_cost_per_delivery"]).merge(vehicle_cpd, on="vehicle_type")
    return grp


def monthly_cost_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    monthly = pd.DataFrame({
        "month": ["2024-01"],
        "total_fuel_cost": [df["fuel_cost"].sum()],
        "total_toll_cost": [df["toll_cost"].sum()],
        "total_driver_cost": [df["driver_cost"].sum()],
        "total_cost": [df["total_cost"].sum()],
        "total_records": [len(df)],
        "total_deliveries": [df["delivery_count"].sum()],
    })
    monthly = monthly.round(0)
    return monthly


def delay_cancel_rate(df: pd.DataFrame) -> dict:
    total = len(df)
    delay_rate = (df["status"] == "遅延").sum() / total
    cancel_rate = (df["status"] == "キャンセル").sum() / total
    complete_rate = (df["status"] == "完了").sum() / total
    return {
        "total_records": total,
        "complete_rate": round(complete_rate, 4),
        "delay_rate": round(delay_rate, 4),
        "cancel_rate": round(cancel_rate, 4),
    }


def cost_reduction_opportunities(df: pd.DataFrame, route_df: pd.DataFrame) -> pd.DataFrame:
    overall_avg = df["cost_per_km"].mean()
    expensive = route_df[route_df["avg_cost_per_km"] > overall_avg].copy()
    expensive["excess_cost_per_km"] = expensive["avg_cost_per_km"] - overall_avg
    expensive["reduction_potential_pct"] = (expensive["excess_cost_per_km"] / expensive["avg_cost_per_km"] * 100).round(1)
    return expensive[["route_id", "avg_cost_per_km", "excess_cost_per_km", "reduction_potential_pct"]]


def build_report(df, route_df, vehicle_df, monthly_df, rates, reduction_df) -> str:
    overall_avg_cpk = df["cost_per_km"].mean()
    lines = []
    lines.append("# C-17 配送コスト分析レポート（2024年1月）\n")
    lines.append(f"生成日時: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")

    lines.append("## 1. サマリー\n")
    lines.append(f"- 総レコード数: **{rates['total_records']:,}件**")
    lines.append(f"- 月間総コスト: **¥{monthly_df['total_cost'].iloc[0]:,.0f}**")
    lines.append(f"  - 燃料費: ¥{monthly_df['total_fuel_cost'].iloc[0]:,.0f}")
    lines.append(f"  - 高速代: ¥{monthly_df['total_toll_cost'].iloc[0]:,.0f}")
    lines.append(f"  - 人件費: ¥{monthly_df['total_driver_cost'].iloc[0]:,.0f}")
    lines.append(f"- 総配送件数: **{monthly_df['total_deliveries'].iloc[0]:,.0f}件**")
    lines.append(f"- 平均 cost_per_km: **¥{overall_avg_cpk:.2f}/km**\n")

    lines.append("## 2. ルート別コスト効率（cost_per_km）\n")
    lines.append("| ルート | 平均cost_per_km (¥/km) | 平均総コスト (¥) | 配送件数 |")
    lines.append("|--------|------------------------|-----------------|---------|")
    for _, row in route_df.iterrows():
        lines.append(f"| {row['route_id']} | {row['avg_cost_per_km']:.2f} | {row['avg_total_cost']:,.0f} | {row['total_deliveries']:,.0f} |")
    lines.append("")

    lines.append("## 3. 車種別コスト分析\n")
    lines.append("| 車種 | 平均燃料費 | 平均高速代 | 平均人件費 | 平均総コスト | 平均1件あたりコスト |")
    lines.append("|------|-----------|-----------|-----------|------------|-------------------|")
    for _, row in vehicle_df.iterrows():
        lines.append(
            f"| {row['vehicle_type']} | ¥{row['avg_fuel_cost']:,.0f} | ¥{row['avg_toll_cost']:,.0f} | "
            f"¥{row['avg_driver_cost']:,.0f} | ¥{row['avg_total_cost']:,.0f} | ¥{row['avg_cost_per_delivery']:,.0f} |"
        )
    lines.append("")

    lines.append("## 4. 月間コスト内訳（2024年1月）\n")
    total = monthly_df['total_cost'].iloc[0]
    fuel_pct = monthly_df['total_fuel_cost'].iloc[0] / total * 100
    toll_pct = monthly_df['total_toll_cost'].iloc[0] / total * 100
    driver_pct = monthly_df['total_driver_cost'].iloc[0] / total * 100
    lines.append(f"- 燃料費: ¥{monthly_df['total_fuel_cost'].iloc[0]:,.0f}（{fuel_pct:.1f}%）")
    lines.append(f"- 高速代: ¥{monthly_df['total_toll_cost'].iloc[0]:,.0f}（{toll_pct:.1f}%）")
    lines.append(f"- 人件費: ¥{monthly_df['total_driver_cost'].iloc[0]:,.0f}（{driver_pct:.1f}%）")
    lines.append(f"- 合計: ¥{total:,.0f}\n")

    lines.append("## 5. 配送ステータス分析\n")
    lines.append(f"- 完了率: **{rates['complete_rate']:.1%}**")
    lines.append(f"- 遅延率: **{rates['delay_rate']:.1%}**")
    lines.append(f"- キャンセル率: **{rates['cancel_rate']:.1%}**\n")

    lines.append("## 6. コスト削減余地（平均以上のルート）\n")
    lines.append(f"全体平均 cost_per_km: ¥{overall_avg_cpk:.2f}/km\n")
    if len(reduction_df) > 0:
        lines.append("| ルート | 現状 cost_per_km | 超過分 | 削減余地 |")
        lines.append("|--------|----------------|--------|---------|")
        for _, row in reduction_df.iterrows():
            lines.append(
                f"| {row['route_id']} | ¥{row['avg_cost_per_km']:.2f} | "
                f"¥{row['excess_cost_per_km']:.2f} | {row['reduction_potential_pct']:.1f}% |"
            )
        lines.append("")
    else:
        lines.append("全ルートが平均以下です。\n")

    lines.append("## 7. インサイトと改善提案\n")
    most_eff = route_df.iloc[0]["route_id"]
    least_eff = route_df.iloc[-1]["route_id"]
    lines.append(f"1. **最効率ルート**: {most_eff}（cost_per_km最小）を他ルートのベンチマークとして活用する。")
    lines.append(f"2. **高コストルート改善**: {least_eff}は平均よりコストが高い。積載効率向上や経路最適化を検討する。")
    lines.append(f"3. **遅延対策**: 遅延率{rates['delay_rate']:.1%}の原因分析（交通渋滞・積み込み時間）を実施し、改善余地を特定する。")
    lines.append("4. **燃料費削減**: エコドライブ研修や燃費の良い車両への切り替えで燃料費を削減できる可能性がある。")
    lines.append("5. **高速代の最適化**: 通行パターンを分析し、深夜割引や回数券の活用を検討する。\n")

    return "\n".join(lines)


def main():
    print("[INFO] データ読み込み中...")
    df = load_data()
    print(f"  {len(df)} rows loaded")

    print("[INFO] 分析中...")
    route_df = route_cost_efficiency(df)
    vehicle_df = vehicle_cost_analysis(df)
    monthly_df = monthly_cost_breakdown(df)
    rates = delay_cancel_rate(df)
    reduction_df = cost_reduction_opportunities(df, route_df)

    # 集計CSVの作成
    summary_records = []
    for _, row in route_df.iterrows():
        summary_records.append({
            "category": "route",
            "name": row["route_id"],
            "avg_cost_per_km": row["avg_cost_per_km"],
            "avg_total_cost": row["avg_total_cost"],
            "total_deliveries": row["total_deliveries"],
            "record_count": row["record_count"],
        })
    for _, row in vehicle_df.iterrows():
        summary_records.append({
            "category": "vehicle",
            "name": row["vehicle_type"],
            "avg_cost_per_km": None,
            "avg_total_cost": row["avg_total_cost"],
            "total_deliveries": row["total_deliveries"],
            "record_count": row["record_count"],
        })
    summary_df = pd.DataFrame(summary_records)
    summary_df.to_csv(ANALYSIS_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] 集計CSV: {ANALYSIS_CSV_PATH}")

    # レポート生成
    report = build_report(df, route_df, vehicle_df, monthly_df, rates, reduction_df)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"[OK] レポート: {REPORT_PATH}")


if __name__ == "__main__":
    main()
