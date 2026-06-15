import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
WASTE_ALERT = config.get("waste_rate_alert_threshold", 0.10)

df = pd.read_csv("output/cleaned_cost_202401.csv", encoding="utf-8-sig")
for col in ["purchase_cost", "waste_cost", "waste_rate", "purchase_qty", "waste_qty"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

charts_dir = Path("output/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. カテゴリ別仕入コスト棒グラフ
cat_cost = df.groupby("category")["purchase_cost"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(cat_cost.index, cat_cost.values, color="#2563eb")
ax.set_title("カテゴリ別 仕入コスト合計（2024年1月）", fontsize=14)
ax.set_ylabel("仕入コスト（円）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h * 1.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=8)
plt.tight_layout()
plt.savefig(charts_dir / "bar_category_cost.png", dpi=150)
plt.close()
print("Saved: bar_category_cost.png")

# 2. 店舗別食材ロス率棒グラフ（ロス率10%超は赤）
store_loss = (df.groupby("store")["waste_qty"].sum() /
              df.groupby("store")["purchase_qty"].sum() * 100).sort_values(ascending=False)
colors = ["#ef4444" if v > WASTE_ALERT * 100 else "#2563eb" for v in store_loss.values]
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(store_loss.index, store_loss.values, color=colors)
ax.axhline(y=WASTE_ALERT * 100, color="#f97316", linestyle="--",
           label=f"アラートライン ({WASTE_ALERT*100:.0f}%)")
ax.set_title("店舗別 食材ロス率（2024年1月）", fontsize=14)
ax.set_ylabel("ロス率（%）")
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 0.1,
            f"{h:.2f}%", ha="center", va="bottom", fontsize=9)
ax.legend()
plt.tight_layout()
plt.savefig(charts_dir / "bar_store_loss_rate.png", dpi=150)
plt.close()
print("Saved: bar_store_loss_rate.png")

# 3. 廃棄コスト上位食材棒グラフ
ing_waste = df.groupby("ingredient_name")["waste_cost"].sum().sort_values(ascending=False).head(10)
fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.barh(ing_waste.index[::-1], ing_waste.values[::-1], color="#ef4444")
ax.set_title("廃棄コスト上位食材 TOP10（2024年1月）", fontsize=14)
ax.set_xlabel("廃棄コスト（円）")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    w = bar.get_width()
    ax.text(w + w * 0.01, bar.get_y() + bar.get_height()/2,
            f"{w:,.0f}円", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(charts_dir / "bar_ingredient_waste.png", dpi=150)
plt.close()
print("Saved: bar_ingredient_waste.png")

print("グラフ生成完了")
