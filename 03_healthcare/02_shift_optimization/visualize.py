"""
visualize.py
分析結果を可視化して output/charts/ に PNG を出力する。
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_shift_202401.csv")
SUMMARY_FILE = os.path.join(BASE_DIR, "output", "shift_summary_202401.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")

os.makedirs(CHARTS_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    summary = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
    return df, summary


def chart1_role_night_ratio(df: pd.DataFrame):
    """役職別夜勤希望率（棒グラフ）"""
    role_order = ["看護師", "介護士", "看護補助", "リハビリ師"]
    role_night = (
        df.groupby("role")["preferred_shift"]
        .apply(lambda s: (s == "夜勤").mean())
        .reindex(role_order)
        .fillna(0)
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2"]
    bars = ax.bar(role_night.index, role_night.values * 100, color=colors, edgecolor="white", linewidth=0.8)

    for bar, val in zip(bars, role_night.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{val * 100:.1f}%",
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )

    ax.set_title("役職別 夜勤希望率（2024年1月）", fontsize=14, pad=12)
    ax.set_xlabel("役職", fontsize=12)
    ax.set_ylabel("夜勤希望率 (%)", fontsize=12)
    ax.set_ylim(0, max(role_night.values * 100) * 1.25 + 1)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.0f%%"))
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = os.path.join(CHARTS_DIR, "bar_role_night_ratio.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[保存] {path}")


def chart2_staff_night_count(summary: pd.DataFrame):
    """夜勤希望回数 上位15名（横棒グラフ）"""
    top15 = summary.nlargest(15, "night_count").reset_index(drop=True)
    labels = top15["name"] + "\n(" + top15["role"] + ")"

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = plt.cm.RdYlGn_r([i / len(top15) for i in range(len(top15))])
    bars = ax.barh(labels[::-1], top15["night_count"][::-1], color=colors[::-1], edgecolor="white")

    for bar, val in zip(bars, top15["night_count"][::-1]):
        ax.text(
            bar.get_width() + 0.1,
            bar.get_y() + bar.get_height() / 2,
            f"{int(val)}回",
            va="center", fontsize=9
        )

    ax.set_title("夜勤希望回数 上位15名（2024年1月）", fontsize=14, pad=12)
    ax.set_xlabel("夜勤希望回数（回）", fontsize=12)
    ax.set_xlim(0, top15["night_count"].max() * 1.2 + 1)
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = os.path.join(CHARTS_DIR, "bar_staff_night_count.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[保存] {path}")


def chart3_stacked_shift_distribution(df: pd.DataFrame):
    """施設別シフト分布（積み上げ棒グラフ）"""
    df = df.copy()
    df["facility"] = df["source_file"].str.extract(r"0\d_(.+)_shift")

    shift_order = ["早番", "日勤", "遅番", "夜勤", "休み"]
    colors_map = {
        "早番": "#FFD700",
        "日勤": "#4C72B0",
        "遅番": "#FFA500",
        "夜勤": "#2C3E50",
        "休み": "#95A5A6",
    }

    pivot = (
        df.groupby(["facility", "preferred_shift"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=shift_order, fill_value=0)
    )
    # 割合に変換
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = pd.Series([0.0] * len(pivot_pct), index=pivot_pct.index)

    for shift in shift_order:
        vals = pivot_pct[shift] if shift in pivot_pct.columns else pd.Series(0, index=pivot_pct.index)
        bars = ax.bar(
            pivot_pct.index, vals, bottom=bottom,
            label=shift, color=colors_map[shift], edgecolor="white", linewidth=0.5
        )
        for bar, val, bot in zip(bars, vals, bottom):
            if val > 5:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bot + val / 2,
                    f"{val:.0f}%",
                    ha="center", va="center", fontsize=9, color="white", fontweight="bold"
                )
        bottom += vals

    ax.set_title("施設別 シフト希望分布（2024年1月）", fontsize=14, pad=12)
    ax.set_xlabel("施設", fontsize=12)
    ax.set_ylabel("割合 (%)", fontsize=12)
    ax.set_ylim(0, 110)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.0f%%"))
    ax.legend(title="シフト", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = os.path.join(CHARTS_DIR, "stacked_shift_distribution.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[保存] {path}")


def main():
    print("[可視化開始] visualize.py")
    df, summary = load_data()

    chart1_role_night_ratio(df)
    chart2_staff_night_count(summary)
    chart3_stacked_shift_distribution(df)

    print("\n[OK] チャート生成完了")


if __name__ == "__main__":
    main()
