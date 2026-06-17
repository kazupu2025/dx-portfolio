import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_enrollment_202401.csv", encoding="utf-8-sig")
for col in ["study_hours", "test_score", "satisfaction", "is_completed"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ------- 1. 講座別修了率の棒グラフ -------
course_comp = df.groupby("course_name").agg(
    総受講数=("enroll_no", "count"),
    修了数=("is_completed", "sum"),
).reset_index()
course_comp["修了率(%)"] = (course_comp["修了数"] / course_comp["総受講数"] * 100).round(1)
course_comp = course_comp.sort_values("修了率(%)", ascending=False)

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(
    course_comp["course_name"].values,
    course_comp["修了率(%)"].values,
    color="#2563eb",
)
ax.set_title("講座別 修了率（2024年1月）", fontsize=14)
ax.set_ylabel("修了率 (%)")
ax.set_ylim(0, 110)
for bar in bars:
    h = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2, h + 1.0,
        f"{h:.1f}%", ha="center", va="bottom", fontsize=10,
    )
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
out1 = CHARTS_DIR / "bar_course_completion.png"
plt.savefig(out1, dpi=150)
plt.close()
print(f"Saved: {out1.name}")

# ------- 2. スコアグレード別件数の棒グラフ -------
if "score_grade" in df.columns:
    grade_counts = df["score_grade"].value_counts()
    # 表示順: 優秀 → 合格 → 不合格
    grade_order = [g for g in ["優秀", "合格", "不合格"] if g in grade_counts.index]
    grade_counts = grade_counts.reindex(grade_order)
    colors = ["#16a34a", "#f59e0b", "#dc2626"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        grade_counts.index,
        grade_counts.values,
        color=colors[: len(grade_counts)],
    )
    ax.set_title("スコアグレード別 件数（2024年1月）", fontsize=14)
    ax.set_ylabel("件数")
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + 1.0,
            f"{int(h)}", ha="center", va="bottom", fontsize=11,
        )
    plt.tight_layout()
    out2 = CHARTS_DIR / "bar_score_grade.png"
    plt.savefig(out2, dpi=150)
    plt.close()
    print(f"Saved: {out2.name}")
else:
    print("score_grade列なし: bar_score_grade.png をスキップ")

# ------- 3. 受講者タイプ別修了率の棒グラフ -------
if "learner_type" in df.columns:
    lt_comp = df.groupby("learner_type").agg(
        総受講数=("enroll_no", "count"),
        修了数=("is_completed", "sum"),
    ).reset_index()
    lt_comp["修了率(%)"] = (lt_comp["修了数"] / lt_comp["総受講数"] * 100).round(1)
    lt_comp = lt_comp.sort_values("修了率(%)", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        lt_comp["learner_type"].values,
        lt_comp["修了率(%)"].values,
        color="#7c3aed",
    )
    ax.set_title("受講者タイプ別 修了率（2024年1月）", fontsize=14)
    ax.set_ylabel("修了率 (%)")
    ax.set_ylim(0, 110)
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + 1.0,
            f"{h:.1f}%", ha="center", va="bottom", fontsize=11,
        )
    plt.tight_layout()
    out3 = CHARTS_DIR / "bar_learnertype_completion.png"
    plt.savefig(out3, dpi=150)
    plt.close()
    print(f"Saved: {out3.name}")
else:
    print("learner_type列なし: bar_learnertype_completion.png をスキップ")

print("グラフ生成完了（3枚）")
