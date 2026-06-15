"""
B-11: 与信スコアリング 可視化（3チャート）
1. bar_risk_distribution.png  — リスク分類別申込者数
2. bar_occupation_score.png   — 職業別平均与信スコア
3. hist_credit_score.png      — 与信スコアのヒストグラム
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import yaml

# 日本語フォント設定（Windows）
matplotlib.rcParams["font.family"] = ["MS Gothic", "Yu Gothic", "Meiryo", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False

BASE = Path(__file__).parent.parent
OUT = Path(__file__).parent
CHARTS = OUT / "charts"

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

CSV_PATH = OUT / "cleaned_credit_202401.csv"

RISK_COLORS = {
    "高リスク": "#e74c3c",
    "中リスク": "#e67e22",
    "低リスク": "#27ae60",
}


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} が存在しません。cleanse.py を先に実行してください。")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    high_th = config["high_risk_threshold"]
    med_th = config["medium_risk_threshold"]

    # =====================================================
    # 1. リスク分類別申込者数 棒グラフ
    # =====================================================
    risk_order = ["高リスク", "中リスク", "低リスク"]
    risk_counts = df["risk_category"].value_counts().reindex(risk_order, fill_value=0)

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(
        risk_counts.index,
        risk_counts.values,
        color=[RISK_COLORS[r] for r in risk_counts.index],
        edgecolor="white",
        linewidth=0.8,
    )
    for bar, val in zip(bars, risk_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f"{val}件", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_title("リスク分類別 申込者数", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("リスク分類", fontsize=11)
    ax.set_ylabel("申込者数（件）", fontsize=11)
    ax.set_ylim(0, risk_counts.max() * 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    out1 = CHARTS / "bar_risk_distribution.png"
    fig.savefig(out1, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out1}")

    # =====================================================
    # 2. 職業別平均与信スコア 棒グラフ
    # =====================================================
    occ_score = (
        df.groupby("occupation")["credit_score"]
        .mean()
        .sort_values(ascending=False)
    )

    def occ_color(score: float) -> str:
        if score < high_th:
            return RISK_COLORS["高リスク"]
        elif score < med_th:
            return RISK_COLORS["中リスク"]
        else:
            return RISK_COLORS["低リスク"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        occ_score.index,
        occ_score.values,
        color=[occ_color(s) for s in occ_score.values],
        edgecolor="white",
        linewidth=0.8,
    )
    for bar, val in zip(bars, occ_score.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    # 閾値ライン
    ax.axhline(y=high_th, color=RISK_COLORS["高リスク"], linestyle="--", linewidth=1.2,
               label=f"高リスク閾値 ({high_th}点)")
    ax.axhline(y=med_th, color=RISK_COLORS["中リスク"], linestyle="--", linewidth=1.2,
               label=f"中リスク閾値 ({med_th}点)")

    ax.set_title("職業別 平均与信スコア", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("職業", fontsize=11)
    ax.set_ylabel("平均与信スコア（点）", fontsize=11)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    out2 = CHARTS / "bar_occupation_score.png"
    fig.savefig(out2, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out2}")

    # =====================================================
    # 3. 与信スコア ヒストグラム
    # =====================================================
    bins = list(range(0, 101, 10))
    fig, ax = plt.subplots(figsize=(9, 5))

    # スコアを10点刻みでビン分け、高リスクゾーン（<40）は赤、それ以外はグレー
    for lo, hi in zip(bins[:-1], bins[1:]):
        count = df["credit_score"].between(lo, hi - 1).sum() if hi < 100 else df["credit_score"].between(lo, 100).sum()
        color = RISK_COLORS["高リスク"] if hi <= high_th else ("#95a5a6" if hi <= med_th else RISK_COLORS["低リスク"])
        bar = ax.bar(lo + 5, count, width=9, color=color, edgecolor="white", linewidth=0.5)
        if count > 0:
            ax.text(lo + 5, count + 0.5, str(count), ha="center", va="bottom", fontsize=8)

    # 凡例
    patches = [
        mpatches.Patch(color=RISK_COLORS["高リスク"], label=f"高リスク（0〜{high_th-1}点）"),
        mpatches.Patch(color="#95a5a6", label=f"中リスク（{high_th}〜{med_th-1}点）"),
        mpatches.Patch(color=RISK_COLORS["低リスク"], label=f"低リスク（{med_th}〜100点）"),
    ]
    ax.legend(handles=patches, fontsize=9)
    ax.set_title("与信スコア分布（ヒストグラム）", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("与信スコア（点）", fontsize=11)
    ax.set_ylabel("申込者数（件）", fontsize=11)
    ax.set_xticks(bins)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    out3 = CHARTS / "hist_credit_score.png"
    fig.savefig(out3, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out3}")

    print("\n可視化完了: 3チャート生成")


if __name__ == "__main__":
    main()
