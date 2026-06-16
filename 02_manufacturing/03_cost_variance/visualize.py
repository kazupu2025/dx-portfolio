"""3枚のチャートを output/charts/ に生成"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUTPUT_DIR / "cleaned_production_cost_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# Chart 1: ライン別原価差異（積み上げ棒）
line_var = df.groupby("line_id")[["material_variance","labor_variance","overhead_variance"]].sum()
fig, ax = plt.subplots(figsize=(8,5))
line_var.plot(kind="bar", stacked=True, ax=ax, color=["#2196F3","#FF9800","#4CAF50"])
ax.set_title("ライン別原価差異（材料費・労務費・間接費）")
ax.set_xlabel("製造ライン")
ax.set_ylabel("差異額（円）")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f"{x/1e6:.1f}M"))
ax.legend(["材料費差異","労務費差異","間接費差異"])
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_line_variance.png", dpi=150)
plt.close()
print("bar_line_variance.png 出力完了")

# Chart 2: 製品別差異率 上位10件（横棒）
prod_var = df.groupby(["product_id","product_name"]).agg(
    avg_variance_ratio=("variance_ratio","mean")
).reset_index().sort_values("avg_variance_ratio", ascending=False).head(10)
fig, ax = plt.subplots(figsize=(9,6))
colors = ["#F44336" if v > 0 else "#2196F3" for v in prod_var["avg_variance_ratio"]]
ax.barh(prod_var["product_name"], prod_var["avg_variance_ratio"]*100, color=colors)
ax.set_title("製品別差異率ランキング（上位10件）")
ax.set_xlabel("平均差異率（%）")
ax.axvline(0, color="black", linewidth=0.8)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_product_variance_ratio.png", dpi=150)
plt.close()
print("bar_product_variance_ratio.png 出力完了")

# Chart 3: 差異構成比（パイチャート）
mat_abs = df["material_variance"].abs().sum()
lab_abs = df["labor_variance"].abs().sum()
ohd_abs = df["overhead_variance"].abs().sum()
fig, ax = plt.subplots(figsize=(6,6))
ax.pie([mat_abs, lab_abs, ohd_abs],
       labels=["材料費差異","労務費差異","間接費差異"],
       autopct="%1.1f%%", colors=["#2196F3","#FF9800","#4CAF50"],
       startangle=90)
ax.set_title("差異構成比（費目別絶対値）")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "pie_variance_components.png", dpi=150)
plt.close()
print("pie_variance_components.png 出力完了")
