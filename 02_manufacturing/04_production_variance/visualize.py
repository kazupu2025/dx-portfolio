# -*- coding: utf-8 -*-
"""
C-25: 生産計画 vs 実績 差異分析パイプライン
可視化スクリプト

3枚のグラフを output/charts/ に保存する。
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

CLEANED_CSV = OUTPUT_DIR / "cleaned_production_202401.csv"


def load_data() -> pd.DataFrame:
    if not CLEANED_CSV.exists():
        raise FileNotFoundError(f"クレンジング済みCSVが見つかりません: {CLEANED_CSV}")
    return pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")


def plot_bar_line_achievement(df: pd.DataFrame) -> None:
    """1. ライン別達成率の棒グラフ（100%ラインに赤点線）"""
    grp = df.groupby("line_name")["achievement_rate"].mean().reset_index()
    grp = grp.sort_values("line_name")

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(grp["line_name"], grp["achievement_rate"] * 100,
                  color="#4C72B0", edgecolor="white", alpha=0.85)
    ax.axhline(y=100, color="red", linestyle="--", linewidth=1.5, label="計画達成ライン (100%)")
    ax.set_xlabel("製造ライン")
    ax.set_ylabel("平均達成率 (%)")
    ax.set_title("ライン別 平均達成率")
    ax.set_ylim(0, max(grp["achievement_rate"].max() * 100 * 1.15, 110))
    ax.legend()
    ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)

    out_path = CHARTS_DIR / "bar_line_achievement.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[OK] Saved: {out_path}")


def plot_bar_category_defect_rate(df: pd.DataFrame) -> None:
    """2. カテゴリ別不良率の棒グラフ"""
    grp = df.groupby("category")["defect_rate"].mean().reset_index()
    grp = grp.sort_values("defect_rate", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(grp["category"], grp["defect_rate"] * 100,
                  color="#DD8452", edgecolor="white", alpha=0.85)
    ax.set_xlabel("製品カテゴリ")
    ax.set_ylabel("平均不良率 (%)")
    ax.set_title("カテゴリ別 平均不良率")
    ax.bar_label(bars, fmt="%.2f%%", padding=3, fontsize=9)

    out_path = CHARTS_DIR / "bar_category_defect_rate.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[OK] Saved: {out_path}")


def plot_scatter_planned_vs_actual(df: pd.DataFrame) -> None:
    """3. 計画数量 vs 実績数量の散布図"""
    fig, ax = plt.subplots(figsize=(7, 6))

    # ライン別に色を分ける
    lines = sorted(df["line_name"].unique())
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"]
    for i, line in enumerate(lines):
        sub = df[df["line_name"] == line]
        ax.scatter(sub["planned_qty"], sub["actual_qty"],
                   alpha=0.5, s=20, color=colors[i % len(colors)], label=line)

    # 対角線（計画=実績ライン）
    max_val = max(df["planned_qty"].max(), df["actual_qty"].max()) * 1.05
    ax.plot([0, max_val], [0, max_val], "k--", linewidth=1, label="計画=実績ライン")
    ax.set_xlabel("計画数量")
    ax.set_ylabel("実績数量")
    ax.set_title("計画数量 vs 実績数量")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)

    out_path = CHARTS_DIR / "scatter_planned_vs_actual.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[OK] Saved: {out_path}")


def visualize():
    df = load_data()
    print(f"[OK] データ読み込み完了: {len(df)} 行")
    plot_bar_line_achievement(df)
    plot_bar_category_defect_rate(df)
    plot_scatter_planned_vs_actual(df)
    print("[OK] 可視化完了")


if __name__ == "__main__":
    visualize()
