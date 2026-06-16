# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
可視化スクリプト: 3枚のグラフを output/charts/ に保存する
日本語フォント: MS Gothic
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_medicine_202401.csv"


def load_data() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def plot_ward_alert(df: pd.DataFrame):
    """病棟別欠品・警告品目数の積み上げ棒グラフ"""
    alert_df = df[df["alert_level"].isin(["欠品", "警告"])].copy()
    ward_alert = (
        alert_df.groupby(["ward", "alert_level"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["欠品", "警告"]:
        if col not in ward_alert.columns:
            ward_alert[col] = 0
    ward_alert = ward_alert.sort_values("欠品", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    wards = ward_alert["ward"].tolist()
    x = range(len(wards))

    bars1 = ax.bar(x, ward_alert["欠品"].tolist(), label="欠品", color="#E74C3C")
    bars2 = ax.bar(x, ward_alert["警告"].tolist(),
                   bottom=ward_alert["欠品"].tolist(), label="警告", color="#F39C12")

    ax.set_xticks(list(x))
    ax.set_xticklabels(wards, fontsize=11)
    ax.set_ylabel("品目数", fontsize=11)
    ax.set_title("病棟別 欠品・警告品目数", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_ward_alert.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] 保存: {out_path}")


def plot_stockout_risk_top10(df: pd.DataFrame):
    """欠品リスク上位10品目（days_until_stockout）の横棒グラフ"""
    risk_df = df[df["days_until_stockout"].notna()].copy()
    top10 = (
        risk_df.sort_values("days_until_stockout")
        .drop_duplicates("med_code")
        .head(10)
    )

    labels = [f"{row['med_name']}({row['med_code']})" for _, row in top10.iterrows()]
    values = top10["days_until_stockout"].tolist()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#E74C3C" if v < 1 else ("#F39C12" if v < 3 else "#3498DB") for v in values]
    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1])

    ax.set_xlabel("残日数 (days)", fontsize=11)
    ax.set_title("欠品リスク上位10品目（在庫残日数）", fontsize=13, fontweight="bold")
    ax.axvline(x=3, color="orange", linestyle="--", linewidth=1.2, label="警告閾値 (3日)")
    ax.axvline(x=1, color="red", linestyle="--", linewidth=1.2, label="欠品閾値 (1日)")
    ax.legend(fontsize=9)
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    out_path = CHARTS_DIR / "bar_stockout_risk_top10.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] 保存: {out_path}")


def plot_category_stock_value(df: pd.DataFrame):
    """カテゴリ別在庫金額の円グラフ"""
    cat_val = df.groupby("category")["stock_value"].sum().sort_values(ascending=False)

    colors = ["#3498DB", "#2ECC71", "#E74C3C", "#F39C12", "#9B59B6"]
    fig, ax = plt.subplots(figsize=(8, 7))
    wedges, texts, autotexts = ax.pie(
        cat_val.values,
        labels=cat_val.index.tolist(),
        autopct="%1.1f%%",
        colors=colors[: len(cat_val)],
        startangle=140,
        pctdistance=0.8,
    )
    for text in texts:
        text.set_fontsize(11)
    for autotext in autotexts:
        autotext.set_fontsize(10)

    ax.set_title("カテゴリ別在庫金額構成", fontsize=13, fontweight="bold")

    plt.tight_layout()
    out_path = CHARTS_DIR / "pie_category_stock_value.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] 保存: {out_path}")


def main():
    print("[INFO] 可視化開始...")
    df = load_data()
    print(f"[INFO] データ読み込み: {len(df)} 件")

    plot_ward_alert(df)
    plot_stockout_risk_top10(df)
    plot_category_stock_value(df)

    print("[OK] 全グラフ生成完了")


if __name__ == "__main__":
    main()
