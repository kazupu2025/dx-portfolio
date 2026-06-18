# -*- coding: utf-8 -*-
"""
C-59 農場スタッフ勤怠・作業効率分析パイプライン
可視化スクリプト
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = os.path.dirname(__file__)
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_farm_work_202401.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)


def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    return df


def plot_crop_achievement(df):
    grp = df.groupby("crop")["achievement_rate"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(grp.index, grp.values, color="steelblue")
    ax.set_title("作物別目標達成率 (2024年1月)")
    ax.set_xlabel("作物")
    ax.set_ylabel("平均達成率")
    ax.set_ylim(0, 1.3)
    ax.tick_params(axis='x', rotation=15)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "bar_crop_achievement.png")
    fig.savefig(path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def plot_worktype_productivity(df):
    grp = df.groupby("work_type")["productivity"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(grp.index, grp.values, color="seagreen")
    ax.set_title("作業区分別平均生産性 (2024年1月)")
    ax.set_xlabel("平均生産性 (単位/時間)")
    ax.set_ylabel("作業区分")
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "bar_worktype_productivity.png")
    fig.savefig(path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def plot_staff_productivity(df):
    grp = df.groupby("staff_id")["productivity"].mean().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(grp.index[::-1], grp.values[::-1], color="coral")
    ax.set_title("スタッフ別平均生産性 上位10名 (2024年1月)")
    ax.set_xlabel("平均生産性 (単位/時間)")
    ax.set_ylabel("スタッフID")
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "bar_staff_productivity.png")
    fig.savefig(path, dpi=100)
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def main():
    df = load_data()
    print(f"[OK] Loaded {len(df)} rows")
    plot_crop_achievement(df)
    plot_worktype_productivity(df)
    plot_staff_productivity(df)
    print("[OK] All charts saved")


if __name__ == "__main__":
    main()
