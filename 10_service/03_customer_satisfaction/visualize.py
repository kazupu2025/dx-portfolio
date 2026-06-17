# visualize.py — グラフ可視化モジュール（C-36 顧客満足度）
# encoding: utf-8

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"

OUTPUT_DIR = Path(__file__).parent / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_FILE = OUTPUT_DIR / "cleaned_satisfaction_202401.csv"


def plot_service_csat(df: pd.DataFrame) -> None:
    """グラフ1: サービス区分別 CSAT 平均の棒グラフ。"""
    svc_mean = (
        df.groupby("service_type")["csat_score"]
        .mean()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(svc_mean.index, svc_mean.values, color="#4C72B0", edgecolor="white")
    ax.set_title("サービス区分別 CSAT 平均", fontsize=14, pad=12)
    ax.set_xlabel("サービス区分", fontsize=11)
    ax.set_ylabel("平均 CSAT (1-5)", fontsize=11)
    ax.set_ylim(0, 5.5)
    ax.axhline(y=3.0, color="gray", linestyle="--", linewidth=0.8, label="基準値 3.0")
    for bar, val in zip(bars, svc_mean.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{val:.2f}", ha="center", va="bottom", fontsize=9)
    ax.legend()
    plt.tight_layout()
    path = CHARTS_DIR / "bar_service_csat.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"Saved: {path}")


def plot_nps_category(df: pd.DataFrame) -> None:
    """グラフ2: NPS 区分別件数の棒グラフ。"""
    order = ["推奨者", "中立者", "批判者"]
    colors = {"推奨者": "#2ca02c", "中立者": "#ffbb33", "批判者": "#d62728"}
    counts = df["nps_category"].value_counts().reindex(order, fill_value=0)

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(counts.index, counts.values,
                  color=[colors[k] for k in counts.index], edgecolor="white")
    ax.set_title("NPS 区分別件数", fontsize=14, pad=12)
    ax.set_xlabel("NPS 区分", fontsize=11)
    ax.set_ylabel("件数", fontsize=11)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(val), ha="center", va="bottom", fontsize=10)
    plt.tight_layout()
    path = CHARTS_DIR / "bar_nps_category.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"Saved: {path}")


def plot_agent_satisfaction(df: pd.DataFrame) -> None:
    """グラフ3: 担当者別平均満足度の横棒グラフ。"""
    agent_mean = (
        df.groupby("agent")["csat_score"]
        .mean()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.barh(agent_mean.index, agent_mean.values, color="#DD8452", edgecolor="white")
    ax.set_title("担当者別 平均満足度", fontsize=14, pad=12)
    ax.set_xlabel("平均 CSAT (1-5)", fontsize=11)
    ax.set_ylabel("担当者", fontsize=11)
    ax.set_xlim(0, 5.5)
    ax.axvline(x=3.0, color="gray", linestyle="--", linewidth=0.8, label="基準値 3.0")
    for bar, val in zip(bars, agent_mean.values):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", ha="left", va="center", fontsize=9)
    ax.legend()
    plt.tight_layout()
    path = CHARTS_DIR / "bar_agent_satisfaction.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"Saved: {path}")


def run() -> None:
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    plot_service_csat(df)
    plot_nps_category(df)
    plot_agent_satisfaction(df)
    print("All charts generated.")


if __name__ == "__main__":
    run()
