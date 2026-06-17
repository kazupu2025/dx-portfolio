# -*- coding: utf-8 -*-
"""
C-52: 保険契約問い合わせ・対応履歴分析パイプライン 可視化スクリプト
3枚のグラフを output/charts/ に保存する。
日本語フォント: MS Gothic
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_inquiries_202401.csv"
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["handling_minutes", "is_resolved", "recontact_flag", "satisfaction"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ===== グラフ1: 問い合わせ区分別件数（横棒）=====
if "inquiry_type" in df.columns:
    type_order = ["契約内容確認", "保険金請求", "解約手続き", "新規加入", "変更手続き"]
    type_counts = (
        df["inquiry_type"]
        .value_counts()
        .reindex([t for t in type_order if t in df["inquiry_type"].unique()])
        .fillna(0)
        .astype(int)
    )
    # 残りの区分があれば追加
    for t in df["inquiry_type"].unique():
        if t not in type_counts.index:
            type_counts[t] = df["inquiry_type"].value_counts()[t]

    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(
        type_counts.index[::-1],
        type_counts.values[::-1],
        color=colors[: len(type_counts)][::-1],
    )
    ax.set_title("問い合わせ区分別 件数（2024年1月）", fontsize=14)
    ax.set_xlabel("件数")
    for bar in bars:
        w = bar.get_width()
        if w > 0:
            ax.text(
                w + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{int(w):,}", va="center", fontsize=10,
            )
    ax.set_xlim(0, type_counts.max() * 1.15)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "bar_type_count.png", dpi=150)
    plt.close()
    print("[OK] Saved: bar_type_count.png")

# ===== グラフ2: チャネル別平均満足度（縦棒）=====
if "channel" in df.columns and "satisfaction" in df.columns:
    channel_sat = df.groupby("channel")["satisfaction"].mean().sort_values(ascending=False)
    channel_colors = ["#2563eb", "#7c3aed", "#0891b2"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        channel_sat.index,
        channel_sat.values,
        color=channel_colors[: len(channel_sat)],
        width=0.5,
    )
    ax.set_title("チャネル別 平均満足度（2024年1月）", fontsize=14)
    ax.set_xlabel("チャネル")
    ax.set_ylabel("平均満足度（点）")
    ax.set_ylim(0, 5.5)
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + 0.05,
            f"{h:.2f}", ha="center", va="bottom", fontsize=11,
        )
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "bar_channel_satisfaction.png", dpi=150)
    plt.close()
    print("[OK] Saved: bar_channel_satisfaction.png")

# ===== グラフ3: 問い合わせ区分別解決率（横棒）=====
if "inquiry_type" in df.columns and "is_resolved" in df.columns:
    type_res_rate = (
        df.groupby("inquiry_type")["is_resolved"]
        .mean()
        .sort_values(ascending=True)
        * 100
    )
    res_colors = ["#22c55e" if v >= 85 else "#f59e0b" if v >= 70 else "#ef4444"
                  for v in type_res_rate.values]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(type_res_rate.index, type_res_rate.values, color=res_colors)
    ax.set_title("問い合わせ区分別 解決率（2024年1月）", fontsize=14)
    ax.set_xlabel("解決率 (%)")
    ax.set_xlim(0, 115)
    ax.axvline(x=85, color="#ef4444", linestyle="--", linewidth=1, label="目標 85%")
    ax.legend(fontsize=10)
    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{w:.1f}%", va="center", fontsize=10,
        )
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "bar_type_resolution.png", dpi=150)
    plt.close()
    print("[OK] Saved: bar_type_resolution.png")

print("[OK] Graph generation complete -> output/charts/")
