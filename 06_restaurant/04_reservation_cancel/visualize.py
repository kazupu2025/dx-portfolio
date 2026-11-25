# -*- coding: utf-8 -*-
"""
C-38: 予約キャンセル集計・傾向分析パイプライン
可視化スクリプト
3枚のグラフを output/charts/ に保存する
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "cleaned_reservations_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig", dtype=str)
    df["is_cancel"] = pd.to_numeric(df["is_cancel"], errors="coerce").fillna(0).astype(int)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0).astype(int)
    df["loss_amount"] = pd.to_numeric(df["loss_amount"], errors="coerce").fillna(0).astype(int)
    return df


def plot_store_cancel_rate(df: pd.DataFrame):
    """グラフ1: 店舗別キャンセル率の棒グラフ"""
    store_grp = df.groupby("store_name").agg(
        total=("is_cancel", "count"),
        cancel=("is_cancel", "sum"),
    )
    store_grp["cancel_rate"] = store_grp["cancel"] / store_grp["total"] * 100
    store_grp = store_grp.sort_values("cancel_rate", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        store_grp.index,
        store_grp["cancel_rate"],
        color=["#E74C3C", "#F39C12", "#3498DB"],
        edgecolor="white",
        width=0.5,
    )
    ax.set_title("店舗別キャンセル率", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("店舗名", fontsize=11)
    ax.set_ylabel("キャンセル率 (%)", fontsize=11)
    ax.set_ylim(0, max(store_grp["cancel_rate"]) * 1.3 + 1)
    ax.yaxis.grid(True, linestyle="--", alpha=0.6)
    ax.set_axisbelow(True)

    for bar, val in zip(bars, store_grp["cancel_rate"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{val:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_store_cancel_rate.png"
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {out_path}")


def plot_cancel_reason(df: pd.DataFrame):
    """グラフ2: キャンセル理由別件数の横棒グラフ"""
    cancel_df = df[df["is_cancel"] == 1].copy()
    reason_counts = cancel_df["cancel_reason"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#E74C3C", "#E67E22", "#F1C40F", "#2ECC71", "#3498DB"]
    bars = ax.barh(
        reason_counts.index,
        reason_counts.values,
        color=colors[: len(reason_counts)],
        edgecolor="white",
    )
    ax.set_title("キャンセル理由別件数", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("件数", fontsize=11)
    ax.set_ylabel("キャンセル理由", fontsize=11)
    ax.xaxis.grid(True, linestyle="--", alpha=0.6)
    ax.set_axisbelow(True)

    for bar, val in zip(bars, reason_counts.values):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            str(val),
            ha="left",
            va="center",
            fontsize=10,
        )

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_cancel_reason.png"
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {out_path}")


def plot_weekday_cancel(df: pd.DataFrame):
    """グラフ3: 曜日別キャンセル件数の棒グラフ"""
    weekday_order = ["月", "火", "水", "木", "金", "土", "日"]
    weekday_grp = df.groupby("day_of_week").agg(
        cancel_count=("is_cancel", "sum"),
    ).reset_index()
    # 曜日を順序付けカテゴリに
    weekday_grp["day_of_week"] = pd.Categorical(
        weekday_grp["day_of_week"], categories=weekday_order, ordered=True
    )
    weekday_grp = weekday_grp.sort_values("day_of_week")

    fig, ax = plt.subplots(figsize=(9, 5))
    bar_colors = ["#3498DB"] * 5 + ["#E74C3C"] * 2  # 週末を強調
    bars = ax.bar(
        weekday_grp["day_of_week"].astype(str),
        weekday_grp["cancel_count"],
        color=bar_colors[: len(weekday_grp)],
        edgecolor="white",
        width=0.6,
    )
    ax.set_title("曜日別キャンセル件数", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("曜日", fontsize=11)
    ax.set_ylabel("キャンセル件数", fontsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.6)
    ax.set_axisbelow(True)

    for bar, val in zip(bars, weekday_grp["cancel_count"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            str(int(val)),
            ha="center",
            va="bottom",
            fontsize=10,
        )

    # 凡例
    weekday_patch = mpatches.Patch(color="#3498DB", label="平日")
    weekend_patch = mpatches.Patch(color="#E74C3C", label="週末")
    ax.legend(handles=[weekday_patch, weekend_patch], loc="upper right")

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_weekday_cancel.png"
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {out_path}")


def main():
    df = load_data()
    print(f"[OK] Loaded {len(df)} rows")

    plot_store_cancel_rate(df)
    plot_cancel_reason(df)
    plot_weekday_cancel(df)

    print("[OK] All charts saved to output/charts/")


if __name__ == "__main__":
    main()
