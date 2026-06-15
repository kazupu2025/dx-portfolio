"""
B-14 可視化 (3チャート)
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import yaml
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT = Path(__file__).parent
CHARTS = OUT / "charts"
CSV = OUT / "cleaned_rental_202401.csv"

# Japanese font setup
def get_jp_font():
    for fname in fm.findSystemFonts():
        if any(k in fname.lower() for k in ["msgothic", "meiryo", "yugothic", "noto"]):
            return fm.FontProperties(fname=fname)
    return None

jp_font = get_jp_font()

def set_jp(ax, title=None, xlabel=None, ylabel=None):
    if jp_font:
        if title: ax.set_title(title, fontproperties=jp_font, fontsize=12)
        if xlabel: ax.set_xlabel(xlabel, fontproperties=jp_font)
        if ylabel: ax.set_ylabel(ylabel, fontproperties=jp_font)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(jp_font)
    else:
        if title: ax.set_title(title, fontsize=12)
        if xlabel: ax.set_xlabel(xlabel)
        if ylabel: ax.set_ylabel(ylabel)

def load_cfg():
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    cfg = load_cfg()
    vacancy_threshold = cfg.get("vacancy_alert_threshold", 0.20)

    df = pd.read_csv(CSV, encoding="utf-8-sig")
    for col in ["rent", "management_fee", "management_cost", "repair_cost", "monthly_revenue", "total_cost", "net_income"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["is_vacant"] = pd.to_numeric(df["is_vacant"], errors="coerce").fillna(0)

    # Chart 1: エリア別空室率棒グラフ
    area_grp = df.groupby("area").agg(
        total=("property_id", "count"),
        vacant=("is_vacant", "sum"),
        total_revenue=("monthly_revenue", "sum"),
    ).reset_index()
    area_grp["vacancy_rate"] = area_grp["vacant"] / area_grp["total"]
    area_grp = area_grp.sort_values("vacancy_rate", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#e74c3c" if r > vacancy_threshold else "#3498db" for r in area_grp["vacancy_rate"]]
    bars = ax.bar(area_grp["area"], area_grp["vacancy_rate"] * 100, color=colors, edgecolor="white", linewidth=0.5)
    ax.axhline(y=vacancy_threshold * 100, color="red", linestyle="--", linewidth=1.5, label=f"Alert: {vacancy_threshold*100:.0f}%")
    for bar, val in zip(bars, area_grp["vacancy_rate"] * 100):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, f"{val:.1f}%",
                ha="center", va="bottom", fontsize=9,
                fontproperties=jp_font if jp_font else None)
    ax.set_ylim(0, max(area_grp["vacancy_rate"].max() * 100 + 5, 30))
    set_jp(ax, title="エリア別空室率 (2024年1月)", xlabel="エリア", ylabel="空室率 (%)")
    ax.legend(prop=jp_font if jp_font else None)
    plt.tight_layout()
    plt.savefig(CHARTS / "bar_area_vacancy_rate.png", dpi=120, bbox_inches="tight")
    plt.close()
    print("Saved bar_area_vacancy_rate.png")

    # Chart 2: 物件タイプ別平均純収益 (twinx: 棒=純収益, 線=空室率)
    type_grp = df.groupby("property_type").agg(
        total=("property_id", "count"),
        vacant=("is_vacant", "sum"),
        avg_net_income=("net_income", "mean"),
    ).reset_index()
    type_grp["vacancy_rate_pct"] = type_grp["vacant"] / type_grp["total"] * 100
    type_order = ["1K", "1DK", "1LDK", "2LDK", "3LDK"]
    type_grp["property_type"] = pd.Categorical(type_grp["property_type"], categories=type_order, ordered=True)
    type_grp = type_grp.sort_values("property_type")

    fig, ax1 = plt.subplots(figsize=(9, 5))
    x = np.arange(len(type_grp))
    bars = ax1.bar(x, type_grp["avg_net_income"], color="#2ecc71", edgecolor="white", linewidth=0.5, label="平均純収益")
    set_jp(ax1, title="物件タイプ別純収益・空室率", xlabel="物件タイプ", ylabel="平均純収益 (円)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(type_grp["property_type"])

    ax2 = ax1.twinx()
    ax2.plot(x, type_grp["vacancy_rate_pct"], color="#e67e22", marker="o", linewidth=2, label="空室率(%)")
    if jp_font:
        ax2.set_ylabel("空室率 (%)", fontproperties=jp_font)
    else:
        ax2.set_ylabel("空室率 (%)")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, prop=jp_font if jp_font else None, loc="upper left")
    plt.tight_layout()
    plt.savefig(CHARTS / "bar_type_net_income.png", dpi=120, bbox_inches="tight")
    plt.close()
    print("Saved bar_type_net_income.png")

    # Chart 3: エリア別月次収益積み上げ（入居中のみ）
    occupied = df[df["is_vacant"] == 0]
    area_type_rev = occupied.groupby(["area", "property_type"])["monthly_revenue"].sum().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors_stack = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
    area_type_rev.plot(kind="bar", stacked=True, ax=ax, color=colors_stack[:len(area_type_rev.columns)], edgecolor="white", linewidth=0.3)
    set_jp(ax, title="エリア別月次収益（物件タイプ別積み上げ）", xlabel="エリア", ylabel="月次収益 (円)")
    ax.legend(title="物件タイプ", prop=jp_font if jp_font else None,
              title_fontproperties=jp_font if jp_font else None,
              bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(CHARTS / "bar_area_revenue.png", dpi=120, bbox_inches="tight")
    plt.close()
    print("Saved bar_area_revenue.png")

if __name__ == "__main__":
    main()
