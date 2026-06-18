# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
分析スクリプト: 学科別・選考方法別・地域別の申込分析
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_applications_202401.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_analysis():
    if not os.path.exists(CLEANED_FILE):
        print(f"[FAIL] クレンジング済みファイルが見つかりません: {CLEANED_FILE}")
        return

    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    print(f"[OK] データ読み込み: {len(df)} 行")

    # --- 学科別分析 ---
    dept_group = df.groupby("department").agg(
        申込数=("app_id", "count"),
        合格数=("is_enrolled", "sum"),
        平均点=("score", "mean"),
    ).reset_index()
    dept_group["合格率(%)"] = (dept_group["合格数"] / dept_group["申込数"] * 100).round(1)
    dept_group["平均点"] = dept_group["平均点"].round(1)
    dept_group = dept_group.rename(columns={"department": "学科"})

    # --- 選考方法別分析 ---
    sel_group = df.groupby("selection_method").agg(
        申込数=("app_id", "count"),
        合格数=("is_enrolled", "sum"),
    ).reset_index()
    sel_group["合格率(%)"] = (sel_group["合格数"] / sel_group["申込数"] * 100).round(1)
    sel_group = sel_group.rename(columns={"selection_method": "選考方法"})

    # --- 地域別分析 ---
    region_group = df.groupby("region").agg(
        申込数=("app_id", "count"),
        合格数=("is_enrolled", "sum"),
    ).reset_index()
    region_group["合格率(%)"] = (region_group["合格数"] / region_group["申込数"] * 100).round(1)
    region_group = region_group.rename(columns={"region": "地域"})

    # --- KPI ---
    total = len(df)
    pass_count = int(df["is_enrolled"].sum())
    pass_rate = round(pass_count / total * 100, 1)
    avg_score = round(df["score"].mean(), 1)
    interview_rate = round((df["interview_flag"] == 1).sum() / total * 100, 1)

    # --- Markdown レポート ---
    report_lines = [
        "# 生徒入学申込・入学率分析レポート",
        "",
        "## 分析期間",
        "2024年1月（2024-01-01 〜 2024-01-20）",
        "",
        "## KPIサマリー",
        "",
        f"- 総申込数: {total} 件",
        f"- 合格数: {pass_count} 件",
        f"- 合格率: {pass_rate} %",
        f"- 平均点: {avg_score} 点",
        f"- 面接実施率: {interview_rate} %",
        "",
        "## 学科別申込数・合格率・平均点",
        "",
        dept_group.to_markdown(index=False),
        "",
        "## 選考方法別合格率",
        "",
        sel_group.to_markdown(index=False),
        "",
        "## 地域別申込数",
        "",
        region_group.to_markdown(index=False),
        "",
    ]

    report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"[OK] レポート出力: {report_path}")

    # --- dept_summary CSV ---
    dept_summary_path = os.path.join(OUTPUT_DIR, "dept_summary_202401.csv")
    dept_group.to_csv(dept_summary_path, index=False, encoding="utf-8-sig")
    print(f"[OK] 学科別サマリーCSV: {dept_summary_path}")


if __name__ == "__main__":
    run_analysis()
