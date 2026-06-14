import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
BUDGET_ALERT_THRESHOLD = config.get("budget_alert_threshold", 1.0)

df = pd.read_csv("output/cleaned_expense_202401.csv", encoding="utf-8-sig")
for col in ["amount", "budget"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

charts_dir = Path("output/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. 部門別経費棒グラフ
dept_total = df.groupby("department")["amount"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(dept_total.index, dept_total.values, color="#2563eb")
ax.set_title("部門別経費合計（2024年1月）", fontsize=14)
ax.set_ylabel("経費金額（円）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + h*0.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(charts_dir / "bar_dept_expense.png", dpi=150)
plt.close()
print("Saved: bar_dept_expense.png")

# 2. 費目別経費棒グラフ
type_total = df.groupby("expense_type")["amount"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(type_total.index, type_total.values, color="#7c3aed")
ax.set_title("費目別経費合計（2024年1月）", fontsize=14)
ax.set_ylabel("経費金額（円）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + h*0.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(charts_dir / "bar_expense_type.png", dpi=150)
plt.close()
print("Saved: bar_expense_type.png")

# 3. 予算 vs 実績比較（予算超過は赤棒）
dept_agg = df.groupby("department").agg(
    actual=("amount", "sum"),
    budget=("budget", "sum"),
).sort_values("actual", ascending=False)
dept_agg["ratio"] = dept_agg["actual"] / dept_agg["budget"].replace(0, 1)
colors = ["#ef4444" if r > BUDGET_ALERT_THRESHOLD else "#22c55e" for r in dept_agg["ratio"]]

x = range(len(dept_agg))
width = 0.35
fig, ax = plt.subplots(figsize=(11, 5))
bars1 = ax.bar([i - width/2 for i in x], dept_agg["budget"], width, label="予算", color="#93c5fd")
bars2 = ax.bar([i + width/2 for i in x], dept_agg["actual"], width, label="実績", color=colors)
ax.set_title("部門別 予算 vs 実績（赤=超過）（2024年1月）", fontsize=14)
ax.set_ylabel("金額（円）")
ax.set_xticks(list(x))
ax.set_xticklabels(dept_agg.index)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.legend()
plt.tight_layout()
plt.savefig(charts_dir / "bar_budget_vs_actual.png", dpi=150)
plt.close()
print("Saved: bar_budget_vs_actual.png")

print("グラフ生成完了")
