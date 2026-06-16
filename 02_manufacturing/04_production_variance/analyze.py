# -*- coding: utf-8 -*-
"""
C-25: 生産計画 vs 実績 差異分析パイプライン
分析スクリプト

クレンジング済みCSVを読み込み、各種集計・分析を行い、
Markdownレポートとライン別サマリーCSVを出力する。
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CLEANED_CSV = OUTPUT_DIR / "cleaned_production_202401.csv"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
LINE_SUMMARY_CSV = OUTPUT_DIR / "line_summary_202401.csv"


def load_data() -> pd.DataFrame:
    if not CLEANED_CSV.exists():
        raise FileNotFoundError(f"クレンジング済みCSVが見つかりません: {CLEANED_CSV}")
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig", parse_dates=["date"])
    return df


def analyze_by_line(df: pd.DataFrame) -> pd.DataFrame:
    """ライン別達成率・不良率・差異数量の集計"""
    grp = df.groupby("line_name").agg(
        planned_qty_sum=("planned_qty", "sum"),
        actual_qty_sum=("actual_qty", "sum"),
        defect_qty_sum=("defect_qty", "sum"),
        variance_qty_sum=("variance_qty", "sum"),
        achievement_rate_mean=("achievement_rate", "mean"),
        defect_rate_mean=("defect_rate", "mean"),
        work_hours_sum=("work_hours", "sum"),
        record_count=("date", "count"),
    ).reset_index()
    grp["overall_achievement_rate"] = grp["actual_qty_sum"] / grp["planned_qty_sum"]
    grp["overall_defect_rate"] = grp["defect_qty_sum"] / grp["actual_qty_sum"]
    grp = grp.sort_values("overall_achievement_rate", ascending=False)
    return grp


def analyze_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ別生産効率の集計"""
    grp = df.groupby("category").agg(
        planned_qty_sum=("planned_qty", "sum"),
        actual_qty_sum=("actual_qty", "sum"),
        defect_qty_sum=("defect_qty", "sum"),
        achievement_rate_mean=("achievement_rate", "mean"),
        defect_rate_mean=("defect_rate", "mean"),
    ).reset_index()
    grp["overall_achievement_rate"] = grp["actual_qty_sum"] / grp["planned_qty_sum"]
    grp["overall_defect_rate"] = grp["defect_qty_sum"] / grp["actual_qty_sum"]
    return grp


def underperforming_lines(df: pd.DataFrame) -> pd.DataFrame:
    """未達ラインのランキング（achievement_rate昇順）"""
    under = df[df["achievement_flag"] == "未達"].groupby("line_name").agg(
        under_count=("achievement_flag", "count"),
        avg_achievement_rate=("achievement_rate", "mean"),
    ).reset_index().sort_values("avg_achievement_rate", ascending=True)
    return under


def daily_trend(df: pd.DataFrame) -> pd.DataFrame:
    """日別生産トレンド"""
    grp = df.groupby("date").agg(
        planned_qty_sum=("planned_qty", "sum"),
        actual_qty_sum=("actual_qty", "sum"),
        defect_qty_sum=("defect_qty", "sum"),
        variance_qty_sum=("variance_qty", "sum"),
    ).reset_index()
    grp["daily_achievement_rate"] = grp["actual_qty_sum"] / grp["planned_qty_sum"]
    return grp


def fmt_pct(val: float) -> str:
    return f"{val*100:.1f}%"


def fmt_int(val: float) -> str:
    return f"{int(val):,}"


