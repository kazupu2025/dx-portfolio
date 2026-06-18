# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
分析スクリプト
出力: output/analysis_report.md, output/category_summary_202401.csv
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CLEANED_PATH = os.path.join(BASE_DIR, "output", "cleaned_tickets_202401.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(CLEANED_PATH, encoding="utf-8-sig")
    df["resolution_hours"] = pd.to_numeric(df["resolution_hours"], errors="coerce")
    df["is_resolved"] = pd.to_numeric(df["is_resolved"], errors="coerce")
    df["is_escalated"] = pd.to_numeric(df["is_escalated"], errors="coerce")
    df["satisfaction"] = pd.to_numeric(df["satisfaction"], errors="coerce")
    return df


def analyze_category(df):
    """カテゴリ別: 件数・解決率・平均解決時間・満足度"""
    g = df.groupby("category", sort=False)
    summary = pd.DataFrame({
        "件数": g["ticket_id"].count(),
        "解決率": g["is_resolved"].mean().round(4),
        "平均解決時間(h)": g["resolution_hours"].mean().round(2),
        "平均満足度": g["satisfaction"].mean().round(2),
    }).reset_index()
    summary.columns = ["category", "count", "resolve_rate", "avg_resolution_hours", "avg_satisfaction"]
    return summary


def analyze_priority(df):
    """優先度別: 件数・エスカレーション率"""
    g = df.groupby("priority", sort=False)
    summary = pd.DataFrame({
        "件数": g["ticket_id"].count(),
        "エスカレーション率": g["is_escalated"].mean().round(4),
    }).reset_index()
    summary.columns = ["priority", "count", "escalation_rate"]
    return summary


def analyze_agent(df):
    """担当者別: 担当件数・解決率"""
    g = df.groupby("agent_id", sort=False)
    summary = pd.DataFrame({
        "担当件数": g["ticket_id"].count(),
        "解決率": g["is_resolved"].mean().round(4),
    }).reset_index()
    summary.columns = ["agent_id", "count", "resolve_rate"]
    return summary.sort_values("agent_id")


def build_report(df, cat_df, prio_df, agent_df):
    total = len(df)
    resolved = int(df["is_resolved"].sum())
    resolve_rate = resolved / total if total > 0 else 0
    avg_rh = df["resolution_hours"].mean()
    avg_sat = df["satisfaction"].mean()
    esc_count = int(df["is_escalated"].sum())
    esc_rate = esc_count / total if total > 0 else 0

    lines = []
    lines.append("# CSチケット分析レポート (2024年1月)")
    lines.append("")
    lines.append("## 1. 全体サマリー")
    lines.append("")
    lines.append(f"- 総チケット数: {total}件")
    lines.append(f"- 解決済み件数: {resolved}件 (解決率: {resolve_rate:.1%})")
    lines.append(f"- 平均解決時間: {avg_rh:.1f}時間")
    lines.append(f"- 平均満足度: {avg_sat:.2f}点 (5点満点)")
    lines.append(f"- エスカレーション件数: {esc_count}件 (エスカレーション率: {esc_rate:.1%})")
    lines.append("")

    lines.append("## 2. カテゴリ別分析")
    lines.append("")
    lines.append("| カテゴリ | 件数 | 解決率 | 平均解決時間(h) | 平均満足度 |")
    lines.append("|----------|------|--------|----------------|-----------|")
    for _, row in cat_df.iterrows():
        lines.append(
            f"| {row['category']} | {row['count']} | {row['resolve_rate']:.1%} "
            f"| {row['avg_resolution_hours']:.1f} | {row['avg_satisfaction']:.2f} |"
        )
    lines.append("")

    lines.append("## 3. 優先度別分析")
    lines.append("")
    lines.append("| 優先度 | 件数 | エスカレーション率 |")
    lines.append("|--------|------|------------------|")
    for _, row in prio_df.iterrows():
        lines.append(
            f"| {row['priority']} | {row['count']} | {row['escalation_rate']:.1%} |"
        )
    lines.append("")

    lines.append("## 4. 担当者別分析")
    lines.append("")
    lines.append("| 担当者ID | 担当件数 | 解決率 |")
    lines.append("|----------|---------|--------|")
    for _, row in agent_df.iterrows():
        lines.append(
            f"| {row['agent_id']} | {row['count']} | {row['resolve_rate']:.1%} |"
        )
    lines.append("")

    return "\n".join(lines)


def main():
    if not os.path.exists(CLEANED_PATH):
        print(f"[FAIL] クレンジング済みファイルが見つかりません: {CLEANED_PATH}")
        return

    df = load_data()
    print(f"[OK] データ読み込み: {len(df)}件")

    cat_df = analyze_category(df)
    prio_df = analyze_priority(df)
    agent_df = analyze_agent(df)

    # カテゴリサマリーCSV出力
    cat_out = os.path.join(OUTPUT_DIR, "category_summary_202401.csv")
    cat_df.to_csv(cat_out, index=False, encoding="utf-8-sig")
    print(f"[OK] カテゴリサマリー出力: {cat_out}")

    # 分析レポートMD出力
    report_text = build_report(df, cat_df, prio_df, agent_df)
    report_out = os.path.join(OUTPUT_DIR, "analysis_report.md")
    with open(report_out, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"[OK] 分析レポート出力: {report_out}")


if __name__ == "__main__":
    main()
