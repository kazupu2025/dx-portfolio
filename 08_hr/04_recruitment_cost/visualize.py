"""
C-41: 可視化スクリプト
output/charts/ に 3枚のグラフを出力
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_recruitment_202401.csv"

PHASES = ["書類選考", "一次面接", "二次面接", "最終面接", "内定"]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def chart_bar_channel_cost(df: pd.DataFrame):
    """チャネル別平均採用コストの棒グラフ"""
    channel_cost = (
        df.groupby("channel")["cost"]
        .mean()
        .reset_index()
        .sort_values("cost", ascending=False)
    )

    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        channel_cost["channel"],
        channel_cost["cost"],
        color=colors[: len(channel_cost)],
    )
    ax.set_title("チャネル別 平均採用コスト", fontsize=14, pad=12)
    ax.set_xlabel("採用チャネル", fontsize=12)
    ax.set_ylabel("平均採用コスト (円)", fontsize=12)
    ax.set_ylim(0, channel_cost["cost"].max() * 1.25)

    for bar, val in zip(bars, channel_cost["cost"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + channel_cost["cost"].max() * 0.01,
            f"{val:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_channel_cost.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_channel_hire_rate(df: pd.DataFrame):
    """チャネル別採用率の横棒グラフ"""
    channel_summary = (
        df.groupby("channel")
        .agg(total=("apply_no", "count"), hired=("is_hired", "sum"))
        .reset_index()
    )
    channel_summary["hire_rate"] = (
        channel_summary["hired"] / channel_summary["total"] * 100
    ).round(1)
    channel_summary = channel_summary.sort_values("hire_rate", ascending=True)

    colors = ["#59a14f", "#76b7b2", "#f28e2b", "#e15759", "#4e79a7"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(
        channel_summary["channel"],
        channel_summary["hire_rate"],
        color=colors[: len(channel_summary)],
    )
    ax.set_title("チャネル別 採用率", fontsize=14, pad=12)
    ax.set_xlabel("採用率 (%)", fontsize=12)
    ax.set_ylabel("採用チャネル", fontsize=12)
    ax.set_xlim(0, channel_summary["hire_rate"].max() * 1.3 + 2)

    for bar, rate in zip(bars, channel_summary["hire_rate"]):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{rate:.1f}%",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_channel_hire_rate.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_phase_funnel(df: pd.DataFrame):
    """選考フェーズ別応募者数（ファネル）の棒グラフ"""
    phase_counts = []
    for phase in PHASES:
        count = (df["phase"] == phase).sum()
        phase_counts.append(count)

    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(PHASES, phase_counts, color=colors)
    ax.set_title("選考フェーズ別 応募者数（ファネル）", fontsize=14, pad=12)
    ax.set_xlabel("選考フェーズ", fontsize=12)
    ax.set_ylabel("応募者数 (名)", fontsize=12)
    ax.set_ylim(0, max(phase_counts) * 1.2)

    for bar, count in zip(bars, phase_counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(phase_counts) * 0.01,
            f"{count:,} 名",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_phase_funnel.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def main():
    df = load_data()
    chart_bar_channel_cost(df)
    chart_bar_channel_hire_rate(df)
    chart_bar_phase_funnel(df)
    print(f"\nグラフ生成完了: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
