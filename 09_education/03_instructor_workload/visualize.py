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

df = pd.read_csv(OUTPUT_DIR / "cleaned_instructor_202401.csv", encoding="utf-8-sig")
for col in ["lesson_count", "lesson_hours", "lesson_cost", "attendee_count", "hourly_rate"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ------- 1. コマ数上位10講師（横棒グラフ）-------
inst_lessons = (
    df.groupby(["instructor_id", "name"])["lesson_count"]
    .sum()
    .reset_index()
    .sort_values("lesson_count", ascending=False)
    .head(10)
)
inst_lessons["label"] = inst_lessons["name"] + "\n(" + inst_lessons["instructor_id"] + ")"

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(
    inst_lessons["label"].values[::-1],
    inst_lessons["lesson_count"].values[::-1],
    color="#2563eb",
)
ax.set_title("コマ数上位10講師（2024年1月）", fontsize=14)
ax.set_xlabel("月間コマ数")
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{int(w)}", va="center", fontsize=9)
plt.tight_layout()
out1 = CHARTS_DIR / "bar_instructor_lessons_top10.png"
plt.savefig(out1, dpi=150)
plt.close()
print(f"Saved: {out1.name}")

# ------- 2. 専門分野別コスト（棒グラフ）-------
specialty_cost = df.groupby("specialty")["lesson_cost"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(specialty_cost.index, specialty_cost.values, color="#16a34a")
ax.set_title("専門分野別 講師コスト合計（2024年1月）", fontsize=14)
ax.set_ylabel("講師コスト（円）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=8)
plt.tight_layout()
out2 = CHARTS_DIR / "bar_specialty_cost.png"
plt.savefig(out2, dpi=150)
plt.close()
print(f"Saved: {out2.name}")

# ------- 3. 雇用区分別コスト構成比（円グラフ）-------
emp_cost = df.groupby("employment_type")["lesson_cost"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(8, 6))
colors = ["#2563eb", "#f97316", "#16a34a", "#dc2626", "#7c3aed"]
wedges, texts, autotexts = ax.pie(
    emp_cost.values,
    labels=emp_cost.index,
    autopct="%1.1f%%",
    startangle=90,
    colors=colors[: len(emp_cost)],
    pctdistance=0.8,
)
for text in texts:
    text.set_fontsize(11)
for autotext in autotexts:
    autotext.set_fontsize(10)
ax.set_title("雇用区分別 講師コスト構成比（2024年1月）", fontsize=14)
plt.tight_layout()
out3 = CHARTS_DIR / "pie_employment_cost_share.png"
plt.savefig(out3, dpi=150)
plt.close()
print(f"Saved: {out3.name}")

print("グラフ生成完了（3枚）")
