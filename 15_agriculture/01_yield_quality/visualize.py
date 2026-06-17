# -*- coding: utf-8 -*-
"""
C-49 作物収量・品質検査レポートパイプライン
可視化スクリプト
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = os.path.dirname(__file__)
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_harvest_202401.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    return df


def plot_farm_harvest(df):
    grp = df.groupby("farm_name")["harvest_qty"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(grp.index, grp.values, color="steelblue")
    ax.set_title("農場別収穫量合計 (2024年1月)")
    ax.set_xlabel("農場名")
    ax.set_ylabel("収穫量 (kg)")
    ax.tick_params(axis='x', rotation=0)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "bar_farm_harvest.png")
    fig.savefig(path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def plot_crop_grade_a_rate(df):
    grp = df.groupby("crop")["grade_a_rate"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(grp.index, grp.values, color="seagreen")
    ax.set_title("作物別平均A等級率 (2024年1月)")
    ax.set_xlabel("平均A等級率")
    ax.set_ylabel("作物")
    ax.set_xlim(0, 1)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "bar_crop_grade_a_rate.png")
    fig.savefig(path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def plot_quality_flag_dist(df):
    flag_order = ["優良", "合格", "要改善"]
    counts = df["quality_flag"].value_counts()
    counts = counts.reindex(flag_order, fill_value=0)
    colors = ["#2ecc71", "#f39c12", "#e74c3c"]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(counts.index, counts.values, color=colors)
    ax.set_title("品質フラグ分布 (2024年1月)")
    ax.set_xlabel("品質フラグ")
    ax.set_ylabel("件数")
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "bar_quality_flag_dist.png")
    fig.savefig(path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def main():
    df = load_data()
    print(f"[OK] Loaded {len(df)} rows")
    plot_farm_harvest(df)
    plot_crop_grade_a_rate(df)
    plot_quality_flag_dist(df)
    print("[OK] All charts saved")


if __name__ == "__main__":
    main()
