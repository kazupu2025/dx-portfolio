"""
C-19: visualize.py
output/charts/ に 3 枚以上のグラフを生成する
- bar_store_revenue_vs_plan.png  店舗別 売上実績vs予算（grouped bar）
- bar_store_profit_flag.png      店舗別 profit_flag分布（積み上げ）
- line_monthly_profit.png        月次 営業利益推移（折れ線）
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_pnl_202401.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")

os.makedirs(CHARTS_DIR, exist_ok=True)


def load_data():
    return pd.read_csv(INPUT_FILE, encoding="utf-8-sig")


def chart1_store_revenue_vs_plan(df):
    """店舗別 売上実績vs予算 grouped bar"""
    grp = df.groupby(["store_id", "store_name"]).agg(
        planned_revenue=("planned_revenue", "sum"),
        actual_revenue=("actual_revenue", "sum"),
    ).reset_index().sort_values("store_id")

    x = range(len(grp))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 6))

    bars1 = ax.bar([i - width / 2 for i in x], grp["planned_revenue"] / 1e6,
                   width, label="売上予算", color="#4C72B0")
    bars2 = ax.bar([i + width / 2 for i in x], grp["actual_revenue"] / 1e6,
                   width, label="売上実績", color="#DD8452")

    ax.set_xticks(list(x))
    ax.set_xticklabels(grp["store_name"].tolist(), fontsize=11)
    ax.set_ylabel("金額（百万円）", fontsize=11)
    ax.set_title("店舗別 売上実績 vs 予算", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}M"))
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    out = os.path.join(CHARTS_DIR, "bar_store_revenue_vs_plan.png")
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"[visualize] Saved: {out}")


def chart2_profit_flag_dist(df):
    """店舗別 profit_flag 分布（積み上げ棒グラフ）"""
    grp = df.groupby(["store_id", "store_name", "profit_flag"]).size().unstack(fill_value=0).reset_index()

    # 全フラグを保証
    for col in ["赤字", "未達", "達成"]:
        if col not in grp.columns:
            grp[col] = 0

    grp = grp.sort_values("store_id")
    labels = grp["store_name"].tolist()
    x = range(len(grp))

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = [0] * len(grp)
    colors = {"達成": "#55A868", "未達": "#F0E442", "赤字": "#C44E52"}

    for flag in ["達成", "未達", "赤字"]:
        vals = grp[flag].tolist()
        ax.bar(list(x), vals, bottom=bottom, label=flag, color=colors[flag])
        bottom = [b + v for b, v in zip(bottom, vals)]

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("週数", fontsize=11)
    ax.set_title("店舗別 利益フラグ分布", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    out = os.path.join(CHARTS_DIR, "bar_store_profit_flag.png")
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"[visualize] Saved: {out}")


def chart3_monthly_profit_trend(df):
    """月次 営業利益推移（折れ線）"""
    grp = df.groupby("year_month").agg(
        planned_operating_profit=("planned_operating_profit", "sum"),
        actual_operating_profit=("actual_operating_profit", "sum"),
    ).reset_index().sort_values("year_month")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(grp["year_month"], grp["planned_operating_profit"] / 1e6,
            marker="o", label="営業利益予算", color="#4C72B0", linewidth=2)
    ax.plot(grp["year_month"], grp["actual_operating_profit"] / 1e6,
            marker="s", label="営業利益実績", color="#DD8452", linewidth=2)

    ax.axhline(0, color="red", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_xlabel("期間", fontsize=11)
    ax.set_ylabel("営業利益（百万円）", fontsize=11)
    ax.set_title("月次 営業利益推移", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.tight_layout()

    out = os.path.join(CHARTS_DIR, "line_monthly_profit.png")
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"[visualize] Saved: {out}")


def main():
    print("[visualize.py] Loading cleaned data...")
    df = load_data()

    chart1_store_revenue_vs_plan(df)
    chart2_profit_flag_dist(df)
    chart3_monthly_profit_trend(df)

    print("[visualize.py] Done. 3 charts generated.")


if __name__ == "__main__":
    main()
