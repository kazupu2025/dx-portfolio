"""
C-30: 可視化スクリプト
output/charts/ に 3枚のグラフを出力
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

CSV_PATH = OUTPUT_DIR / "cleaned_labor_cost_202401.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def chart_bar_dept_variance(df: pd.DataFrame):
    """部門別予実差異額の棒グラフ（超過=赤、節約=青）"""
    dept_summary = (
        df.groupby("department")
        .agg(variance_total=("variance_amount", "sum"))
        .reset_index()
        .sort_values("variance_total", ascending=False)
    )

    colors = [
        "#e15759" if v > 0 else "#4e79a7"
        for v in dept_summary["variance_total"]
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(dept_summary["department"], dept_summary["variance_total"], color=colors)
    ax.set_title("部門別 予実差異額（超過=赤、節約=青）", fontsize=14, pad=12)
    ax.set_xlabel("部門", fontsize=12)
    ax.set_ylabel("差異額 (円)", fontsize=12)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + (abs(height) * 0.02),
            f"{height:+,.0f}",
            ha="center",
            va="bottom" if height >= 0 else "top",
            fontsize=9,
        )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_dept_variance.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_bar_employment_cost(df: pd.DataFrame):
    """雇用区分別人件費の積み上げ棒グラフ（部門別）"""
    pivot = (
        df.groupby(["department", "employment_type"])["actual_cost"]
        .sum()
        .unstack(fill_value=0)
    )

    emp_order = ["正社員", "契約社員", "パート"]
    emp_order = [e for e in emp_order if e in pivot.columns]
    pivot = pivot[emp_order]

    colors = ["#4e79a7", "#f28e2b", "#59a14f"]
    ax = pivot.plot(kind="bar", stacked=True, figsize=(12, 6),
                    color=colors[:len(emp_order)])
    ax.set_title("雇用区分別 人件費（部門別積み上げ）", fontsize=14, pad=12)
    ax.set_xlabel("部門", fontsize=12)
    ax.set_ylabel("実績人件費 (円)", fontsize=12)
    ax.legend(title="雇用区分", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.tick_params(axis="x", rotation=0)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )

    plt.tight_layout()
    out = CHARTS_DIR / "bar_employment_cost.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def chart_line_monthly_trend(df: pd.DataFrame):
    """月別人件費推移の折れ線グラフ（予算 vs 実績）"""
    trend = (
        df.groupby("year_month")
        .agg(
            budget_total=("budget_cost", "sum"),
            actual_total=("actual_cost", "sum"),
        )
        .reset_index()
        .sort_values("year_month")
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(trend["year_month"], trend["budget_total"],
            marker="o", label="予算", color="#4e79a7", linewidth=2)
    ax.plot(trend["year_month"], trend["actual_total"],
            marker="s", label="実績", color="#e15759", linewidth=2)
    ax.fill_between(
        trend["year_month"],
        trend["budget_total"],
        trend["actual_total"],
        alpha=0.15,
        color="#e15759",
    )
    ax.set_title("月別 人件費推移（予算 vs 実績）", fontsize=14, pad=12)
    ax.set_xlabel("年月", fontsize=12)
    ax.set_ylabel("人件費 (円)", fontsize=12)
    ax.legend(fontsize=11)
    ax.tick_params(axis="x", rotation=30)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )

    plt.tight_layout()
    out = CHARTS_DIR / "line_monthly_trend.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"保存: {out}")


def main():
    df = load_data()
    chart_bar_dept_variance(df)
    chart_bar_employment_cost(df)
    chart_line_monthly_trend(df)
    print(f"\nグラフ生成完了: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
