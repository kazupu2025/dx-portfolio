"""
C-22 ドライバー勤怠・拘束時間管理パイプライン
可視化スクリプト
output/charts/ に3枚以上のグラフを出力する
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams['font.family'] = 'MS Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_driver_202401.csv"
SUMMARY_CSV_PATH = OUTPUT_DIR / "driver_summary_202401.csv"


def load_data() -> tuple:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["confinement_over_flag"] = df["confinement_over_flag"].astype(bool)
    df["work_over_flag"] = df["work_over_flag"].astype(bool)
    summary = pd.read_csv(SUMMARY_CSV_PATH, encoding="utf-8-sig")
    return df, summary


def plot_bar_office_violation_rate(df: pd.DataFrame):
    """営業所別違反率 棒グラフ"""
    grp = df.groupby("office").agg(
        total=("driver_id", "count"),
        violations=("violation_flag", lambda x: (x == "違反").sum()),
    ).reset_index()
    grp["rate"] = grp["violations"] / grp["total"] * 100
    grp = grp.sort_values("rate", ascending=True)

    overall_rate = (df["violation_flag"] == "違反").mean() * 100

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#e74c3c" if v > overall_rate else "#2ecc71" for v in grp["rate"]]
    bars = ax.barh(grp["office"], grp["rate"], color=colors)
    ax.axvline(overall_rate, color="navy", linestyle="--", linewidth=1.5,
               label=f"全体平均: {overall_rate:.1f}%")
    ax.set_xlabel("違反率 (%)", fontsize=12)
    ax.set_title("営業所別 拘束時間違反率", fontsize=14, fontweight="bold")
    for bar, val in zip(bars, grp["rate"]):
        ax.text(val + 0.2, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=10)
    ax.legend(fontsize=10)
    plt.tight_layout()
    out = CHARTS_DIR / "bar_office_violation_rate.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")


def plot_bar_driver_violation_top10(summary: pd.DataFrame):
    """違反件数上位10ドライバー 棒グラフ"""
    top10 = summary.head(10).sort_values("violation_count", ascending=True)
    labels = top10["name"].tolist()
    values = top10["violation_count"].tolist()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(labels)))
    bars = ax.barh(labels, values, color=colors)
    ax.set_xlabel("違反件数", fontsize=12)
    ax.set_title("違反件数 上位10ドライバー", fontsize=14, fontweight="bold")
    for bar, val in zip(bars, values):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                str(int(val)), va="center", fontsize=10)
    plt.tight_layout()
    out = CHARTS_DIR / "bar_driver_violation_top10.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")


def plot_pie_operation_distance(df: pd.DataFrame):
    """運行区分別走行距離構成比 円グラフ"""
    grp = df.groupby("operation_type")["distance_km"].sum().reset_index()
    grp.columns = ["operation_type", "total_distance"]

    colors = ["#e67e22", "#3498db", "#2ecc71"]
    explode = [0.03] * len(grp)

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        grp["total_distance"],
        labels=grp["operation_type"],
        colors=colors[:len(grp)],
        autopct="%1.1f%%",
        startangle=140,
        explode=explode[:len(grp)],
        textprops={"fontsize": 13},
    )
    for at in autotexts:
        at.set_fontsize(12)
        at.set_fontweight("bold")

    ax.set_title("運行区分別 走行距離構成比", fontsize=14, fontweight="bold")
    legend_labels = [
        f"{row['operation_type']}: {row['total_distance']:,.1f}km"
        for _, row in grp.iterrows()
    ]
    ax.legend(legend_labels, loc="lower left", fontsize=10)

    plt.tight_layout()
    out = CHARTS_DIR / "pie_operation_distance.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] {out}")


def main():
    print("[INFO] データ読み込み...")
    df, summary = load_data()
    print(f"  {len(df)} rows")

    print("[INFO] グラフ生成中...")
    plot_bar_office_violation_rate(df)
    plot_bar_driver_violation_top10(summary)
    plot_pie_operation_distance(df)

    charts = list(CHARTS_DIR.glob("*.png"))
    print(f"\n[OK] 合計 {len(charts)} 枚のグラフを生成しました: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
