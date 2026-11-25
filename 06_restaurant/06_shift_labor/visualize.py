# -*- coding: utf-8 -*-
"""
C-40: アルバイトシフト管理・人件費集計パイプライン
可視化スクリプト
3枚のグラフを output/charts/ に保存
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

INPUT_FILE = OUTPUT_DIR / "cleaned_shift_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    df["hourly_rate"] = pd.to_numeric(df["hourly_rate"], errors="coerce")
    df["daily_wage"] = pd.to_numeric(df["daily_wage"], errors="coerce")
    return df


def plot_store_labor_cost(df: pd.DataFrame):
    """1. 店舗別総人件費の棒グラフ"""
    store_cost = (
        df.groupby("store_name")["daily_wage"]
        .sum()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#E74C3C", "#3498DB", "#2ECC71"]
    bars = ax.bar(store_cost.index, store_cost.values, color=colors[: len(store_cost)])

    ax.set_title("店舗別 総人件費（2024年1月）", fontsize=14, fontweight="bold")
    ax.set_xlabel("店舗名", fontsize=11)
    ax.set_ylabel("総人件費（円）", fontsize=11)

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
    out = CHARTS_DIR / "bar_store_labor_cost.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")


def plot_role_avg_wage(df: pd.DataFrame):
    """2. 役職別平均日次賃金の棒グラフ"""
    role_wage = (
        df.groupby("role")["daily_wage"]
        .mean()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#9B59B6", "#F39C12", "#1ABC9C"]
    bars = ax.bar(role_wage.index, role_wage.values, color=colors[: len(role_wage)])

    ax.set_title("役職別 平均日次賃金（2024年1月）", fontsize=14, fontweight="bold")
    ax.set_xlabel("役職", fontsize=11)
    ax.set_ylabel("平均日次賃金（円）", fontsize=11)

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
    out = CHARTS_DIR / "bar_role_avg_wage.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")


def plot_staff_hours_top10(df: pd.DataFrame):
    """3. スタッフ別労働時間上位10人の横棒グラフ"""
    staff_hours = (
        df.groupby("staff_id")["work_hours"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#E74C3C" if i == 0 else "#3498DB" for i in range(len(staff_hours))]
    bars = ax.barh(
        staff_hours.index[::-1],
        staff_hours.values[::-1],
        color=colors[::-1],
    )

    ax.set_title("スタッフ別 月間労働時間 上位10名（2024年1月）", fontsize=14, fontweight="bold")
    ax.set_xlabel("総労働時間（時間）", fontsize=11)
    ax.set_ylabel("スタッフID", fontsize=11)

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{w:.1f}h",
            ha="left",
            va="center",
            fontsize=9,
        )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_staff_hours_top10.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")


def main():
    print("[INFO] 可視化開始 ...")
    df = load_data()
    plot_store_labor_cost(df)
    plot_role_avg_wage(df)
    plot_staff_hours_top10(df)
    print("[INFO] 可視化完了")


if __name__ == "__main__":
    main()
