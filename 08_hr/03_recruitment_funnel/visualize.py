"""
C-33: 可視化スクリプト
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

PHASE_ORDER = {
    "書類選考": 1,
    "一次面接": 2,
    "二次面接": 3,
    "最終面接": 4,
    "内定": 5,
}
PHASES = ["書類選考", "一次面接", "二次面接", "最終面接", "内定"]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def chart_bar_funnel_passrate(df: pd.DataFrame):
    """フェーズ別通過率の棒グラフ（ファネル可視化）"""
    total = len(df)
    rates = []
    for phase in PHASES:
        phase_num = PHASE_ORDER[phase]
        count = (df["phase_order"] >= phase_num).sum()
        rate = count / total * 100 if total > 0 else 0
        rates.append(rate)

    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(PHASES, rates, color=colors)
    ax.set_title("フェーズ別 到達率（採用ファネル）", fontsize=14, pad=12)
    ax.set_xlabel("選考フェーズ", fontsize=12)
    ax.set_ylabel("到達率 (%)", fontsize=12)
    ax.set_ylim(0, 110)
    ax.axhline(100, color="gray", linewidth=0.8, linestyle="--")

    for bar, rate in zip(bars, rates):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_funnel_passrate.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_channel_hire_rate(df: pd.DataFrame):
    """チャネル別採用率の棒グラフ"""
    channel_summary = (
        df.groupby("channel")
        .agg(
            total=("applicant_id", "count"),
            hired=("is_hired", "sum"),
        )
        .reset_index()
    )
    channel_summary["hire_rate"] = (
        channel_summary["hired"] / channel_summary["total"] * 100
    ).round(1)
    channel_summary = channel_summary.sort_values("hire_rate", ascending=False)

    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        channel_summary["channel"],
        channel_summary["hire_rate"],
        color=colors[:len(channel_summary)],
    )
    ax.set_title("チャネル別 採用率", fontsize=14, pad=12)
    ax.set_xlabel("採用チャネル", fontsize=12)
    ax.set_ylabel("採用率 (%)", fontsize=12)
    ax.set_ylim(0, max(channel_summary["hire_rate"]) * 1.2 + 5)

    for bar, rate in zip(bars, channel_summary["hire_rate"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_channel_hire_rate.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_jobtype_screening_days(df: pd.DataFrame):
    """職種別平均選考日数の横棒グラフ"""
    jobtype_summary = (
        df.groupby("job_type")
        .agg(avg_days=("screening_days", "mean"))
        .reset_index()
        .sort_values("avg_days", ascending=True)
    )

    colors = ["#76b7b2", "#59a14f", "#f28e2b", "#4e79a7", "#e15759"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(
        jobtype_summary["job_type"],
        jobtype_summary["avg_days"],
        color=colors[:len(jobtype_summary)],
    )
    ax.set_title("職種別 平均選考日数", fontsize=14, pad=12)
    ax.set_xlabel("平均選考日数 (日)", fontsize=12)
    ax.set_ylabel("職種", fontsize=12)

    for bar, days in zip(bars, jobtype_summary["avg_days"]):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{days:.1f} 日",
            ha="left",
            va="center",
            fontsize=10,
        )

    ax.set_xlim(0, jobtype_summary["avg_days"].max() * 1.2 + 3)
    plt.tight_layout()
    out = CHARTS_DIR / "bar_jobtype_screening_days.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def main():
    df = load_data()
    chart_bar_funnel_passrate(df)
    chart_bar_channel_hire_rate(df)
    chart_bar_jobtype_screening_days(df)
    print(f"\nグラフ生成完了: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
