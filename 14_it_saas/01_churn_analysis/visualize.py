# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["font.family"] = "MS Gothic"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_contracts_202401.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)


def main():
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df["monthly_fee"] = pd.to_numeric(df["monthly_fee"], errors="coerce")
    df["usage_months"] = pd.to_numeric(df["usage_months"], errors="coerce")
    df["ltv"] = pd.to_numeric(df["ltv"], errors="coerce")
    df["is_churned"] = pd.to_numeric(df["is_churned"], errors="coerce")

    # ---- Chart 1: Plan churn rate bar chart ----
    plan_stats = df.groupby("plan").agg(
        total=("contract_id", "count"),
        churned=("is_churned", "sum"),
    ).reset_index()
    plan_stats["churn_rate"] = plan_stats["churned"] / plan_stats["total"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(plan_stats["plan"], plan_stats["churn_rate"] * 100,
                  color=["#4C72B0", "#DD8452", "#55A868"])
    ax.set_title("プラン別 解約率", fontsize=14)
    ax.set_xlabel("プラン")
    ax.set_ylabel("解約率 (%)")
    ax.set_ylim(0, 50)
    for bar, val in zip(bars, plan_stats["churn_rate"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1%}", ha="center", va="bottom", fontsize=10)
    plt.tight_layout()
    out1 = os.path.join(CHARTS_DIR, "bar_plan_churn_rate.png")
    plt.savefig(out1, dpi=100)
    plt.close()
    print(f"[OK] Chart saved: {out1}")

    # ---- Chart 2: Industry average LTV horizontal bar ----
    industry_stats = df.groupby("industry")["ltv"].mean().reset_index()
    industry_stats.columns = ["industry", "avg_ltv"]
    industry_stats = industry_stats.sort_values("avg_ltv", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(industry_stats["industry"], industry_stats["avg_ltv"],
                   color="#4C72B0")
    ax.set_title("業種別 平均LTV", fontsize=14)
    ax.set_xlabel("平均LTV (円)")
    ax.set_ylabel("業種")
    for bar, val in zip(bars, industry_stats["avg_ltv"]):
        ax.text(val + 500, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", va="center", fontsize=9)
    plt.tight_layout()
    out2 = os.path.join(CHARTS_DIR, "bar_industry_ltv.png")
    plt.savefig(out2, dpi=100)
    plt.close()
    print(f"[OK] Chart saved: {out2}")

    # ---- Chart 3: Churn risk distribution bar chart ----
    risk_order = ["高リスク", "中リスク", "低リスク"]
    risk_counts = df["churn_risk"].value_counts().reindex(risk_order, fill_value=0)
    risk_colors = {"高リスク": "#C44E52", "中リスク": "#DD8452", "低リスク": "#55A868"}
    colors = [risk_colors.get(r, "#4C72B0") for r in risk_order]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(risk_order, risk_counts.values, color=colors)
    ax.set_title("チャーンリスク分布", fontsize=14)
    ax.set_xlabel("リスクレベル")
    ax.set_ylabel("顧客数")
    for bar, val in zip(bars, risk_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                str(int(val)), ha="center", va="bottom", fontsize=10)
    plt.tight_layout()
    out3 = os.path.join(CHARTS_DIR, "bar_churn_risk.png")
    plt.savefig(out3, dpi=100)
    plt.close()
    print(f"[OK] Chart saved: {out3}")

    print("[OK] All charts generated.")


if __name__ == "__main__":
    main()
