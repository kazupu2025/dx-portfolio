"""
C-21: サービス別売上・原価分析 可視化
output/charts/ に3枚以上のPNGを生成する
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE = Path(__file__).parent
CSV_PATH = BASE / "output" / "cleaned_revenue_cost_202401.csv"
CHARTS_DIR = BASE / "output" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def load():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def chart1_bar_service_margin(df):
    """サービス別 粗利率・営業利益率 grouped bar"""
    grp = df.groupby("service_type").agg(
        粗利合計=("gross_profit", "sum"),
        営業利益合計=("operating_profit", "sum"),
        売上合計=("revenue", "sum"),
    ).reset_index()
    grp["粗利率"] = grp["粗利合計"] / grp["売上合計"].replace(0, np.nan) * 100
    grp["営業利益率"] = grp["営業利益合計"] / grp["売上合計"].replace(0, np.nan) * 100
    grp = grp.sort_values("粗利率", ascending=False)

    x = np.arange(len(grp))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width / 2, grp["粗利率"], width, label="粗利率(%)", color="#4472C4")
    bars2 = ax.bar(x + width / 2, grp["営業利益率"], width, label="営業利益率(%)", color="#ED7D31")

    ax.set_title("サービス別 粗利率・営業利益率", fontsize=14, fontweight="bold")
    ax.set_xlabel("サービス区分")
    ax.set_ylabel("利益率 (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(grp["service_type"], rotation=20, ha="right")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.legend()
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    out = CHARTS_DIR / "bar_service_margin.png"
    plt.savefig(out, dpi=100)
    plt.close()
    print(f"[OK] {out}")


def chart2_bar_dept_revenue(df):
    """部門別売上（棒グラフ）"""
    grp = df.groupby("department").agg(
        売上合計=("revenue", "sum"),
        粗利合計=("gross_profit", "sum"),
    ).reset_index()
    grp = grp.sort_values("売上合計", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#4472C4", "#ED7D31", "#A9D18E", "#FFC000"][:len(grp)]
    bars = ax.bar(grp["department"], grp["売上合計"] / 1_000_000, color=colors)

    ax.set_title("部門別 売上合計", fontsize=14, fontweight="bold")
    ax.set_xlabel("担当部門")
    ax.set_ylabel("売上合計 (百万円)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"¥{x:.1f}M"))
    ax.grid(axis="y", alpha=0.3)

    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.02,
                f"¥{h:.1f}M", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    out = CHARTS_DIR / "bar_dept_revenue.png"
    plt.savefig(out, dpi=100)
    plt.close()
    print(f"[OK] {out}")


def chart3_pie_service_revenue(df):
    """サービス別売上構成比（円グラフ）"""
    grp = df.groupby("service_type")["revenue"].sum().reset_index()
    grp = grp.sort_values("revenue", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#4472C4", "#ED7D31", "#A9D18E", "#FFC000", "#FF6B6B"]

    wedges, texts, autotexts = ax.pie(
        grp["revenue"],
        labels=grp["service_type"],
        autopct="%1.1f%%",
        colors=colors[:len(grp)],
        startangle=140,
        pctdistance=0.8,
    )
    for t in autotexts:
        t.set_fontsize(9)

    ax.set_title("サービス別 売上構成比", fontsize=14, fontweight="bold")

    total = grp["revenue"].sum()
    ax.text(0, -1.3, f"売上合計: ¥{total:,.0f}", ha="center", fontsize=10)

    plt.tight_layout()
    out = CHARTS_DIR / "pie_service_revenue_share.png"
    plt.savefig(out, dpi=100)
    plt.close()
    print(f"[OK] {out}")


def main():
    print("=== 可視化開始 ===")
    df = load()
    chart1_bar_service_margin(df)
    chart2_bar_dept_revenue(df)
    chart3_pie_service_revenue(df)
    print("\n=== 可視化完了 (3枚) ===")


if __name__ == "__main__":
    main()
