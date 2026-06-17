"""
C-39: 入居者対応履歴・クレーム集計パイプライン
可視化スクリプト
3枚のグラフを output/charts/ に保存する
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_CSV = OUTPUT_DIR / "cleaned_claims_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
    df["response_days"] = pd.to_numeric(df["response_days"], errors="coerce")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    return df


def plot_bar_property_claims(df: pd.DataFrame):
    """1. 物件別クレーム件数の棒グラフ"""
    counts = df.groupby("property_name")["case_no"].count().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(counts.index, counts.values, color="#4C72B0", edgecolor="white")
    ax.bar_label(bars, fmt="%d", padding=3)
    ax.set_title("物件別クレーム件数", fontsize=14, pad=12)
    ax.set_xlabel("物件名", fontsize=11)
    ax.set_ylabel("件数", fontsize=11)
    ax.tick_params(axis="x", rotation=15)
    ax.set_ylim(0, counts.max() * 1.2)
    plt.tight_layout()
    out = CHARTS_DIR / "bar_property_claims.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"[OK] {out}")


def plot_bar_claim_type(df: pd.DataFrame):
    """2. クレーム区分別件数の横棒グラフ"""
    counts = df.groupby("claim_type")["case_no"].count().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(counts.index, counts.values, color="#DD8452", edgecolor="white")
    ax.bar_label(bars, fmt="%d", padding=3)
    ax.set_title("クレーム区分別発生件数", fontsize=14, pad=12)
    ax.set_xlabel("件数", fontsize=11)
    ax.set_ylabel("クレーム区分", fontsize=11)
    ax.set_xlim(0, counts.max() * 1.2)
    plt.tight_layout()
    out = CHARTS_DIR / "bar_claim_type.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"[OK] {out}")


def plot_bar_status_dist(df: pd.DataFrame):
    """3. 対応状況別件数の棒グラフ（解決済/対応中/未対応）"""
    order = ["解決済", "対応中", "未対応"]
    counts = df["status"].value_counts().reindex(order, fill_value=0)
    colors = ["#55A868", "#4C72B0", "#C44E52"]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(counts.index, counts.values, color=colors, edgecolor="white")
    ax.bar_label(bars, fmt="%d", padding=3)
    ax.set_title("対応状況別件数", fontsize=14, pad=12)
    ax.set_xlabel("対応状況", fontsize=11)
    ax.set_ylabel("件数", fontsize=11)
    ax.set_ylim(0, counts.max() * 1.2)
    plt.tight_layout()
    out = CHARTS_DIR / "bar_status_dist.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"[OK] {out}")


def visualize():
    if not CLEANED_CSV.exists():
        raise FileNotFoundError(f"Cleaned CSV not found: {CLEANED_CSV}. Run cleanse.py first.")

    df = load_data()
    print(f"[OK] Data loaded: {len(df)} rows")

    plot_bar_property_claims(df)
    plot_bar_claim_type(df)
    plot_bar_status_dist(df)

    print(f"\n[DONE] All charts saved to {CHARTS_DIR}")


if __name__ == "__main__":
    visualize()
