# -*- coding: utf-8 -*-
"""
C-58: 可視化スクリプト
output/charts/ に 3枚のグラフを出力
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams['font.family'] = 'MS Gothic'
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_costs_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["record_date"] = pd.to_datetime(df["record_date"])
    return df


def chart_bar_project_variance(df: pd.DataFrame):
    """工事番号別差異率（横棒グラフ、超過=赤/予算内=青）"""
    proj = (
        df.groupby("project_no")
        .agg(
            budget_total=("budget_amount", "sum"),
            actual_total=("actual_amount", "sum"),
        )
        .reset_index()
    )
    proj["variance_rate"] = (proj["actual_total"] - proj["budget_total"]) / proj["budget_total"]
    proj = proj.sort_values("variance_rate", ascending=True)

    colors = ["#e15759" if v > 0 else "#4e79a7" for v in proj["variance_rate"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(proj["project_no"], proj["variance_rate"] * 100, color=colors)

    ax.axvline(x=0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("工事番号別 差異率（超過:赤 / 予算内:青）", fontsize=14, pad=12)
    ax.set_xlabel("差異率 (%)", fontsize=12)
    ax.set_ylabel("工事番号", fontsize=12)

    for bar, val in zip(bars, proj["variance_rate"]):
        width = bar.get_width()
        offset = 0.3 if width >= 0 else -0.3
        ax.text(width + offset, bar.get_y() + bar.get_height() / 2,
                f"{val:.1%}", va="center", fontsize=9)

    plt.tight_layout()
    out = CHARTS_DIR / "bar_project_variance.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_worktype_actual(df: pd.DataFrame):
    """工種別実績額合計（縦棒グラフ）"""
    wt = (
        df.groupby("work_type")["actual_amount"]
        .sum()
        .reset_index()
        .sort_values("actual_amount", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(wt["work_type"], wt["actual_amount"] / 1_000_000, color="#59a14f")

    ax.set_title("工種別 実績額合計", fontsize=14, pad=12)
    ax.set_xlabel("工種", fontsize=12)
    ax.set_ylabel("実績額合計 (百万円)", fontsize=12)
    ax.tick_params(axis="x", rotation=15)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.02,
                f"{height:.1f}M", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    out = CHARTS_DIR / "bar_worktype_actual.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_category_budget_actual(df: pd.DataFrame):
    """費目別予算vs実績（グループ縦棒グラフ）"""
    cat = (
        df.groupby("cost_category")
        .agg(
            budget_total=("budget_amount", "sum"),
            actual_total=("actual_amount", "sum"),
        )
        .reset_index()
        .sort_values("actual_total", ascending=False)
    )

    x = range(len(cat))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 6))
    bars1 = ax.bar([i - width / 2 for i in x], cat["budget_total"] / 1_000_000,
                   width, label="予算額", color="#4e79a7")
    bars2 = ax.bar([i + width / 2 for i in x], cat["actual_total"] / 1_000_000,
                   width, label="実績額", color="#f28e2b")

    ax.set_title("費目別 予算 vs 実績", fontsize=14, pad=12)
    ax.set_xlabel("費目", fontsize=12)
    ax.set_ylabel("金額 (百万円)", fontsize=12)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cat["cost_category"])
    ax.legend()

    for bar in list(bars1) + list(bars2):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.02,
                f"{height:.1f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    out = CHARTS_DIR / "bar_category_budget_actual.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def main():
    df = load_data()
    chart_bar_project_variance(df)
    chart_bar_worktype_actual(df)
    chart_bar_category_budget_actual(df)
    print(f"\nグラフ生成完了: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
