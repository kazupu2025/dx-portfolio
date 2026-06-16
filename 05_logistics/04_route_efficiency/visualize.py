# -*- coding: utf-8 -*-
"""
配送ルート効率化 可視化スクリプト
3枚のグラフを output/charts/ に保存する
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_CSV = OUTPUT_DIR / "cleaned_route_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
    for col in ["distance_km", "fuel_cost", "cost_per_delivery", "cost_per_km", "km_per_delivery"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["delay_flag"] = pd.to_numeric(df["delay_flag"], errors="coerce").fillna(0).astype(int)
    return df


def plot_route_cost_per_delivery(df: pd.DataFrame):
    """グラフ1: ルート別1件当たりコストの横棒グラフ"""
    route_avg = (
        df.groupby("route_id")["cost_per_delivery"]
        .mean()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#2196F3" if v < route_avg.median() else "#F44336" for v in route_avg.values]
    bars = ax.barh(route_avg.index, route_avg.values, color=colors)

    ax.set_xlabel("1件当たりコスト（円）", fontsize=12)
    ax.set_title("ルート別 1件当たり配送コスト", fontsize=14, fontweight="bold")
    ax.axvline(x=route_avg.median(), color="orange", linestyle="--", linewidth=1.5, label=f"中央値 {route_avg.median():.0f}円")
    ax.legend(fontsize=10)

    for bar, val in zip(bars, route_avg.values):
        ax.text(val + 5, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}", va="center", fontsize=9)

    blue_patch = mpatches.Patch(color="#2196F3", label="高効率（中央値未満）")
    red_patch = mpatches.Patch(color="#F44336", label="低効率（中央値以上）")
    ax.legend(handles=[blue_patch, red_patch,
                        plt.Line2D([0], [0], color="orange", linestyle="--", linewidth=1.5, label=f"中央値 {route_avg.median():.0f}円")],
              fontsize=9, loc="lower right")

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_route_cost_per_delivery.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[VIZ] 保存: {out_path}")


def plot_area_delay_rate(df: pd.DataFrame):
    """グラフ2: エリア別遅延率の棒グラフ"""
    area_stats = df.groupby("area").agg(
        delay_count=("delay_flag", "sum"),
        run_count=("date", "count"),
    ).reset_index()
    area_stats["delay_rate"] = area_stats["delay_count"] / area_stats["run_count"]
    area_stats = area_stats.sort_values("delay_rate", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(area_stats)))
    bars = ax.bar(area_stats["area"], area_stats["delay_rate"] * 100, color=colors)

    ax.set_ylabel("遅延率（%）", fontsize=12)
    ax.set_title("エリア別 遅延率", fontsize=14, fontweight="bold")
    ax.set_ylim(0, max(area_stats["delay_rate"].max() * 100 * 1.2, 10))

    for bar, val in zip(bars, area_stats["delay_rate"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val:.1%}", ha="center", fontsize=10)

    overall_delay = df["delay_flag"].mean() * 100
    ax.axhline(y=overall_delay, color="steelblue", linestyle="--", linewidth=1.5,
               label=f"全体平均 {overall_delay:.1f}%")
    ax.legend(fontsize=10)

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_area_delay_rate.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[VIZ] 保存: {out_path}")


def plot_distance_vs_cost_scatter(df: pd.DataFrame):
    """グラフ3: 走行距離 vs 燃料費の散布図（車両タイプ別色分け）"""
    vehicle_types = df["vehicle_type"].unique()
    colors_map = {
        "軽バン": "#4CAF50",
        "2tトラック": "#2196F3",
        "4tトラック": "#FF5722",
    }

    fig, ax = plt.subplots(figsize=(10, 6))

    for vt in vehicle_types:
        subset = df[df["vehicle_type"] == vt].dropna(subset=["distance_km", "fuel_cost"])
        color = colors_map.get(vt, "gray")
        ax.scatter(
            subset["distance_km"], subset["fuel_cost"],
            label=vt, color=color, alpha=0.6, s=40, edgecolors="white", linewidths=0.3
        )

    # 全体トレンドライン
    valid = df.dropna(subset=["distance_km", "fuel_cost"])
    if len(valid) > 1:
        z = np.polyfit(valid["distance_km"], valid["fuel_cost"], 1)
        p = np.poly1d(z)
        x_range = np.linspace(valid["distance_km"].min(), valid["distance_km"].max(), 100)
        ax.plot(x_range, p(x_range), "k--", linewidth=1.5, alpha=0.5, label="全体トレンド")

    ax.set_xlabel("走行距離（km）", fontsize=12)
    ax.set_ylabel("燃料費（円）", fontsize=12)
    ax.set_title("走行距離 vs 燃料費（車両タイプ別）", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = CHARTS_DIR / "scatter_distance_cost.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[VIZ] 保存: {out_path}")


def main():
    if not CLEANED_CSV.exists():
        print(f"[ERROR] クレンジング済みCSVが見つかりません: {CLEANED_CSV}")
        return

    df = load_data()
    print(f"[LOAD] {len(df)}行 読み込み完了")

    plot_route_cost_per_delivery(df)
    plot_area_delay_rate(df)
    plot_distance_vs_cost_scatter(df)

    print("[DONE] 可視化完了")


if __name__ == "__main__":
    main()
