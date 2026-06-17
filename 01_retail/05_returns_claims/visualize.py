# -*- coding: utf-8 -*-
"""
C-34 返品・クレームデータ集計レポートパイプライン
可視化スクリプト

cleaned_claims_202401.csv を読み込み、3 枚のグラフを output/charts/ に保存する。
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # ヘッドレス環境向け
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"


def load_data(base_dir: Path) -> pd.DataFrame:
    csv_path = base_dir / "output" / "cleaned_claims_202401.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"[ERROR] {csv_path} が見つかりません。cleanse.py を先に実行してください。")
    return pd.read_csv(csv_path, encoding="utf-8-sig")


def plot_bar_store_claim_count(df: pd.DataFrame, charts_dir: Path) -> None:
    """棒グラフ: 店舗別クレーム件数"""
    store_counts = df.groupby("store_name")["case_no"].count().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(store_counts.index, store_counts.values, color="#4C72B0", edgecolor="white")

    ax.set_title("店舗別クレーム件数", fontsize=14, pad=12)
    ax.set_xlabel("店舗名", fontsize=11)
    ax.set_ylabel("件数", fontsize=11)
    ax.set_ylim(0, store_counts.max() * 1.15)

    for bar, val in zip(bars, store_counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            str(val),
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.tight_layout()
    out_path = charts_dir / "bar_store_claim_count.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[DONE] {out_path}")


def plot_bar_claim_type(df: pd.DataFrame, charts_dir: Path) -> None:
    """横棒グラフ: クレーム区分別件数"""
    type_counts = df.groupby("claim_type")["case_no"].count().sort_values(ascending=True)

    colors = ["#55A868", "#C44E52", "#4C72B0", "#DD8452"]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(type_counts.index, type_counts.values, color=colors[: len(type_counts)], edgecolor="white")

    ax.set_title("クレーム区分別件数", fontsize=14, pad=12)
    ax.set_xlabel("件数", fontsize=11)
    ax.set_ylabel("クレーム区分", fontsize=11)
    ax.set_xlim(0, type_counts.max() * 1.15)

    for bar, val in zip(bars, type_counts.values):
        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            str(val),
            ha="left",
            va="center",
            fontsize=10,
        )

    plt.tight_layout()
    out_path = charts_dir / "bar_claim_type.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[DONE] {out_path}")


def plot_pie_response_level(df: pd.DataFrame, charts_dir: Path) -> None:
    """円グラフ: 対応スピード別件数"""
    level_counts = df.groupby("response_level")["case_no"].count()
    order = ["迅速", "標準", "遅延"]
    level_counts = level_counts.reindex([o for o in order if o in level_counts.index])

    colors = ["#55A868", "#4C72B0", "#C44E52"]
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        level_counts.values,
        labels=level_counts.index,
        autopct="%1.1f%%",
        colors=colors[: len(level_counts)],
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for t in texts:
        t.set_fontsize(12)
    for at in autotexts:
        at.set_fontsize(11)
        at.set_color("white")
        at.set_fontweight("bold")

    ax.set_title("対応スピード別件数", fontsize=14, pad=12)

    plt.tight_layout()
    out_path = charts_dir / "pie_response_level.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[DONE] {out_path}")


def main() -> None:
    base_dir = Path(__file__).parent
    charts_dir = base_dir / "output" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(base_dir)
    print(f"[LOAD] {len(df)} rows loaded")

    plot_bar_store_claim_count(df, charts_dir)
    plot_bar_claim_type(df, charts_dir)
    plot_pie_response_level(df, charts_dir)

    print("[INFO] All charts saved.")


if __name__ == "__main__":
    main()
