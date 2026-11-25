# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
可視化スクリプト: 学科別・選考方法別・地域別グラフを生成
"""

import os
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_applications_202401.csv")

os.makedirs(CHARTS_DIR, exist_ok=True)


def run_visualize():
    if not os.path.exists(CLEANED_FILE):
        print(f"[FAIL] クレンジング済みファイルが見つかりません: {CLEANED_FILE}")
        return

    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    print(f"[OK] データ読み込み: {len(df)} 行")

    # --- 1. 学科別合格率（縦棒） ---
    dept_group = df.groupby("department").agg(
        申込数=("app_id", "count"),
        合格数=("is_enrolled", "sum"),
    ).reset_index()
    dept_group["合格率(%)"] = (dept_group["合格数"] / dept_group["申込数"] * 100).round(1)
    dept_group = dept_group.sort_values("合格率(%)", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(dept_group["department"], dept_group["合格率(%)"], color="#4C72B0")
    ax.set_title("学科別合格率")
    ax.set_xlabel("学科")
    ax.set_ylabel("合格率(%)")
    ax.set_ylim(0, 100)
    for i, (_, row) in enumerate(dept_group.iterrows()):
        ax.text(i, row["合格率(%)"] + 1, f"{row['合格率(%)']:.1f}%", ha="center", fontsize=10)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "bar_dept_enrollment.png")
    plt.savefig(out_path, dpi=100)
    plt.close()
    print(f"[OK] 学科別合格率グラフ: {out_path}")

    # --- 2. 選考方法別合格率（横棒） ---
    sel_group = df.groupby("selection_method").agg(
        申込数=("app_id", "count"),
        合格数=("is_enrolled", "sum"),
    ).reset_index()
    sel_group["合格率(%)"] = (sel_group["合格数"] / sel_group["申込数"] * 100).round(1)
    sel_group = sel_group.sort_values("合格率(%)", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(sel_group["selection_method"], sel_group["合格率(%)"], color="#DD8452")
    ax.set_title("選考方法別合格率")
    ax.set_xlabel("合格率(%)")
    ax.set_ylabel("選考方法")
    ax.set_xlim(0, 100)
    for i, (_, row) in enumerate(sel_group.iterrows()):
        ax.text(row["合格率(%)"] + 1, i, f"{row['合格率(%)']:.1f}%", va="center", fontsize=10)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "bar_method_enrollment.png")
    plt.savefig(out_path, dpi=100)
    plt.close()
    print(f"[OK] 選考方法別合格率グラフ: {out_path}")

    # --- 3. 地域別申込数（縦棒） ---
    region_group = df.groupby("region").agg(
        申込数=("app_id", "count"),
    ).reset_index()
    region_group = region_group.sort_values("申込数", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(region_group["region"], region_group["申込数"], color="#55A868")
    ax.set_title("地域別申込数")
    ax.set_xlabel("地域")
    ax.set_ylabel("申込数")
    for i, (_, row) in enumerate(region_group.iterrows()):
        ax.text(i, row["申込数"] + 0.5, str(int(row["申込数"])), ha="center", fontsize=10)
    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "bar_region_count.png")
    plt.savefig(out_path, dpi=100)
    plt.close()
    print(f"[OK] 地域別申込数グラフ: {out_path}")

    print("[OK] グラフ生成完了")


if __name__ == "__main__":
    run_visualize()
