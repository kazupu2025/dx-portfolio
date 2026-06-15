"""
visualize.py — 退学リスク可視化（3チャート）
実行: cd 09_education/01_dropout_risk && python output/visualize.py
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import yaml

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "output"
CHARTS = OUT / "charts"

# 日本語フォント設定
def set_japanese_font():
    for font in ["MS Gothic", "Yu Gothic", "Meiryo", "IPAexGothic", "Noto Sans CJK JP"]:
        try:
            fm.findfont(fm.FontProperties(family=font), fallback_to_default=False)
            plt.rcParams["font.family"] = font
            return
        except Exception:
            pass
    plt.rcParams["font.family"] = "DejaVu Sans"

def load_config() -> dict:
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    set_japanese_font()
    config = load_config()

    csv_path = OUT / "cleaned_dropout_202401.csv"
    if not csv_path.exists():
        print("ERROR: cleaned_dropout_202401.csv が存在しません")
        sys.exit(1)

    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # 受講生単位集計
    stu_df = df.groupby("student_id").agg(
        avg_dropout_score=("dropout_risk_score", "mean"),
        risk_category=("risk_category", lambda x: x.mode()[0] if len(x) > 0 else "中リスク"),
        attendance_rate=("attendance_rate", "mean"),
    ).reset_index()

    high_thresh = config["high_risk_threshold"]
    med_thresh  = config["medium_risk_threshold"]

    def classify(score):
        if score < high_thresh: return "高リスク"
        elif score < med_thresh: return "中リスク"
        else: return "低リスク"

    stu_df["student_risk"] = stu_df["avg_dropout_score"].apply(classify)
    low_att_thresh = config["low_attendance_alert"]

    # Chart 1: リスク分類別受講生数（棒グラフ）
    risk_counts = stu_df["student_risk"].value_counts().reindex(["高リスク", "中リスク", "低リスク"], fill_value=0)
    colors = ["#e74c3c", "#e67e22", "#27ae60"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(risk_counts.index, risk_counts.values, color=colors, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, risk_counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, str(val),
                ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.set_title("Risk Category Distribution", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Risk Category", fontsize=11)
    ax.set_ylabel("Student Count", fontsize=11)
    ax.set_ylim(0, risk_counts.max() * 1.15)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top","right"]].set_visible(False)
    plt.tight_layout()
    fig.savefig(CHARTS / "bar_risk_distribution.png", dpi=120, bbox_inches="tight")
    plt.close()
    print("Chart 1: bar_risk_distribution.png")

    # Chart 2: 科目別平均退学リスクスコア棒グラフ + 高リスク率折れ線
    subj_stats = df.groupby("subject").agg(
        avg_score=("dropout_risk_score", "mean"),
        high_risk_rate=("risk_category", lambda x: (x=="高リスク").mean() * 100),
    ).round(1)

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax2 = ax1.twinx()

    bar_colors = ["#3498db" if s >= low_att_thresh else "#e74c3c" for s in subj_stats["avg_score"]]
    bars = ax1.bar(subj_stats.index, subj_stats["avg_score"], color=bar_colors, alpha=0.8, label="Avg Score")
    ax1.axhline(y=high_thresh, color="red", linestyle="--", linewidth=1.5, alpha=0.7, label=f"High Risk Threshold({high_thresh})")
    ax2.plot(subj_stats.index, subj_stats["high_risk_rate"], color="#e74c3c", marker="o",
             linewidth=2, markersize=7, label="High Risk Rate(%)")

    ax1.set_title("Subject-wise Average Dropout Risk Score", fontsize=13, fontweight="bold", pad=15)
    ax1.set_xlabel("Subject", fontsize=11)
    ax1.set_ylabel("Avg Dropout Risk Score", fontsize=11)
    ax2.set_ylabel("High Risk Rate(%)", fontsize=11, color="#e74c3c")
    ax2.tick_params(axis="y", labelcolor="#e74c3c")
    ax1.set_ylim(0, 110)
    ax2.set_ylim(0, 60)
    ax1.grid(axis="y", alpha=0.3)
    ax1.spines[["top","right"]].set_visible(False)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)
    plt.tight_layout()
    fig.savefig(CHARTS / "bar_subject_avg_score.png", dpi=120, bbox_inches="tight")
    plt.close()
    print("Chart 2: bar_subject_avg_score.png")

    # Chart 3: 散布図（出席率 vs 退学リスクスコア）
    color_map = {"高リスク": "#e74c3c", "中リスク": "#e67e22", "低リスク": "#3498db"}

    fig, ax = plt.subplots(figsize=(9, 6))
    for risk, group in stu_df.groupby("student_risk"):
        ax.scatter(group["attendance_rate"], group["avg_dropout_score"],
                   c=color_map.get(risk, "gray"), alpha=0.6, s=40, label=risk)

    ax.axvline(x=low_att_thresh, color="red", linestyle="--", linewidth=1.5,
               alpha=0.8, label=f"Low Attendance Threshold({low_att_thresh:.0f}%)")
    ax.axhline(y=high_thresh, color="#c0392b", linestyle=":", linewidth=1.5,
               alpha=0.7, label=f"High Risk Threshold({high_thresh})")

    ax.set_title("Attendance Rate vs Dropout Risk Score", fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("Avg Attendance Rate(%)", fontsize=11)
    ax.set_ylabel("Avg Dropout Risk Score (higher = safer)", fontsize=11)
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(alpha=0.3)
    ax.spines[["top","right"]].set_visible(False)
    plt.tight_layout()
    fig.savefig(CHARTS / "scatter_attendance_score.png", dpi=120, bbox_inches="tight")
    plt.close()
    print("Chart 3: scatter_attendance_score.png")

    print("visualize.py 完了")

if __name__ == "__main__":
    main()
