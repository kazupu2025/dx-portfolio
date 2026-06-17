"""3枚のチャートを output/charts/ に生成"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUTPUT_DIR / "cleaned_worker_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# ── Chart 1: 作業員別生産性上位10人の横棒グラフ ──
worker_agg = df.groupby("worker_id").agg(
    avg_productivity=("productivity", "mean"),
).reset_index().sort_values("avg_productivity", ascending=False).head(10)

fig, ax = plt.subplots(figsize=(9, 6))
colors = ["#2196F3"] * len(worker_agg)
ax.barh(
    worker_agg["worker_id"][::-1],
    worker_agg["avg_productivity"][::-1],
    color=colors[::-1],
)
ax.set_title("作業員別生産性ランキング（上位10名）")
ax.set_xlabel("平均生産性（個/時）")
ax.set_ylabel("作業員ID")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_worker_productivity_top10.png", dpi=150)
plt.close()
print("bar_worker_productivity_top10.png 出力完了")

# ── Chart 2: ライン別不良率の棒グラフ ──
line_agg = df.groupby("line").agg(
    avg_defect_rate=("defect_rate", "mean"),
).reset_index().sort_values("avg_defect_rate", ascending=False)

fig, ax = plt.subplots(figsize=(7, 5))
bar_colors = ["#F44336", "#FF9800", "#FFC107", "#4CAF50"]
ax.bar(line_agg["line"], line_agg["avg_defect_rate"] * 100,
       color=bar_colors[:len(line_agg)])
ax.set_title("ライン別不良率")
ax.set_xlabel("製造ライン")
ax.set_ylabel("平均不良率（%）")
for i, v in enumerate(line_agg["avg_defect_rate"]):
    ax.text(i, v * 100 + 0.01, f"{v*100:.2f}%", ha="center", va="bottom", fontsize=10)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_line_defect_rate.png", dpi=150)
plt.close()
print("bar_line_defect_rate.png 出力完了")

# ── Chart 3: 生産性 vs 不良率の散布図（工程別色分け） ──
PROCESS_COLORS = {
    "組立": "#2196F3",
    "溶接": "#F44336",
    "検査": "#4CAF50",
    "梱包": "#FF9800",
}

fig, ax = plt.subplots(figsize=(8, 6))
for process, grp in df.groupby("process"):
    color = PROCESS_COLORS.get(process, "#9E9E9E")
    ax.scatter(
        grp["productivity"],
        grp["defect_rate"] * 100,
        label=process,
        alpha=0.5,
        s=20,
        color=color,
    )
ax.set_title("生産性 vs 不良率（工程別）")
ax.set_xlabel("生産性（個/時）")
ax.set_ylabel("不良率（%）")
ax.legend(title="工程")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "scatter_productivity_defect.png", dpi=150)
plt.close()
print("scatter_productivity_defect.png 出力完了")
