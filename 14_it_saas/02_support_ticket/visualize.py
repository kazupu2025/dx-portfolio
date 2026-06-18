# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
可視化スクリプト
出力: output/charts/bar_category_count.png
      output/charts/bar_priority_escalation.png
      output/charts/bar_agent_resolution.png
"""

import os
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(__file__)
CLEANED_PATH = os.path.join(BASE_DIR, "output", "cleaned_tickets_202401.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(CLEANED_PATH, encoding="utf-8-sig")
    df["resolution_hours"] = pd.to_numeric(df["resolution_hours"], errors="coerce")
    df["is_resolved"] = pd.to_numeric(df["is_resolved"], errors="coerce")
    df["is_escalated"] = pd.to_numeric(df["is_escalated"], errors="coerce")
    df["satisfaction"] = pd.to_numeric(df["satisfaction"], errors="coerce")
    return df


def plot_category_count(df):
    """カテゴリ別チケット件数（横棒グラフ）"""
    cat_counts = df.groupby("category")["ticket_id"].count().sort_values()

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(cat_counts.index, cat_counts.values, color="#4C72B0")
    ax.set_xlabel("チケット件数")
    ax.set_title("カテゴリ別チケット件数")
    ax.bar_label(bars, padding=3)
    ax.set_xlim(0, cat_counts.values.max() * 1.15)

    plt.tight_layout()
    out = os.path.join(CHARTS_DIR, "bar_category_count.png")
    plt.savefig(out, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {out}")


def plot_priority_escalation(df):
    """優先度別エスカレーション率（縦棒グラフ）"""
    prio_order = ["高", "中", "低"]
    prio_esc = df.groupby("priority")["is_escalated"].mean().reindex(prio_order, fill_value=0)

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(prio_esc.index, prio_esc.values * 100, color=["#e74c3c", "#f39c12", "#2ecc71"])
    ax.set_xlabel("優先度")
    ax.set_ylabel("エスカレーション率 (%)")
    ax.set_title("優先度別エスカレーション率")
    ax.set_ylim(0, max(prio_esc.values.max() * 100 * 1.3, 10))
    ax.bar_label(bars, fmt="%.1f%%", padding=3)

    plt.tight_layout()
    out = os.path.join(CHARTS_DIR, "bar_priority_escalation.png")
    plt.savefig(out, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {out}")


def plot_agent_resolution(df):
    """担当者別解決率（横棒グラフ）"""
    agent_res = df.groupby("agent_id")["is_resolved"].mean().sort_values()

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.barh(agent_res.index, agent_res.values * 100, color="#2980b9")
    ax.set_xlabel("解決率 (%)")
    ax.set_title("担当者別解決率")
    ax.set_xlim(0, 110)
    ax.bar_label(bars, fmt="%.1f%%", padding=3)

    plt.tight_layout()
    out = os.path.join(CHARTS_DIR, "bar_agent_resolution.png")
    plt.savefig(out, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved: {out}")


def main():
    if not os.path.exists(CLEANED_PATH):
        print(f"[FAIL] クレンジング済みファイルが見つかりません: {CLEANED_PATH}")
        return

    df = load_data()
    print(f"[OK] データ読み込み: {len(df)}件")

    plot_category_count(df)
    plot_priority_escalation(df)
    plot_agent_resolution(df)

    print("[OK] 全グラフの保存完了")


if __name__ == "__main__":
    main()
