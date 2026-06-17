# analyze.py — 分析モジュール（C-36 顧客満足度）
# encoding: utf-8

import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CLEANED_FILE = OUTPUT_DIR / "cleaned_satisfaction_202401.csv"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
SERVICE_SUMMARY_FILE = OUTPUT_DIR / "service_summary_202401.csv"


def compute_nps(df: pd.DataFrame) -> float:
    """NPS = 推奨者% - 批判者%"""
    total = len(df)
    if total == 0:
        return 0.0
    promoters = (df["nps_category"] == "推奨者").sum()
    detractors = (df["nps_category"] == "批判者").sum()
    return round((promoters / total - detractors / total) * 100, 1)


def service_summary(df: pd.DataFrame) -> pd.DataFrame:
    """サービス区分別のCSATおよびNPS集計。"""
    grouped = df.groupby("service_type")

    csat_mean = grouped["csat_score"].mean().rename("avg_csat")
    nps_score = grouped.apply(compute_nps, include_groups=False).rename("nps_score")
    count = grouped.size().rename("response_count")

    summary = pd.concat([count, csat_mean.round(2), nps_score], axis=1).reset_index()
    summary.columns = ["service_type", "response_count", "avg_csat", "nps_score"]
    return summary.sort_values("avg_csat", ascending=False).reset_index(drop=True)


def agent_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """担当者別平均満足度ランキング。"""
    ranked = (
        df.groupby("agent")["csat_score"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "avg_csat", "count": "response_count"})
        .round({"avg_csat": 2})
        .sort_values("avg_csat", ascending=False)
        .reset_index()
    )
    return ranked


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """月別CSAT推移。"""
    df = df.copy()
    df["month"] = pd.to_datetime(df["response_date"], errors="coerce").dt.to_period("M")
    trend = (
        df.groupby("month")["csat_score"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "avg_csat", "count": "response_count"})
        .round({"avg_csat": 2})
        .reset_index()
    )
    trend["month"] = trend["month"].astype(str)
    return trend


def run() -> dict:
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

    total_responses = len(df)
    avg_csat = round(df["csat_score"].mean(), 2)
    overall_nps = compute_nps(df)
    satisfaction_rate = round((df["satisfaction_flag"] == "満足").mean() * 100, 1)
    dissatisfaction_rate = round((df["satisfaction_flag"] == "不満").mean() * 100, 1)

    svc_summary = service_summary(df)
    agent_rank = agent_ranking(df)
    mon_trend = monthly_trend(df)

    promoter_count = (df["nps_category"] == "推奨者").sum()
    neutral_count = (df["nps_category"] == "中立者").sum()
    detractor_count = (df["nps_category"] == "批判者").sum()

    best_service = svc_summary.iloc[0]["service_type"]
    worst_service = svc_summary.iloc[-1]["service_type"]
    top_agent = agent_rank.iloc[0]["agent"]
    low_agent = agent_rank.iloc[-1]["agent"]

    # ── レポート生成 ─────────────────────────────────────────────────────────
    lines = [
        "# 顧客満足度スコア集計・トレンド分析レポート",
        "",
        "## 1. エグゼクティブサマリー",
        "",
        f"- 総回答数: {total_responses} 件",
        f"- 平均CSAT: {avg_csat} / 5.0",
        f"- NPS: {overall_nps}",
        f"- 満足率: {satisfaction_rate}%",
        f"- 不満率: {dissatisfaction_rate}%",
        "",
        "## 2. NPS 内訳",
        "",
        f"| 区分 | 件数 | 比率 |",
        "|------|------|------|",
        f"| 推奨者 | {promoter_count} | {round(promoter_count/total_responses*100,1)}% |",
        f"| 中立者 | {neutral_count} | {round(neutral_count/total_responses*100,1)}% |",
        f"| 批判者 | {detractor_count} | {round(detractor_count/total_responses*100,1)}% |",
        "",
        "## 3. サービス区分別 CSAT・NPS",
        "",
        "| サービス区分 | 回答数 | 平均CSAT | NPS |",
        "|--------------|--------|----------|-----|",
    ]
    for _, row in svc_summary.iterrows():
        lines.append(
            f"| {row['service_type']} | {int(row['response_count'])} "
            f"| {row['avg_csat']:.2f} | {row['nps_score']} |"
        )

    lines += [
        "",
        "## 4. 担当者別満足度ランキング",
        "",
        "| 順位 | 担当者 | 平均CSAT | 回答数 |",
        "|------|--------|----------|--------|",
    ]
    for rank, (_, row) in enumerate(agent_rank.iterrows(), 1):
        lines.append(
            f"| {rank} | {row['agent']} | {row['avg_csat']:.2f} | {int(row['response_count'])} |"
        )

    lines += [
        "",
        "## 5. 月別CSATトレンド",
        "",
        "| 月 | 平均CSAT | 回答数 |",
        "|----|----------|--------|",
    ]
    for _, row in mon_trend.iterrows():
        lines.append(f"| {row['month']} | {row['avg_csat']:.2f} | {int(row['response_count'])} |")

    lines += [
        "",
        "## 6. インサイトと改善示唆",
        "",
        f"- 最高評価サービスは **{best_service}** です。このサービスの成功要因を他サービスに横展開することを推奨します。",
        f"- 最低評価サービスは **{worst_service}** です。顧客フィードバックの詳細分析と対応プロセスの見直しが必要です。",
        f"- 担当者別では **{top_agent}** が最高スコアを記録しています。ベストプラクティスの共有・ナレッジ化を検討してください。",
        f"- **{low_agent}** は最低スコアです。個別コーチングや研修プログラムの提供が効果的です。",
        f"- NPS が {overall_nps} であり、",
        "  批判者比率の削減が最優先課題です。不満顧客への迅速なフォローアップ施策を導入してください。",
        f"- 不満率 {dissatisfaction_rate}% の顧客に対して個別ヒアリングを実施し、離反防止策を講じることを推奨します。",
        "",
        "---",
        "*本レポートは analyze.py により自動生成されました。*",
    ]

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Analysis report saved: {REPORT_FILE}")

    # ── サービス別サマリー CSV ────────────────────────────────────────────
    svc_summary.to_csv(SERVICE_SUMMARY_FILE, index=False, encoding="utf-8-sig")
    print(f"Service summary saved: {SERVICE_SUMMARY_FILE}")

    return {
        "total_responses": total_responses,
        "avg_csat": avg_csat,
        "nps": overall_nps,
        "satisfaction_rate": satisfaction_rate,
        "service_summary": svc_summary,
        "agent_ranking": agent_rank,
        "monthly_trend": mon_trend,
    }


if __name__ == "__main__":
    run()
