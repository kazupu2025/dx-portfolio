# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_orders_202401.csv")
os.makedirs(CHARTS_DIR, exist_ok=True)


def main():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # --- 1. 店舗別売上合計（縦棒） ---
    shop_rev = df.groupby("shop_name")["total_cost"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(shop_rev.index, shop_rev.values, color=["#2196F3", "#FF9800", "#4CAF50"])
    ax.set_title("店舗別売上合計", fontsize=14)
    ax.set_xlabel("店舗名")
    ax.set_ylabel("売上合計（円）")
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50000,
                f"{int(bar.get_height()):,}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "bar_shop_revenue.png")
    fig.savefig(out_path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved {out_path}")

    # --- 2. 作業区分別平均遅延日数（横棒） ---
    wtype_delay = df.groupby("work_type")["delay_days"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#4CAF50" if v <= 0 else "#F44336" for v in wtype_delay.values]
    ax.barh(wtype_delay.index, wtype_delay.values, color=colors)
    ax.set_title("作業区分別平均遅延日数", fontsize=14)
    ax.set_xlabel("平均遅延日数（日）")
    ax.set_ylabel("作業区分")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "bar_worktype_delay.png")
    fig.savefig(out_path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved {out_path}")

    # --- 3. 技術者別遅延率上位10名（横棒） ---
    tech_delay = (
        df.groupby("tech_id")["is_delayed"].mean()
        .sort_values(ascending=False)
        .head(10)
    )
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(tech_delay.index[::-1], tech_delay.values[::-1], color="#FF5722")
    ax.set_title("技術者別遅延率 上位10名", fontsize=14)
    ax.set_xlabel("遅延率")
    ax.set_ylabel("技術者ID")
    ax.set_xlim(0, 1)
    for i, (idx, val) in enumerate(zip(tech_delay.index[::-1], tech_delay.values[::-1])):
        ax.text(val + 0.01, i, f"{val:.1%}", va="center", fontsize=9)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "bar_tech_efficiency.png")
    fig.savefig(out_path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved {out_path}")

    print("[OK] All charts saved to output/charts/")


if __name__ == "__main__":
    main()
