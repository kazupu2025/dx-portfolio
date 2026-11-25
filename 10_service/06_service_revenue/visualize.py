# -*- coding: utf-8 -*-
"""
C-45: サービス別売上・原価レポート
可視化スクリプト
"""

import os
import random
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'MS Gothic'

random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

SRC = os.path.join(OUTPUT_DIR, "cleaned_revenue_202401.csv")


def main():
    df = pd.read_csv(SRC, encoding="utf-8-sig")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df["gross_profit"] = pd.to_numeric(df["gross_profit"], errors="coerce")
    df["gross_margin"] = pd.to_numeric(df["gross_margin"], errors="coerce")

    # サービス別集計
    svc = df.groupby("service_name").agg(
        revenue=("revenue", "sum"),
        cost=("cost", "sum"),
        gross_profit=("gross_profit", "sum"),
        gross_margin=("gross_margin", "mean"),
    ).reset_index().sort_values("revenue", ascending=False)

    # カテゴリ別集計
    cat = df.groupby("category").agg(
        gross_profit=("gross_profit", "sum"),
    ).reset_index()

    # --- 1. サービス別売上・原価積み上げ棒グラフ ---
    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(svc))
    ax.bar(x, svc["revenue"] / 1e6, label="売上", color="#4C72B0", alpha=0.85)
    ax.bar(x, svc["cost"] / 1e6, label="原価", color="#DD8452", alpha=0.85)
    ax.set_xticks(list(x))
    ax.set_xticklabels(svc["service_name"].tolist(), rotation=30, ha="right")
    ax.set_ylabel("金額 (百万円)")
    ax.set_title("サービス別 売上・原価")
    ax.legend()
    plt.tight_layout()
    out1 = os.path.join(CHARTS_DIR, "bar_service_revenue.png")
    plt.savefig(out1, dpi=100)
    plt.close()
    print(f"[OK] {out1}")

    # --- 2. サービス別粗利率横棒 (赤字は赤色) ---
    svc_margin = svc.sort_values("gross_margin", ascending=True)
    colors = ["#D62728" if m < 0 else "#2CA02C" for m in svc_margin["gross_margin"]]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(svc_margin["service_name"].tolist(), svc_margin["gross_margin"] * 100, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("粗利率 (%)")
    ax.set_title("サービス別 粗利率")
    plt.tight_layout()
    out2 = os.path.join(CHARTS_DIR, "bar_service_margin.png")
    plt.savefig(out2, dpi=100)
    plt.close()
    print(f"[OK] {out2}")

    # --- 3. カテゴリ別粗利合計縦棒 ---
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(cat["category"].tolist(), cat["gross_profit"] / 1e6, color=["#9467BD", "#8C564B", "#E377C2"])
    ax.set_ylabel("粗利合計 (百万円)")
    ax.set_title("カテゴリ別 粗利合計")
    plt.tight_layout()
    out3 = os.path.join(CHARTS_DIR, "bar_category_profit.png")
    plt.savefig(out3, dpi=100)
    plt.close()
    print(f"[OK] {out3}")

    print("[OK] Visualization complete.")


if __name__ == "__main__":
    main()
