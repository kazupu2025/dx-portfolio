# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
可視化スクリプト: 3枚のグラフを output/charts/ に保存する
日本語フォント: MS Gothic
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_reception_202401.csv"


def load_data() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def plot_bar_dept_wait(df: pd.DataFrame):
    """診療科別平均待ち時間の棒グラフ"""
    dept_avg = (
        df.groupby("department")["wait_minutes"]
        .mean()
        .round(1)
        .sort_values(ascending=False)
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#E74C3C" if v > 60 else ("#F39C12" if v > 30 else "#3498DB")
              for v in dept_avg["wait_minutes"].tolist()]
    bars = ax.bar(dept_avg["department"].tolist(), dept_avg["wait_minutes"].tolist(), color=colors)

    for bar, val in zip(bars, dept_avg["wait_minutes"].tolist()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1f}分", ha="center", va="bottom", fontsize=10)

    ax.set_xlabel("診療科", fontsize=11)
    ax.set_ylabel("平均待ち時間 (分)", fontsize=11)
    ax.set_title("診療科別 平均待ち時間", fontsize=13, fontweight="bold")
    ax.axhline(y=30, color="orange", linestyle="--", linewidth=1.2, label="警告ライン (30分)")
    ax.axhline(y=60, color="red", linestyle="--", linewidth=1.2, label="長待ちライン (60分)")
    ax.legend(fontsize=9)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_dept_wait.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] 保存: {out_path}")


def plot_heatmap_timeslot_dept(df: pd.DataFrame):
    """時間帯 x 診療科の来院件数ヒートマップ"""
    pivot = (
        df.groupby(["time_slot", "department"])
        .size()
        .unstack(fill_value=0)
    )
    pivot = pivot.sort_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns.tolist(), fontsize=10)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index.tolist(), fontsize=10)

    # セル内に数値表示
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            ax.text(j, i, str(int(val)), ha="center", va="center",
                    fontsize=9, color="black" if val < pivot.values.max() * 0.6 else "white")

    plt.colorbar(im, ax=ax, label="来院件数")
    ax.set_xlabel("診療科", fontsize=11)
    ax.set_ylabel("時間帯", fontsize=11)
    ax.set_title("時間帯 x 診療科 来院件数ヒートマップ", fontsize=13, fontweight="bold")

    plt.tight_layout()
    out_path = CHARTS_DIR / "heatmap_timeslot_dept.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] 保存: {out_path}")


def plot_bar_wait_level(df: pd.DataFrame):
    """待ち時間レベル別件数の棒グラフ"""
    order = ["短待ち", "普通", "長待ち"]
    wait_counts = df["wait_level"].value_counts().reindex(order, fill_value=0)

    colors = ["#3498DB", "#F39C12", "#E74C3C"]
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(wait_counts.index.tolist(), wait_counts.values.tolist(), color=colors)

    for bar, val in zip(bars, wait_counts.values.tolist()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val} 件", ha="center", va="bottom", fontsize=11)

    ax.set_xlabel("待ち時間レベル", fontsize=11)
    ax.set_ylabel("件数", fontsize=11)
    ax.set_title("待ち時間レベル別 来院件数", fontsize=13, fontweight="bold")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_wait_level.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] 保存: {out_path}")


def main():
    print("[INFO] 可視化開始...")
    df = load_data()
    print(f"[INFO] データ読み込み: {len(df)} 件")

    plot_bar_dept_wait(df)
    plot_heatmap_timeslot_dept(df)
    plot_bar_wait_level(df)

    print("[OK] 全グラフ生成完了")


if __name__ == "__main__":
    main()
