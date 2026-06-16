"""
C-17 配送コスト分析パイプライン
可視化スクリプト
output/charts/ に3枚以上のグラフを出力する
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

matplotlib.rcParams['font.family'] = 'MS Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_delivery_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def plot_bar_route_cost_per_km(df: pd.DataFrame):
    """ルート別 cost_per_km 棒グラフ"""
    route_avg = df.groupby("route_id")["cost_per_km"].mean().sort_values(ascending=True)
    overall_avg = df["cost_per_km"].mean()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#e74c3c" if v > overall_avg else "#2ecc71" for v in route_avg.values]
    bars = ax.barh(route_avg.index, route_avg.values, color=colors)

    ax.axvline(overall_avg, color="navy", linestyle="--", linewidth=1.5, label=f"全体平均: ¥{overall_avg:.1f}/km")
    ax.set_xlabel("平均 cost_per_km（¥/km）", fontsize=12)
    ax.set_title("ルート別 配送コスト効率（cost_per_km）", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)

    for bar, val in zip(bars, route_avg.values):
        ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                f"¥{val:.1f}", va="center", fontsize=9)

    # 凡例パッチ
    above_patch = mpatches.Patch(color="#e74c3c", label="平均超（コスト高）")
    below_patch = mpatches.Patch(color="#2ecc71", label="平均以下（効率良）")
    ax.legend(handles=[above_patch, below_patch,
                       plt.Line2D([0], [0], color="navy", linestyle="--", linewidth=1.5,
                                  label=f"全体平均: ¥{overall_avg:.1f}/km")],
              fontsize=9, loc="lower right")

    plt.tight_layout()
    out = CHARTS_DIR / "bar_route_cost_per_km.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")


def plot_bar_vehicle_cost_breakdown(df: pd.DataFrame):
    """車種別コスト内訳（積み上げ棒グラフ）"""
    grp = df.groupby("vehicle_type")[["fuel_cost", "toll_cost", "driver_cost"]].mean().round(0)
    grp = grp.sort_values("fuel_cost", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(grp))
    labels = grp.index.tolist()

    bar1 = ax.bar(x, grp["fuel_cost"], label="燃料費", color="#e67e22")
    bar2 = ax.bar(x, grp["toll_cost"], bottom=grp["fuel_cost"], label="高速代", color="#3498db")
    bar3 = ax.bar(x, grp["driver_cost"],
                  bottom=grp["fuel_cost"] + grp["toll_cost"], label="人件費", color="#9b59b6")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("平均コスト（¥）", fontsize=12)
    ax.set_title("車種別 コスト内訳（積み上げ棒グラフ）", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"¥{v:,.0f}"))

    plt.tight_layout()
    out = CHARTS_DIR / "bar_vehicle_cost_breakdown.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")


def plot_pie_cost_components(df: pd.DataFrame):
    """コスト構成比（円グラフ）"""
    totals = {
        "燃料費": df["fuel_cost"].sum(),
        "高速代": df["toll_cost"].sum(),
        "人件費": df["driver_cost"].sum(),
    }
    colors = ["#e67e22", "#3498db", "#9b59b6"]
    explode = (0.03, 0.03, 0.03)

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        totals.values(),
        labels=totals.keys(),
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        explode=explode,
        textprops={"fontsize": 13},
    )
    for at in autotexts:
        at.set_fontsize(12)
        at.set_fontweight("bold")

    ax.set_title("月間コスト構成比（2024年1月）", fontsize=14, fontweight="bold")

    # 金額を凡例に追加
    legend_labels = [f"{k}: ¥{v:,.0f}" for k, v in totals.items()]
    ax.legend(legend_labels, loc="lower left", fontsize=10)

    plt.tight_layout()
    out = CHARTS_DIR / "pie_cost_components.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")


def main():
    print("[INFO] データ読み込み...")
    df = load_data()
    print(f"  {len(df)} rows")

    print("[INFO] グラフ生成中...")
    plot_bar_route_cost_per_km(df)
    plot_bar_vehicle_cost_breakdown(df)
    plot_pie_cost_components(df)

    charts = list(CHARTS_DIR.glob("*.png"))
    print(f"\n[OK] 合計 {len(charts)} 枚のグラフを生成しました: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
