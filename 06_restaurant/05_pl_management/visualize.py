# -*- coding: utf-8 -*-
"""
C-54: 店舗別損益・原価率管理パイプライン
可視化スクリプト
3グラフを output/charts/ に保存
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "cleaned_pl_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["food_cost"] = pd.to_numeric(df["food_cost"], errors="coerce")
    df["labor_cost"] = pd.to_numeric(df["labor_cost"], errors="coerce")
    df["other_cost"] = pd.to_numeric(df["other_cost"], errors="coerce")
    df["gross_profit"] = pd.to_numeric(df["gross_profit"], errors="coerce")
    df["profit_margin"] = pd.to_numeric(df["profit_margin"], errors="coerce")
    return df


def plot_bar_store_revenue(df: pd.DataFrame):
    """1. 店舗別売上合計（縦棒）"""
    store_rev = (
        df.groupby("store_name")["revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6"]
    bars = ax.bar(store_rev.index, store_rev.values, color=colors[: len(store_rev)])

    ax.set_title("店舗別 総売上（縦棒グラフ）", fontsize=14, fontweight="bold")
    ax.set_xlabel("店舗名", fontsize=11)
    ax.set_ylabel("総売上（円）", fontsize=11)

    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + h * 0.01,
            f"{int(h):,}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x):,}")
    )
    plt.tight_layout()
    out = CHARTS_DIR / "bar_store_revenue.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")


def plot_bar_store_margin(df: pd.DataFrame):
    """2. 店舗別利益率（横棒、赤字は赤色）"""
    store_margin = (
        df.groupby("store_name").apply(
            lambda g: g["gross_profit"].sum() / g["revenue"].sum() * 100
            if g["revenue"].sum() > 0 else 0
        )
        .sort_values(ascending=True)
    )

    colors = ["#E74C3C" if v < 0 else "#3498DB" for v in store_margin.values]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(store_margin.index, store_margin.values, color=colors)

    ax.set_title("店舗別 利益率（横棒グラフ、赤字は赤色）", fontsize=14, fontweight="bold")
    ax.set_xlabel("利益率（%）", fontsize=11)
    ax.set_ylabel("店舗名", fontsize=11)
    ax.axvline(x=0, color="black", linewidth=0.8, linestyle="--")

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 0.2 if w >= 0 else w - 0.2,
            bar.get_y() + bar.get_height() / 2,
            f"{w:.1f}%",
            ha="left" if w >= 0 else "right",
            va="center",
            fontsize=9,
        )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_store_margin.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")


def plot_bar_cost_breakdown(df: pd.DataFrame):
    """3. 店舗別コスト内訳積み上げ（食材費/人件費/その他）"""
    store_food = df.groupby("store_name")["food_cost"].sum()
    store_labor = df.groupby("store_name")["labor_cost"].sum()
    store_other = df.groupby("store_name")["other_cost"].sum()

    stores = store_food.index.tolist()

    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(stores))
    w = 0.6

    p1 = ax.bar(x, store_food.values, w, label="食材費", color="#E74C3C")
    p2 = ax.bar(x, store_labor.values, w, bottom=store_food.values, label="人件費", color="#3498DB")
    bottom3 = store_food.values + store_labor.values
    p3 = ax.bar(x, store_other.values, w, bottom=bottom3, label="その他経費", color="#2ECC71")

    ax.set_title("店舗別 コスト内訳（積み上げ棒グラフ）", fontsize=14, fontweight="bold")
    ax.set_xlabel("店舗名", fontsize=11)
    ax.set_ylabel("コスト（円）", fontsize=11)
    ax.set_xticks(list(x))
    ax.set_xticklabels(stores)
    ax.legend(loc="upper right")
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}")
    )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_cost_breakdown.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")


def main():
    print("[INFO] Visualization start ...")
    df = load_data()
    plot_bar_store_revenue(df)
    plot_bar_store_margin(df)
    plot_bar_cost_breakdown(df)
    print("[INFO] Visualization complete")


if __name__ == "__main__":
    main()
