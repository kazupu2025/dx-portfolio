"""
C-23: 可視化スクリプト
output/charts/ に 3枚以上のグラフを出力
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_maintenance_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["occurrence_date"] = pd.to_datetime(df["occurrence_date"])
    return df


def chart_bar_area_cost(df: pd.DataFrame):
    """エリア別コスト（費用区分別積み上げ棒グラフ）"""
    pivot = (
        df.groupby(["area", "cost_category"])["cost_amount"]
        .sum()
        .unstack(fill_value=0)
    )

    cat_order = ["管理費", "定期修繕", "緊急修繕", "清掃費", "設備点検"]
    cat_order = [c for c in cat_order if c in pivot.columns]
    pivot = pivot[cat_order]

    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"]
    ax = pivot.plot(kind="bar", stacked=True, figsize=(12, 7),
                    color=colors[:len(cat_order)])
    ax.set_title("エリア別 コスト（費用区分別積み上げ）", fontsize=14, pad=12)
    ax.set_xlabel("エリア", fontsize=12)
    ax.set_ylabel("コスト (円)", fontsize=12)
    ax.legend(title="費用区分", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.tick_params(axis="x", rotation=0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    plt.tight_layout()
    out = CHARTS_DIR / "bar_area_cost.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_property_cost_top10(df: pd.DataFrame):
    """コスト上位10物件（横棒グラフ）"""
    top10 = (
        df.groupby(["property_id", "property_name"])["cost_amount"]
        .sum()
        .reset_index()
        .sort_values("cost_amount", ascending=False)
        .head(10)
    )
    top10["label"] = top10["property_name"] + " (" + top10["property_id"] + ")"
    top10 = top10.sort_values("cost_amount", ascending=True)

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(top10["label"], top10["cost_amount"], color="#4e79a7")
    ax.set_title("コスト上位10物件", fontsize=14, pad=12)
    ax.set_xlabel("コスト (円)", fontsize=12)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 5000, bar.get_y() + bar.get_height() / 2,
                f"{width:,.0f}", va="center", fontsize=8)

    plt.tight_layout()
    out = CHARTS_DIR / "bar_property_cost_top10.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_pie_cost_category(df: pd.DataFrame):
    """費用区分別コスト構成比（円グラフ）"""
    cat_cost = df.groupby("cost_category")["cost_amount"].sum()
    cat_order = ["管理費", "定期修繕", "緊急修繕", "清掃費", "設備点検"]
    cat_order = [c for c in cat_order if c in cat_cost.index]
    cat_cost = cat_cost[cat_order]

    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"]
    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts, autotexts = ax.pie(
        cat_cost,
        labels=cat_order,
        autopct="%1.1f%%",
        colors=colors[:len(cat_order)],
        startangle=140,
        pctdistance=0.8,
    )
    for t in autotexts:
        t.set_fontsize(11)
    ax.set_title("費用区分別 コスト構成比", fontsize=14, pad=12)

    plt.tight_layout()
    out = CHARTS_DIR / "pie_cost_category.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def main():
    df = load_data()
    chart_bar_area_cost(df)
    chart_bar_property_cost_top10(df)
    chart_pie_cost_category(df)
    print(f"\nグラフ生成完了: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
