"""
C-33: 分析スクリプト
output/cleaned_recruitment_202401.csv を読み込み、採用歩留まり率分析レポートとサマリーCSVを出力
print文に記号(YEN記号等)は使用しない。
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_recruitment_202401.csv"

PHASE_ORDER = {
    "書類選考": 1,
    "一次面接": 2,
    "二次面接": 3,
    "最終面接": 4,
    "内定": 5,
}
PHASES = ["書類選考", "一次面接", "二次面接", "最終面接", "内定"]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def funnel_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """フェーズ別歩留まり率（ファネル分析）"""
    total_applicants = len(df)
    rows = []
    for phase in PHASES:
        # そのフェーズ以上に到達した応募者数
        phase_num = PHASE_ORDER[phase]
        count = (df["phase_order"] >= phase_num).sum()
        rate = count / total_applicants if total_applicants > 0 else 0.0
        rows.append({
            "phase": phase,
            "phase_order": phase_num,
            "reach_count": count,
            "reach_rate": round(rate, 4),
        })

    funnel_df = pd.DataFrame(rows)
    # フェーズ間の通過率（前フェーズからの通過率）
    funnel_df["pass_rate_from_prev"] = None
    for i in range(1, len(funnel_df)):
        prev_count = funnel_df.loc[i - 1, "reach_count"]
        curr_count = funnel_df.loc[i, "reach_count"]
        if prev_count > 0:
            funnel_df.at[i, "pass_rate_from_prev"] = round(curr_count / prev_count, 4)
        else:
            funnel_df.at[i, "pass_rate_from_prev"] = 0.0
    # 最初のフェーズは全体からの通過率
    funnel_df.at[0, "pass_rate_from_prev"] = round(
        funnel_df.loc[0, "reach_count"] / total_applicants, 4
    ) if total_applicants > 0 else 0.0

    return funnel_df


def channel_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """チャネル別採用率・コスト効率（採用数/応募数）"""
    summary = (
        df.groupby("channel")
        .agg(
            total_applicants=("applicant_id", "count"),
            hired_count=("is_hired", "sum"),
            avg_screening_days=("screening_days", "mean"),
        )
        .reset_index()
    )
    summary["hire_rate"] = (summary["hired_count"] / summary["total_applicants"]).round(4)
    summary["avg_screening_days"] = summary["avg_screening_days"].round(1)
    return summary.sort_values("hire_rate", ascending=False).reset_index(drop=True)


def jobtype_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """職種別採用率・選考日数"""
    summary = (
        df.groupby("job_type")
        .agg(
            total_applicants=("applicant_id", "count"),
            hired_count=("is_hired", "sum"),
            avg_screening_days=("screening_days", "mean"),
        )
        .reset_index()
    )
    summary["hire_rate"] = (summary["hired_count"] / summary["total_applicants"]).round(4)
    summary["avg_screening_days"] = summary["avg_screening_days"].round(1)
    return summary.sort_values("total_applicants", ascending=False).reset_index(drop=True)


def channel_volume_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """採用チャネル別応募数ランキング"""
    ranking = (
        df.groupby("channel")
        .agg(applicant_count=("applicant_id", "count"))
        .reset_index()
        .sort_values("applicant_count", ascending=False)
        .reset_index(drop=True)
    )
    ranking["rank"] = range(1, len(ranking) + 1)
    return ranking[["rank", "channel", "applicant_count"]]


def build_report(
    df: pd.DataFrame,
    funnel_df: pd.DataFrame,
    channel_df: pd.DataFrame,
    jobtype_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
) -> str:
    total = len(df)
    hired = df["is_hired"].sum()
    overall_rate = hired / total * 100 if total > 0 else 0
    avg_days = df["screening_days"].mean()
    first_screen_pass = df["passed_first_screen"].sum()
    first_screen_rate = first_screen_pass / total * 100 if total > 0 else 0

    # 最も採用率が高いチャネル
    top_channel = channel_df.iloc[0]["channel"] if not channel_df.empty else "N/A"
    top_channel_rate = channel_df.iloc[0]["hire_rate"] * 100 if not channel_df.empty else 0

    # 最も応募が多いチャネル
    top_volume_channel = ranking_df.iloc[0]["channel"] if not ranking_df.empty else "N/A"
    top_volume_count = int(ranking_df.iloc[0]["applicant_count"]) if not ranking_df.empty else 0

    lines = [
        "# 採用歩留まり率分析レポート（2024年1月-3月）",
        "",
        "## 1. 概要",
        "",
        f"- 分析対象応募者数: {total:,} 名",
        f"- 採用人数: {hired:,} 名",
        f"- 総採用率: {overall_rate:.1f}%",
        f"- 平均選考日数: {avg_days:.1f} 日",
        f"- 書類選考通過者数: {first_screen_pass:,} 名 ({first_screen_rate:.1f}%)",
        f"- 分析チャネル数: {df['channel'].nunique()} チャネル",
        f"- 分析職種数: {df['job_type'].nunique()} 職種",
        "",
        "## 2. ファネル分析（フェーズ別歩留まり率）",
        "",
        "| フェーズ | 到達者数 | 到達率(全体比) | フェーズ間通過率 |",
        "|---------|---------|-------------|--------------|",
    ]

    for _, row in funnel_df.iterrows():
        prev_rate_str = (
            f"{float(row['pass_rate_from_prev']) * 100:.1f}%"
            if row["pass_rate_from_prev"] is not None
            else "-"
        )
        lines.append(
            f"| {row['phase']} | {int(row['reach_count']):,} 名 "
            f"| {float(row['reach_rate']) * 100:.1f}% "
            f"| {prev_rate_str} |"
        )

    lines += [
        "",
        "## 3. チャネル別採用率",
        "",
        "| 採用チャネル | 応募数 | 採用数 | 採用率 | 平均選考日数 |",
        "|------------|-------|-------|-------|------------|",
    ]
    for _, row in channel_df.iterrows():
        lines.append(
            f"| {row['channel']} | {int(row['total_applicants']):,} 名 "
            f"| {int(row['hired_count'])} 名 "
            f"| {row['hire_rate'] * 100:.1f}% "
            f"| {row['avg_screening_days']:.1f} 日 |"
        )

    lines += [
        "",
        "## 4. 職種別採用率・選考日数",
        "",
        "| 職種 | 応募数 | 採用数 | 採用率 | 平均選考日数 |",
        "|-----|-------|-------|-------|------------|",
    ]
    for _, row in jobtype_df.iterrows():
        lines.append(
            f"| {row['job_type']} | {int(row['total_applicants']):,} 名 "
            f"| {int(row['hired_count'])} 名 "
            f"| {row['hire_rate'] * 100:.1f}% "
            f"| {row['avg_screening_days']:.1f} 日 |"
        )

    lines += [
        "",
        "## 5. 採用チャネル別応募数ランキング",
        "",
        "| 順位 | チャネル | 応募数 |",
        "|-----|---------|-------|",
    ]
    for _, row in ranking_df.iterrows():
        lines.append(
            f"| {int(row['rank'])} | {row['channel']} | {int(row['applicant_count']):,} 名 |"
        )

    lines += [
        "",
        "## 6. インサイト・改善示唆",
        "",
        "### 歩留まり率の傾向",
        "",
        f"書類選考から内定承諾まで一貫した歩留まり分析を実施した結果、"
        f"全体の採用率は {overall_rate:.1f}% でした。",
        f"書類選考通過率は {first_screen_rate:.1f}% であり、"
        "最初のスクリーニングが採用効率に大きな影響を与えています。",
        "",
        "### チャネル別採用効率",
        "",
        f"採用率が最も高いチャネルは「{top_channel}」({top_channel_rate:.1f}%)です。",
        f"応募数が最多のチャネルは「{top_volume_channel}」({top_volume_count:,} 名)ですが、"
        "採用率との乖離を確認し、質の高い応募者確保を意識したチャネル戦略が重要です。",
        "",
        "### 選考プロセスの改善提案",
        "",
        f"平均選考日数 {avg_days:.1f} 日は応募者の機会損失を防ぐ観点から重要です。",
        "選考日数が長い職種・チャネルを特定し、面接プロセスのスリム化や"
        "意思決定サイクルの短縮を検討してください。",
        "",
        "## 7. まとめ",
        "",
        f"1. 総採用率は {overall_rate:.1f}% で、{total:,} 名の応募に対して {hired:,} 名を採用しました。",
        f"2. 採用効率が最も高いチャネルは「{top_channel}」です。このチャネルへの投資を優先することを推奨します。",
        f"3. 平均選考日数は {avg_days:.1f} 日です。ボトルネックとなっているフェーズを特定し、選考スピードの向上を図ってください。",
        "4. 書類選考の精度向上により、その後のフェーズのリソース効率を高めることができます。",
        "",
    ]

    return "\n".join(lines)


def main():
    df = load_data()

    funnel_df = funnel_analysis(df)
    channel_df = channel_analysis(df)
    jobtype_df = jobtype_analysis(df)
    ranking_df = channel_volume_ranking(df)

    # レポート出力
    report = build_report(df, funnel_df, channel_df, jobtype_df, ranking_df)
    report_path = OUTPUT_DIR / "analysis_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"レポート出力: {report_path}")

    # チャネル別サマリーCSV出力
    summary_path = OUTPUT_DIR / "channel_summary_202401.csv"
    channel_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"チャネルサマリーCSV出力: {summary_path}")
    print(f"  -> {len(channel_df)} 行")


if __name__ == "__main__":
    main()
