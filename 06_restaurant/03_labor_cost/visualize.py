"""
C-20: 可視化スクリプト
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

CSV_PATH = OUTPUT_DIR / "cleaned_labor_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["work_date"] = pd.to_datetime(df["work_date"])
    return df


def chart_bar_store_labor_cost(df: pd.DataFrame):
    """店舗別人件費（雇用区分別積み上げ棒グラフ）"""
    pivot = (
        df.groupby(["store_id", "employment_type"])["total_wage"]
        .sum()
        .unstack(fill_value=0)
    )

    emp_order = ["アルバイト", "パート", "社員"]
    emp_order = [e for e in emp_order if e in pivot.columns]
    pivot = pivot[emp_order]

    colors = ["#4e79a7", "#f28e2b", "#e15759"]
    ax = pivot.plot(kind="bar", stacked=True, figsize=(10, 6),
                    color=colors[:len(emp_order)])
    ax.set_title("店舗別 人件費（雇用区分別積み上げ）", fontsize=14, pad=12)
    ax.set_xlabel("店舗", fontsize=12)
    ax.set_ylabel("人件費 (円)", fontsize=12)
    ax.legend(title="雇用区分", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.tick_params(axis="x", rotation=0)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    plt.tight_layout()
    out = CHARTS_DIR / "bar_store_labor_cost.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_staff_hours_top10(df: pd.DataFrame):
    """労働時間上位10名（横棒グラフ）"""
    top10 = (
        df.groupby(["staff_id", "name"])["work_hours"]
        .sum()
        .reset_index()
        .sort_values("work_hours", ascending=False)
        .head(10)
    )
    top10["label"] = top10["name"] + " (" + top10["staff_id"] + ")"
    top10 = top10.sort_values("work_hours", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(top10["label"], top10["work_hours"], color="#59a14f")
    ax.set_title("月間労働時間ランキング 上位10名", fontsize=14, pad=12)
    ax.set_xlabel("労働時間 (h)", fontsize=12)
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{width:.1f}h", va="center", fontsize=9)

    plt.tight_layout()
    out = CHARTS_DIR / "bar_staff_hours_top10.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_pie_employment_cost_share(df: pd.DataFrame):
    """雇用区分別人件費構成比（円グラフ）"""
    emp_cost = df.groupby("employment_type")["total_wage"].sum()
    emp_order = ["アルバイト", "パート", "社員"]
    emp_order = [e for e in emp_order if e in emp_cost.index]
    emp_cost = emp_cost[emp_order]

    colors = ["#4e79a7", "#f28e2b", "#e15759"]
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        emp_cost,
        labels=emp_order,
        autopct="%1.1f%%",
        colors=colors[:len(emp_order)],
        startangle=140,
        pctdistance=0.8,
    )
    for t in autotexts:
        t.set_fontsize(11)
    ax.set_title("雇用区分別 人件費構成比", fontsize=14, pad=12)

    plt.tight_layout()
    out = CHARTS_DIR / "pie_employment_cost_share.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def main():
    df = load_data()
    chart_bar_store_labor_cost(df)
    chart_bar_staff_hours_top10(df)
    chart_pie_employment_cost_share(df)
    print(f"\nグラフ生成完了: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
