"""
C-22 ドライバー勤怠・拘束時間管理パイプライン
分析スクリプト
- ドライバー別違反件数ランキング
- 営業所別違反率・平均拘束時間
- 運行区分別距離・時間
- 月間違反件数推移
出力: output/analysis_report.md, output/driver_summary_202401.csv
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_driver_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV_PATH = OUTPUT_DIR / "driver_summary_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["work_date"] = pd.to_datetime(df["work_date"], errors="coerce")
    df["confinement_over_flag"] = df["confinement_over_flag"].astype(bool)
    df["work_over_flag"] = df["work_over_flag"].astype(bool)
    return df


def driver_violation_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """ドライバー別違反件数ランキング"""
    grp = df.groupby(["driver_id", "name", "office"]).agg(
        total_rides=("work_date", "count"),
        violation_count=("violation_flag", lambda x: (x == "違反").sum()),
        confinement_over=("confinement_over_flag", "sum"),
        work_over=("work_over_flag", "sum"),
        avg_confinement_hours=("confinement_hours", "mean"),
        avg_work_hours=("work_hours", "mean"),
        avg_distance_km=("distance_km", "mean"),
    ).reset_index()
    grp["violation_rate"] = (grp["violation_count"] / grp["total_rides"]).round(4)
    grp["avg_confinement_hours"] = grp["avg_confinement_hours"].round(2)
    grp["avg_work_hours"] = grp["avg_work_hours"].round(2)
    grp["avg_distance_km"] = grp["avg_distance_km"].round(1)
    grp = grp.sort_values("violation_count", ascending=False).reset_index(drop=True)
    grp["rank"] = grp.index + 1
    return grp


def office_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """営業所別違反率・平均拘束時間"""
    grp = df.groupby("office").agg(
        total_rides=("work_date", "count"),
        violation_count=("violation_flag", lambda x: (x == "違反").sum()),
        avg_confinement_hours=("confinement_hours", "mean"),
        avg_work_hours=("work_hours", "mean"),
        avg_distance_km=("distance_km", "mean"),
    ).reset_index()
    grp["violation_rate"] = (grp["violation_count"] / grp["total_rides"]).round(4)
    grp["avg_confinement_hours"] = grp["avg_confinement_hours"].round(2)
    grp["avg_work_hours"] = grp["avg_work_hours"].round(2)
    grp["avg_distance_km"] = grp["avg_distance_km"].round(1)
    grp = grp.sort_values("violation_rate", ascending=False)
    return grp


def operation_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """運行区分別距離・時間"""
    grp = df.groupby("operation_type").agg(
        total_rides=("work_date", "count"),
        violation_count=("violation_flag", lambda x: (x == "違反").sum()),
        avg_distance_km=("distance_km", "mean"),
        avg_confinement_hours=("confinement_hours", "mean"),
        avg_work_hours=("work_hours", "mean"),
        total_distance_km=("distance_km", "sum"),
    ).reset_index()
    grp["violation_rate"] = (grp["violation_count"] / grp["total_rides"]).round(4)
    grp["avg_distance_km"] = grp["avg_distance_km"].round(1)
    grp["avg_confinement_hours"] = grp["avg_confinement_hours"].round(2)
    grp["avg_work_hours"] = grp["avg_work_hours"].round(2)
    grp["total_distance_km"] = grp["total_distance_km"].round(1)
    return grp


def monthly_violation_trend(df: pd.DataFrame) -> pd.DataFrame:
    """月間違反件数推移（日別）"""
    df2 = df.copy()
    df2["work_day"] = df2["work_date"].dt.day
    grp = df2.groupby("work_day").agg(
        total_rides=("driver_id", "count"),
        violation_count=("violation_flag", lambda x: (x == "違反").sum()),
    ).reset_index()
    grp["violation_rate"] = (grp["violation_count"] / grp["total_rides"]).round(4)
    return grp.sort_values("work_day")


def build_report(df, driver_df, office_df, op_df, trend_df) -> str:
    total_rides = len(df)
    total_violations = (df["violation_flag"] == "違反").sum()
    violation_rate = total_violations / total_rides if total_rides > 0 else 0
    avg_conf = df["confinement_hours"].mean()
    avg_work = df["work_hours"].mean()

    lines = []
    lines.append("# C-22 ドライバー勤怠・拘束時間管理レポート（2024年1月）\n")
    lines.append(f"生成日時: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")

    lines.append("## 1. サマリー\n")
    lines.append(f"- 総乗務件数: **{total_rides:,}件**")
    lines.append(f"- 違反件数: **{total_violations:,}件**")
    lines.append(f"- 違反率: **{violation_rate:.1%}**")
    lines.append(f"- 平均拘束時間: **{avg_conf:.2f}時間**")
    lines.append(f"- 平均実労働時間: **{avg_work:.2f}時間**\n")

    lines.append("## 2. ドライバー別違反件数ランキング（上位10名）\n")
    lines.append("| 順位 | ドライバーID | 氏名 | 営業所 | 違反件数 | 乗務件数 | 違反率 | 平均拘束時間 |")
    lines.append("|------|-------------|------|--------|---------|---------|-------|------------|")
    for _, row in driver_df.head(10).iterrows():
        lines.append(
            f"| {row['rank']} | {row['driver_id']} | {row['name']} | {row['office']} "
            f"| {row['violation_count']} | {row['total_rides']} "
            f"| {row['violation_rate']:.1%} | {row['avg_confinement_hours']:.1f}h |"
        )
    lines.append("")

    lines.append("## 3. 営業所別違反率・平均拘束時間\n")
    lines.append("| 営業所 | 乗務件数 | 違反件数 | 違反率 | 平均拘束時間 | 平均実労働時間 |")
    lines.append("|--------|---------|---------|-------|------------|-------------|")
    for _, row in office_df.iterrows():
        lines.append(
            f"| {row['office']} | {row['total_rides']} | {row['violation_count']} "
            f"| {row['violation_rate']:.1%} | {row['avg_confinement_hours']:.2f}h "
            f"| {row['avg_work_hours']:.2f}h |"
        )
    lines.append("")

    lines.append("## 4. 運行区分別距離・時間\n")
    lines.append("| 運行区分 | 乗務件数 | 違反件数 | 違反率 | 平均距離km | 平均拘束時間 | 総走行距離km |")
    lines.append("|---------|---------|---------|-------|----------|------------|-----------|")
    for _, row in op_df.iterrows():
        lines.append(
            f"| {row['operation_type']} | {row['total_rides']} | {row['violation_count']} "
            f"| {row['violation_rate']:.1%} | {row['avg_distance_km']:.1f} "
            f"| {row['avg_confinement_hours']:.2f}h | {row['total_distance_km']:,.1f} |"
        )
    lines.append("")

    lines.append("## 5. 月間違反件数推移（日別）\n")
    lines.append("| 日 | 乗務件数 | 違反件数 | 違反率 |")
    lines.append("|---|---------|---------|-------|")
    for _, row in trend_df.iterrows():
        lines.append(
            f"| {int(row['work_day'])}日 | {row['total_rides']} "
            f"| {row['violation_count']} | {row['violation_rate']:.1%} |"
        )
    lines.append("")

    # インサイト
    worst_office = office_df.iloc[0]["office"]
    worst_driver = driver_df.iloc[0]["name"]
    worst_op = op_df.sort_values("violation_rate", ascending=False).iloc[0]["operation_type"]
    lines.append("## 6. インサイトと改善提案\n")
    lines.append(
        f"1. **違反リスクの高い営業所**: {worst_office}は違反率が最も高い。"
        "運行管理体制の強化と定期的な点呼確認が必要。"
    )
    lines.append(
        f"2. **要注意ドライバー**: {worst_driver}は違反件数トップ。"
        "個別の労働時間管理と健康管理を優先的に実施する。"
    )
    lines.append(
        f"3. **運行区分別対策**: {worst_op}は拘束時間違反が多い。"
        "ルートの見直しや中継地点の設定を検討する。"
    )
    lines.append(
        "4. **休憩時間確保**: 実労働時間の超過を防ぐため、休憩時間を適切に確保する仕組みを導入する。"
    )
    lines.append(
        "5. **デジタルタコグラフ活用**: 勤怠データのリアルタイム収集により、"
        "翌日以降の違反を未然に防ぐアラート体制を構築する。\n"
    )

    return "\n".join(lines)


def main():
    print("[INFO] データ読み込み中...")
    df = load_data()
    print(f"  {len(df)} rows loaded")

    print("[INFO] 分析中...")
    driver_df = driver_violation_ranking(df)
    office_df = office_analysis(df)
    op_df = operation_analysis(df)
    trend_df = monthly_violation_trend(df)

    # ドライバーサマリーCSV出力
    summary_cols = [
        "rank", "driver_id", "name", "office",
        "total_rides", "violation_count", "violation_rate",
        "confinement_over", "work_over",
        "avg_confinement_hours", "avg_work_hours", "avg_distance_km",
    ]
    driver_df[summary_cols].to_csv(SUMMARY_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] ドライバーサマリーCSV: {SUMMARY_CSV_PATH}")

    # レポート生成
    report = build_report(df, driver_df, office_df, op_df, trend_df)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"[OK] レポート: {REPORT_PATH}")


if __name__ == "__main__":
    main()
