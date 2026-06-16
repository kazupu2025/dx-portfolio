# -*- coding: utf-8 -*-
"""
visualize.py
RFM分析結果を3枚のグラフとして output/charts/ に保存する。
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

RFM_CSV = OUTPUT_DIR / "customer_rfm_202401.csv"
CLEANED_CSV = OUTPUT_DIR / "cleaned_purchases_202401.csv"

SEGMENT_ORDER = ["優良顧客", "成長顧客", "離反リスク", "休眠顧客"]
SEGMENT_COLORS = {
    "優良顧客": "#2196F3",
    "成長顧客": "#4CAF50",
    "離反リスク": "#FF9800",
    "休眠顧客": "#9E9E9E",
}


def plot_segment_count(rfm: pd.DataFrame):
    """1. セグメント別顧客数の棒グラフ"""
    seg_counts = rfm["segment"].value_counts().reindex(SEGMENT_ORDER, fill_value=0)
    colors = [SEGMENT_COLORS[s] for s in seg_counts.index]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(seg_counts.index, seg_counts.values, color=colors, edgecolor="white", linewidth=0.8)

    for bar, val in zip(bars, seg_counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            str(val),
            ha="center",
            va="bottom",
            fontsize=11,
        )

    ax.set_title("セグメント別顧客数", fontsize=14, pad=12)
    ax.set_xlabel("セグメント", fontsize=11)
    ax.set_ylabel("顧客数（名）", fontsize=11)
    ax.set_ylim(0, seg_counts.max() * 1.2 + 1)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    out = CHARTS_DIR / "bar_segment_count.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] グラフ保存: {out}")


def plot_scatter_rfm(rfm: pd.DataFrame):
    """2. Frequency vs Monetary の散布図（セグメント別に色分け）"""
    fig, ax = plt.subplots(figsize=(8, 6))

    for seg in SEGMENT_ORDER:
        subset = rfm[rfm["segment"] == seg]
        if subset.empty:
            continue
        ax.scatter(
            subset["frequency"],
            subset["monetary"],
            label=seg,
            color=SEGMENT_COLORS[seg],
            alpha=0.7,
            s=60,
            edgecolors="white",
            linewidths=0.5,
        )

    ax.set_title("Frequency vs Monetary（セグメント別）", fontsize=14, pad=12)
    ax.set_xlabel("購買回数（Frequency）", fontsize=11)
    ax.set_ylabel("累計購買金額（Monetary）", fontsize=11)
    ax.legend(title="セグメント", fontsize=9)
    ax.grid(alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    out = CHARTS_DIR / "scatter_rfm_frequency_monetary.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] グラフ保存: {out}")


def plot_category_amount(df_cleaned: pd.DataFrame):
    """3. カテゴリ別累計売上の棒グラフ"""
    cat_sales = df_cleaned.groupby("category")["amount"].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = plt.cm.Blues_r([i / len(cat_sales) * 0.6 + 0.2 for i in range(len(cat_sales))])
    bars = ax.bar(cat_sales.index, cat_sales.values, color=colors, edgecolor="white", linewidth=0.8)

    for bar, val in zip(bars, cat_sales.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + cat_sales.max() * 0.01,
            f"{val:,}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_title("カテゴリ別累計売上", fontsize=14, pad=12)
    ax.set_xlabel("カテゴリ", fontsize=11)
    ax.set_ylabel("累計売上（円）", fontsize=11)
    ax.set_ylim(0, cat_sales.max() * 1.15)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    out = CHARTS_DIR / "bar_category_amount.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] グラフ保存: {out}")


def main():
    if not RFM_CSV.exists():
        raise FileNotFoundError(f"[FAIL] RFM CSVが見つかりません: {RFM_CSV}")
    if not CLEANED_CSV.exists():
        raise FileNotFoundError(f"[FAIL] クレンジング済みCSVが見つかりません: {CLEANED_CSV}")

    rfm = pd.read_csv(RFM_CSV, encoding="utf-8-sig")
    df_cleaned = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")

    plot_segment_count(rfm)
    plot_scatter_rfm(rfm)
    plot_category_amount(df_cleaned)

    print(f"[OK] 全グラフ出力完了: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
