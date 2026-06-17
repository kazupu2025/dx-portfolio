# -*- coding: utf-8 -*-
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_contracts_202401.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.md")
PLAN_SUMMARY_FILE = os.path.join(OUTPUT_DIR, "plan_summary_202401.csv")


def main():
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df["monthly_fee"] = pd.to_numeric(df["monthly_fee"], errors="coerce")
    df["usage_months"] = pd.to_numeric(df["usage_months"], errors="coerce")
    df["login_count"] = pd.to_numeric(df["login_count"], errors="coerce")
    df["ltv"] = pd.to_numeric(df["ltv"], errors="coerce")
    df["is_churned"] = pd.to_numeric(df["is_churned"], errors="coerce")

    # ---- Plan analysis ----
    plan_group = df.groupby("plan").agg(
        total=("contract_id", "count"),
        churned=("is_churned", "sum"),
        avg_ltv=("ltv", "mean"),
        avg_login=("login_count", "mean"),
    ).reset_index()
    plan_group["churn_rate"] = plan_group["churned"] / plan_group["total"]
    plan_group = plan_group.round({"churn_rate": 4, "avg_ltv": 0, "avg_login": 2})

    # ---- Industry analysis ----
    industry_group = df.groupby("industry").agg(
        total=("contract_id", "count"),
        churned=("is_churned", "sum"),
        avg_usage_months=("usage_months", "mean"),
    ).reset_index()
    industry_group["churn_rate"] = industry_group["churned"] / industry_group["total"]
    industry_group = industry_group.round({"churn_rate": 4, "avg_usage_months": 2})

    # ---- Cohort analysis (contract_date month) ----
    df["contract_month"] = pd.to_datetime(df["contract_date"], errors="coerce").dt.to_period("M").astype(str)
    cohort_group = df.groupby("contract_month").agg(
        total=("contract_id", "count"),
        churned=("is_churned", "sum"),
    ).reset_index()
    cohort_group["churn_rate"] = cohort_group["churned"] / cohort_group["total"]
    cohort_group = cohort_group.round({"churn_rate": 4})

    # ---- Overall KPIs ----
    total_contracts = len(df)
    total_churned = int(df["is_churned"].sum())
    overall_churn_rate = total_churned / total_contracts if total_contracts > 0 else 0
    avg_ltv = df["ltv"].mean()
    avg_usage = df["usage_months"].mean()
    high_risk_count = int((df["churn_risk"] == "高リスク").sum())

    # ---- Write plan_summary CSV ----
    plan_group.to_csv(PLAN_SUMMARY_FILE, index=False, encoding="utf-8-sig")
    print(f"[OK] plan_summary written: {PLAN_SUMMARY_FILE}")

    # ---- Write analysis_report.md ----
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# SaaSサブスクリプション チャーン分析レポート\n\n")
        f.write(f"## 全体概要\n\n")
        f.write(f"- 総契約数: {total_contracts:,}\n")
        f.write(f"- 解約数: {total_churned:,}\n")
        f.write(f"- 全体解約率: {overall_churn_rate:.1%}\n")
        f.write(f"- 平均LTV: {avg_ltv:,.0f}円\n")
        f.write(f"- 平均利用月数: {avg_usage:.1f}ヶ月\n")
        f.write(f"- 高リスク顧客数: {high_risk_count:,}\n\n")

        f.write("## プラン別分析\n\n")
        f.write("| プラン | 件数 | 解約率 | 平均LTV | 平均ログイン数 |\n")
        f.write("|--------|------|--------|---------|----------------|\n")
        for _, row in plan_group.iterrows():
            f.write(
                f"| {row['plan']} | {int(row['total']):,} | "
                f"{row['churn_rate']:.1%} | {int(row['avg_ltv']):,}円 | "
                f"{row['avg_login']:.1f} |\n"
            )
        f.write("\n")

        f.write("## 業種別分析\n\n")
        f.write("| 業種 | 件数 | 解約率 | 平均利用月数 |\n")
        f.write("|------|------|--------|-------------|\n")
        for _, row in industry_group.iterrows():
            f.write(
                f"| {row['industry']} | {int(row['total']):,} | "
                f"{row['churn_rate']:.1%} | {row['avg_usage_months']:.1f} |\n"
            )
        f.write("\n")

        f.write("## コホート分析（契約開始月別 解約率）\n\n")
        f.write("| 契約月 | 件数 | 解約率 |\n")
        f.write("|--------|------|--------|\n")
        for _, row in cohort_group.iterrows():
            f.write(
                f"| {row['contract_month']} | {int(row['total']):,} | "
                f"{row['churn_rate']:.1%} |\n"
            )
        f.write("\n")

    print(f"[OK] analysis_report written: {REPORT_FILE}")
    print(f"[OK] Analysis complete. Total={total_contracts}, Churned={total_churned}, Rate={overall_churn_rate:.1%}")


if __name__ == "__main__":
    main()
