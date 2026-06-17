"""
C-41: 分析スクリプト
output/cleaned_recruitment_202401.csv を読み込み、
採用チャネル別コスト・採用レポートを出力
print文に記号(YEN記号等)は使用しない。
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_recruitment_202401.csv"

PHASES = ["書類選考", "一次面接", "二次面接", "最終面接", "内定"]
PHASE_ORDER = {p: i + 1 for i, p in enumerate(PHASES)}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def channel_cost_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """チャネル別採用コスト・採用率・採用単価"""
    summary = (
        df.groupby("channel")
        .agg(
            total_applicants=("apply_no", "count"),
            hired_count=("is_hired", "sum"),
            avg_cost=("cost", "mean"),
            total_cost=("cost", "sum"),
            min_cost=("cost", "min"),
            max_cost=("cost", "max"),
        )
        .reset_index()
    )
    summary["hire_rate"] = (summary["hired_count"] / summary["total_applicants"]).round(4)
    summary["cost_per_hire"] = (
        summary.apply(
            lambda r: r["total_cost"] / r["hired_count"] if r["hired_count"] > 0 else None,
            axis=1,
        )
    ).round(0)
    summary["avg_cost"] = summary["avg_cost"].round(0)
    summary["total_cost"] = summary["total_cost"].round(0)
    return summary.sort_values("avg_cost", ascending=True).reset_index(drop=True)


def jobtype_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """職種別採用傾向"""
    summary = (
        df.groupby("job_type")
        .agg(
            total_applicants=("apply_no", "count"),
            hired_count=("is_hired", "sum"),
            avg_cost=("cost", "mean"),
        )
        .reset_index()
    )
    summary["hire_rate"] = (summary["hired_count"] / summary["total_applicants"]).round(4)
    summary["avg_cost"] = summary["avg_cost"].round(0)
    return summary.sort_values("total_applicants", ascending=False).reset_index(drop=True)


def offer_acceptance_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """内定承諾率分析"""
    if "offer_acceptance" not in df.columns:
        return pd.DataFrame()
    counts = df["offer_acceptance"].value_counts().reset_index()
    counts.columns = ["offer_acceptance", "count"]
    total = len(df)
    counts["rate"] = (counts["count"] / total).round(4)
    return counts


def phase_funnel_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """採用フェーズ別漏れ率"""
    total = len(df)
    rows = []
    for phase in PHASES:
        count = (df["phase"] == phase).sum()
        rate = count / total if total > 0 else 0.0
        rows.append({
            "phase": phase,
            "applicant_count": count,
            "rate": round(rate, 4),
        })
    funnel_df = pd.DataFrame(rows)
    # 前フェーズからの漏れ率
    funnel_df["dropout_rate"] = None
    for i in range(1, len(funnel_df)):
        prev = funnel_df.loc[i - 1, "applicant_count"]
        curr = funnel_df.loc[i, "applicant_count"]
        if prev > 0:
            funnel_df.at[i, "dropout_rate"] = round(1 - curr / prev, 4)
        else:
            funnel_df.at[i, "dropout_rate"] = None
    return funnel_df


def build_report(
    df: pd.DataFrame,
    channel_df: pd.DataFrame,
    jobtype_df: pd.DataFrame,
    oa_df: pd.DataFrame,
    funnel_df: pd.DataFrame,
) -> str:
    total = len(df)
    hired = int(df["is_hired"].sum())
    hire_rate = hired / total * 100 if total > 0 else 0
    avg_cost = df["cost"].mean()
    total_cost = df["cost"].sum()

    # 内定承諾率
    if not oa_df.empty and "承諾" in oa_df["offer_acceptance"].values:
        accepted_count = int(oa_df.loc[oa_df["offer_acceptance"] == "承諾", "count"].iloc[0])
        accept_rate = accepted_count / hired * 100 if hired > 0 else 0
    else:
        accepted_count = 0
        accept_rate = 0

    # 最低コストチャネル
    lowest_cost_ch = channel_df.iloc[0]["channel"] if not channel_df.empty else "N/A"
    lowest_cost_val = channel_df.iloc[0]["avg_cost"] if not channel_df.empty else 0

    # 最高採用率チャネル
    top_hire_rate_ch = channel_df.sort_values("hire_rate", ascending=False).iloc[0]["channel"] if not channel_df.empty else "N/A"
    top_hire_rate_val = channel_df.sort_values("hire_rate", ascending=False).iloc[0]["hire_rate"] * 100 if not channel_df.empty else 0

    lines = [
        "# 採用チャネル別コスト・採用分析レポート（2024年1月-3月）",
        "",
        "## 1. 概要",
        "",
        f"- 分析対象応募者数: {total:,} 名",
        f"- 採用人数: {hired:,} 名",
        f"- 総採用率: {hire_rate:.1f}%",
        f"- 平均採用コスト: {avg_cost:,.0f} 円",
        f"- 採用コスト総額: {total_cost:,.0f} 円",
        f"- 内定承諾数: {accepted_count:,} 名（承諾率: {accept_rate:.1f}%）",
        f"- 分析チャネル数: {df['channel'].nunique()} チャネル",
        f"- 分析職種数: {df['job_type'].nunique()} 職種",
        "",
        "## 2. チャネル別採用コスト・採用率・採用単価",
        "",
        "| チャネル | 応募数 | 採用数 | 採用率 | 平均コスト(円) | 採用単価(円) |",
        "|---------|-------|-------|-------|------------|-----------|",
    ]

    for _, row in channel_df.iterrows():
        cost_per_hire_str = (
            f"{row['cost_per_hire']:,.0f}"
            if pd.notna(row["cost_per_hire"]) and row["cost_per_hire"] is not None
            else "N/A"
        )
        lines.append(
            f"| {row['channel']} | {int(row['total_applicants']):,} 名 "
            f"| {int(row['hired_count'])} 名 "
            f"| {row['hire_rate'] * 100:.1f}% "
            f"| {row['avg_cost']:,.0f} "
            f"| {cost_per_hire_str} |"
        )

    lines += [
        "",
        "## 3. 職種別採用傾向",
        "",
        "| 職種 | 応募数 | 採用数 | 採用率 | 平均コスト(円) |",
        "|-----|-------|-------|-------|------------|",
    ]
    for _, row in jobtype_df.iterrows():
        lines.append(
            f"| {row['job_type']} | {int(row['total_applicants']):,} 名 "
            f"| {int(row['hired_count'])} 名 "
            f"| {row['hire_rate'] * 100:.1f}% "
            f"| {row['avg_cost']:,.0f} |"
        )

    lines += [
        "",
        "## 4. 内定承諾率分析",
        "",
        "| 区分 | 件数 | 割合 |",
        "|-----|-----|-----|",
    ]
    for _, row in oa_df.iterrows():
        lines.append(
            f"| {row['offer_acceptance']} | {int(row['count']):,} 件 "
            f"| {row['rate'] * 100:.1f}% |"
        )

    lines += [
        "",
        "## 5. 採用フェーズ別漏れ率（ファネル分析）",
        "",
        "| フェーズ | 応募者数 | 全体比 | 前フェーズからの漏れ率 |",
        "|---------|---------|-------|------------------|",
    ]
    for _, row in funnel_df.iterrows():
        dropout_str = (
            f"{float(row['dropout_rate']) * 100:.1f}%"
            if pd.notna(row["dropout_rate"]) and row["dropout_rate"] is not None
            else "-"
        )
        lines.append(
            f"| {row['phase']} | {int(row['applicant_count']):,} 名 "
            f"| {row['rate'] * 100:.1f}% "
            f"| {dropout_str} |"
        )

    lines += [
        "",
        "## 6. インサイト・改善示唆",
        "",
        "### チャネル別コスト効率",
        "",
        f"平均採用コストが最も低いチャネルは「{lowest_cost_ch}」({lowest_cost_val:,.0f} 円)です。",
        f"採用率が最も高いチャネルは「{top_hire_rate_ch}」({top_hire_rate_val:.1f}%)です。",
        "コスト効率と採用率の両方が優れたチャネルへの集中投資を検討してください。",
        "",
        "### 採用コスト最適化の提案",
        "",
        "1. リファラル採用・SNS採用は低コストかつ高効率な場合が多く、積極活用を推奨します。",
        "2. エージェント採用は高コストですが、特定の専門職種では有効な場合があります。",
        "   採用単価ベースの費用対効果を定期的に評価してください。",
        "3. 合同説明会は母集団形成には有効ですが、採用率の継続的モニタリングが重要です。",
        "",
        "### 内定承諾率の改善",
        "",
        f"内定承諾率は {accept_rate:.1f}% です。",
        "承諾率向上のために、オファー面談の実施や条件提示タイミングの最適化を検討してください。",
        "",
        "## 7. まとめ",
        "",
        f"1. 総採用率は {hire_rate:.1f}% で、{total:,} 名の応募に対して {hired:,} 名を採用しました。",
        f"2. 採用コスト最小チャネルは「{lowest_cost_ch}」、採用率最高チャネルは「{top_hire_rate_ch}」です。",
        f"3. 平均採用コストは {avg_cost:,.0f} 円です。チャネル間のコスト格差を把握し、予算配分を最適化してください。",
        f"4. 内定承諾率 {accept_rate:.1f}% の改善により、採用効率のさらなる向上が期待できます。",
        "",
    ]

    return "\n".join(lines)


def main():
    df = load_data()

    channel_df = channel_cost_analysis(df)
    jobtype_df = jobtype_analysis(df)
    oa_df = offer_acceptance_analysis(df)
    funnel_df = phase_funnel_analysis(df)

    report = build_report(df, channel_df, jobtype_df, oa_df, funnel_df)
    report_path = OUTPUT_DIR / "analysis_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"レポート出力: {report_path}")

    summary_path = OUTPUT_DIR / "channel_summary_202401.csv"
    channel_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"チャネルサマリーCSV出力: {summary_path}")
    print(f"  -> {len(channel_df)} 行")


if __name__ == "__main__":
    main()
