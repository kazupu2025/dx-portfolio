# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
分析スクリプト: クレンジング済みCSVを読み込み、分析結果を output/ に出力する
print文に記号類は使わない
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_reception_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
SUMMARY_CSV_PATH = OUTPUT_DIR / "dept_summary_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def analyze_dept_wait(df: pd.DataFrame) -> pd.DataFrame:
    """診療科別平均待ち時間・長待ち率"""
    summary = df.groupby("department").agg(
        来院件数=("reception_no", "count"),
        平均待ち時間=("wait_minutes", "mean"),
        最大待ち時間=("wait_minutes", "max"),
        平均診察時間=("treat_minutes", "mean"),
    ).round(1).reset_index()

    # 長待ち率
    long_wait_counts = df[df["wait_level"] == "長待ち"].groupby("department").size().reset_index(name="長待ち件数")
    summary = summary.merge(long_wait_counts, on="department", how="left")
    summary["長待ち件数"] = summary["長待ち件数"].fillna(0).astype(int)
    summary["長待ち率(%)"] = (summary["長待ち件数"] / summary["来院件数"] * 100).round(1)

    return summary


def analyze_timeslot(df: pd.DataFrame) -> pd.DataFrame:
    """時間帯別来院件数（ピーク時間帯）"""
    ts_counts = df.groupby("time_slot").agg(
        来院件数=("reception_no", "count"),
        平均待ち時間=("wait_minutes", "mean"),
    ).round(1).reset_index()
    ts_counts = ts_counts.sort_values("time_slot")
    return ts_counts


def analyze_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """曜日別来院傾向"""
    weekday_map = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}
    df = df.copy()
    df["visit_date_dt"] = pd.to_datetime(df["visit_date"], format="%Y-%m-%d")
    df["weekday"] = df["visit_date_dt"].dt.dayofweek.map(weekday_map)
    df["weekday_no"] = df["visit_date_dt"].dt.dayofweek

    weekday_counts = df.groupby(["weekday_no", "weekday"]).agg(
        来院件数=("reception_no", "count"),
        平均待ち時間=("wait_minutes", "mean"),
    ).round(1).reset_index().sort_values("weekday_no")
    weekday_counts = weekday_counts.drop(columns=["weekday_no"])
    return weekday_counts


def analyze_long_wait_alert(dept_summary: pd.DataFrame) -> pd.DataFrame:
    """長待ち上位診療科アラート"""
    alert = dept_summary.sort_values("長待ち率(%)", ascending=False).head(3)
    return alert[["department", "来院件数", "平均待ち時間", "長待ち件数", "長待ち率(%)"]]


def build_dept_summary(df: pd.DataFrame) -> pd.DataFrame:
    """診療科別サマリーCSV用"""
    return analyze_dept_wait(df)


def build_report(
    dept_summary: pd.DataFrame,
    ts_counts: pd.DataFrame,
    weekday_counts: pd.DataFrame,
    alert_depts: pd.DataFrame,
    df: pd.DataFrame,
) -> str:
    total_visits = len(df)
    avg_wait = df["wait_minutes"].mean()
    long_wait_count = (df["wait_level"] == "長待ち").sum()
    long_wait_rate = long_wait_count / total_visits * 100 if total_visits > 0 else 0
    avg_treat = df["treat_minutes"].mean()

    # ピーク時間帯
    peak_slot = ts_counts.sort_values("来院件数", ascending=False).iloc[0] if len(ts_counts) > 0 else None

    lines = []
    lines.append("# 来院スループット分析レポート")
    lines.append("")
    lines.append("## 概要")
    lines.append("")
    lines.append(f"- 分析対象レコード数: {total_visits} 件")
    lines.append(f"- 平均待ち時間: {avg_wait:.1f} 分")
    lines.append(f"- 長待ち件数: {long_wait_count} 件 ({long_wait_rate:.1f}%)")
    lines.append(f"- 平均診察時間: {avg_treat:.1f} 分")
    lines.append("")

    lines.append("## 診療科別待ち時間サマリー")
    lines.append("")
    lines.append(dept_summary.to_markdown(index=False))
    lines.append("")

    lines.append("## 時間帯別来院件数")
    lines.append("")
    lines.append(ts_counts.to_markdown(index=False))
    lines.append("")

    lines.append("## 曜日別来院傾向")
    lines.append("")
    lines.append(weekday_counts.to_markdown(index=False))
    lines.append("")

    lines.append("## 長待ち上位診療科アラート")
    lines.append("")
    lines.append(alert_depts.to_markdown(index=False))
    lines.append("")

    lines.append("## インサイト・改善示唆")
    lines.append("")

    if peak_slot is not None:
        lines.append(f"1. **ピーク時間帯**: {peak_slot['time_slot']} が最多来院件数"
                     f"（{int(peak_slot['来院件数'])} 件）。この時間帯への受付スタッフ増員を推奨する。")

    if len(alert_depts) > 0:
        top_dept = alert_depts.iloc[0]
        lines.append(f"2. **長待ち診療科**: {top_dept['department']} が長待ち率"
                     f" {top_dept['長待ち率(%)']:.1f}% で最高。診察枠の拡張や予約制導入を検討すること。")

    lines.append(f"3. **全体待ち時間**: 平均 {avg_wait:.1f} 分。30分超えが全体の"
                 f" {((df['wait_minutes'] > 30).sum() / total_visits * 100):.1f}% を占める。"
                 f"トリアージ運用の改善が効果的。")

    if len(weekday_counts) > 0:
        peak_day = weekday_counts.sort_values("来院件数", ascending=False).iloc[0]
        lines.append(f"4. **曜日別ピーク**: {peak_day['weekday']}曜日が最多来院（{int(peak_day['来院件数'])} 件）。"
                     f"人員配置計画の最適化に活用できる。")

    lines.append("")
    lines.append("## まとめ")
    lines.append("")
    lines.append(
        f"本分析では {total_visits} 件の来院記録を対象とした。"
        f"平均待ち時間 {avg_wait:.1f} 分、長待ち率 {long_wait_rate:.1f}% が確認された。"
        f"ピーク時間帯への集中対応と長待ち診療科への構造的改善により、"
        f"患者満足度の向上とスループット効率化が期待できる。"
    )
    lines.append("")

    return "\n".join(lines)


def main():
    print("[INFO] 分析開始...")

    df = load_data()
    print(f"[INFO] データ読み込み: {len(df)} 件")

    dept_summary = analyze_dept_wait(df)
    ts_counts = analyze_timeslot(df)
    weekday_counts = analyze_weekday(df)
    alert_depts = analyze_long_wait_alert(dept_summary)

    # レポート出力
    report_text = build_report(dept_summary, ts_counts, weekday_counts, alert_depts, df)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    print(f"[OK] レポート出力: {REPORT_PATH}")

    # 診療科別サマリーCSV出力
    dept_summary.to_csv(SUMMARY_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] 診療科別サマリーCSV出力: {SUMMARY_CSV_PATH} ({len(dept_summary)} 件)")


if __name__ == "__main__":
    main()