def build_report(
    df: pd.DataFrame,
    line_df: pd.DataFrame,
    cat_df: pd.DataFrame,
    under_df: pd.DataFrame,
    daily_df: pd.DataFrame,
) -> str:
    total_planned = int(df["planned_qty"].sum())
    total_actual = int(df["actual_qty"].sum())
    total_defect = int(df["defect_qty"].sum())
    avg_achievement = df["achievement_rate"].mean()
    avg_defect = df["defect_rate"].mean()
    achievement_count = (df["achievement_flag"] == "達成").sum()
    unachievement_count = (df["achievement_flag"] == "未達").sum()
    total_rows = len(df)

    lines = []
    lines.append("# 生産計画 vs 実績 差異分析レポート（2024年1月）")
    lines.append("")
    lines.append("## 1. 全体サマリー")
    lines.append("")
    lines.append(f"- 対象期間: 2024-01-01 〜 2024-01-31")
    lines.append(f"- 総レコード数: {fmt_int(total_rows)} 件")
    lines.append(f"- 総計画数量: {fmt_int(total_planned)}")
    lines.append(f"- 総実績数量: {fmt_int(total_actual)}")
    lines.append(f"- 総不良数: {fmt_int(total_defect)}")
    lines.append(f"- 平均達成率: {fmt_pct(avg_achievement)}")
    lines.append(f"- 平均不良率: {fmt_pct(avg_defect)}")
    lines.append(f"- 計画達成レコード数: {fmt_int(achievement_count)} 件 / {fmt_int(total_rows)} 件 ({fmt_pct(achievement_count/total_rows)})")
    lines.append(f"- 計画未達レコード数: {fmt_int(unachievement_count)} 件")
    lines.append("")

    lines.append("## 2. ライン別分析")
    lines.append("")
    lines.append("| ライン名 | 計画数量合計 | 実績数量合計 | 差異数量 | 達成率 | 不良率 |")
    lines.append("|---------|------------|------------|---------|-------|-------|")
    for _, row in line_df.iterrows():
        lines.append(
            f"| {row['line_name']} | {fmt_int(row['planned_qty_sum'])} | "
            f"{fmt_int(row['actual_qty_sum'])} | {fmt_int(row['variance_qty_sum'])} | "
            f"{fmt_pct(row['overall_achievement_rate'])} | {fmt_pct(row['overall_defect_rate'])} |"
        )
    lines.append("")

    best_line = line_df.iloc[0]
    worst_line = line_df.iloc[-1]
    lines.append(f"**インサイト:** 最高達成ラインは {best_line['line_name']} "
                 f"（達成率 {fmt_pct(best_line['overall_achievement_rate'])}）、"
                 f"最低達成ラインは {worst_line['line_name']} "
                 f"（達成率 {fmt_pct(worst_line['overall_achievement_rate'])}）。"
                 f"両ラインの差は {fmt_pct(best_line['overall_achievement_rate'] - worst_line['overall_achievement_rate'])} ポイント。")
    lines.append("")

    lines.append("## 3. カテゴリ別分析")
    lines.append("")
    lines.append("| 製品カテゴリ | 計画数量合計 | 実績数量合計 | 達成率 | 不良率 |")
    lines.append("|------------|------------|------------|-------|-------|")
    for _, row in cat_df.sort_values("overall_achievement_rate", ascending=False).iterrows():
        lines.append(
            f"| {row['category']} | {fmt_int(row['planned_qty_sum'])} | "
            f"{fmt_int(row['actual_qty_sum'])} | "
            f"{fmt_pct(row['overall_achievement_rate'])} | {fmt_pct(row['overall_defect_rate'])} |"
        )
    lines.append("")

    max_defect_cat = cat_df.loc[cat_df["overall_defect_rate"].idxmax()]
    min_defect_cat = cat_df.loc[cat_df["overall_defect_rate"].idxmin()]
    lines.append(f"**不良率分析:** 不良率が最も高いカテゴリは「{max_defect_cat['category']}」"
                 f"（{fmt_pct(max_defect_cat['overall_defect_rate'])}）。"
                 f"最も低いのは「{min_defect_cat['category']}」（{fmt_pct(min_defect_cat['overall_defect_rate'])}）。"
                 f"品質改善の優先対象として「{max_defect_cat['category']}」の工程見直しを推奨する。")
    lines.append("")

    lines.append("## 4. 未達ラインランキング")
    lines.append("")
    if len(under_df) > 0:
        lines.append("| ライン名 | 未達件数 | 平均達成率 |")
        lines.append("|---------|---------|----------|")
        for _, row in under_df.iterrows():
            lines.append(
                f"| {row['line_name']} | {int(row['under_count'])} | "
                f"{fmt_pct(row['avg_achievement_rate'])} |"
            )
    else:
        lines.append("全ラインが計画達成しています。")
    lines.append("")

    lines.append("## 5. 日別生産トレンド（抜粋）")
    lines.append("")
    lines.append("| 日付 | 計画数量 | 実績数量 | 差異 | 日次達成率 |")
    lines.append("|-----|---------|---------|-----|----------|")
    for _, row in daily_df.iterrows():
        lines.append(
            f"| {row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else row['date']} | "
            f"{fmt_int(row['planned_qty_sum'])} | {fmt_int(row['actual_qty_sum'])} | "
            f"{fmt_int(row['variance_qty_sum'])} | {fmt_pct(row['daily_achievement_rate'])} |"
        )
    lines.append("")

    lines.append("## 6. インサイト・改善示唆")
    lines.append("")
    lines.append("### 主要インサイト")
    lines.append("")
    lines.append(f"1. **全体達成率**: 平均 {fmt_pct(avg_achievement)} で、計画に対して"
                 + ("概ね達成できている。" if avg_achievement >= 1.0 else "未達傾向が見られる。"))
    lines.append(f"2. **不良品管理**: 平均不良率 {fmt_pct(avg_defect)}。"
                 f"総不良数 {fmt_int(total_defect)} 個の削減が収益改善に直結する。")
    lines.append(f"3. **ライン間格差**: 達成率の最大格差が "
                 f"{fmt_pct(line_df['overall_achievement_rate'].max() - line_df['overall_achievement_rate'].min())} あり、"
                 f"ベストプラクティスの横展開で底上げが可能。")
    lines.append("")
    lines.append("### 改善示唆")
    lines.append("")
    lines.append(f"- **{worst_line['line_name']} の重点改善**: 稼働率・段取り時間・作業者スキルを点検する。")
    lines.append(f"- **{max_defect_cat['category']} の品質対策**: 工程内検査頻度を増やし、不良流出を防ぐ。")
    lines.append("- **計画精度向上**: 計画未達の多い時間帯・曜日パターンを特定し、需要予測を精緻化する。")
    lines.append("- **生産トレンド監視**: 月次ではなく週次での差異モニタリングを導入し、早期対処を可能にする。")
    lines.append("")
    lines.append("## 7. まとめ")
    lines.append("")
    lines.append(f"2024年1月の生産実績は計画数量 {fmt_int(total_planned)} に対し実績 {fmt_int(total_actual)}（達成率 {fmt_pct(total_actual/total_planned)}）。"
                 f"ライン別・カテゴリ別の分析により、改善対象を特定した。"
                 f"継続的なモニタリングと改善サイクルの確立が重要課題である。")
    lines.append("")

    return "\n".join(lines)


def analyze():
    df = load_data()
    print(f"[OK] データ読み込み完了: {len(df)} 行")

    line_df = analyze_by_line(df)
    cat_df = analyze_by_category(df)
    under_df = underperforming_lines(df)
    daily_df = daily_trend(df)

    # ライン別サマリーCSV出力
    line_df.to_csv(LINE_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    print(f"[OK] ライン別サマリー出力: {LINE_SUMMARY_CSV}")

    # レポートMarkdown出力
    report_text = build_report(df, line_df, cat_df, under_df, daily_df)
    REPORT_MD.write_text(report_text, encoding="utf-8")
    print(f"[OK] 分析レポート出力: {REPORT_MD}")


if __name__ == "__main__":
    analyze()
