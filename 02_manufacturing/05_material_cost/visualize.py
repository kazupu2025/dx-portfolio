import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_material_202401.csv"
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["quantity", "unit_price", "prev_month_price", "price_change_rate", "total_cost"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# 1. カテゴリ別仕入コスト合計の棒グラフ
cat_cost = df.groupby("category")["total_cost"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(cat_cost.index, cat_cost.values, color="#2563eb")
ax.set_title("カテゴリ別 仕入コスト合計（2024年1月）", fontsize=14)
ax.set_ylabel("仕入コスト")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=8)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_category_cost.png", dpi=150)
plt.close()
print("Saved: bar_category_cost.png")

# 2. 単価変動率上位10品目の横棒グラフ（急騰/急落を色分け）
if "price_change_rate" in df.columns and "price_change_flag" in df.columns:
    mat_change = (df.groupby(["material_name", "price_change_flag"])["price_change_rate"]
                  .mean()
                  .reset_index())
    mat_avg = df.groupby("material_name")["price_change_rate"].mean().abs()
    top10_names = mat_avg.sort_values(ascending=False).head(10).index
    mat_top10 = df[df["material_name"].isin(top10_names)].groupby(
        ["material_name", "price_change_flag"]
    )["price_change_rate"].mean().reset_index()

    # 各品目の代表フラグ（急騰>急落>安定）
    flag_priority = {"急騰": 2, "急落": 1, "安定": 0}
    mat_rep = (df[df["material_name"].isin(top10_names)]
               .groupby("material_name")
               .agg(avg_rate=("price_change_rate", "mean"),
                    flag=("price_change_flag", lambda x: max(x.unique(), key=lambda f: flag_priority.get(f, 0))))
               .reset_index())
    mat_rep = mat_rep.reindex(mat_rep["avg_rate"].abs().sort_values(ascending=True).index)

    colors = []
    for _, row in mat_rep.iterrows():
        if row["flag"] == "急騰":
            colors.append("#ef4444")
        elif row["flag"] == "急落":
            colors.append("#3b82f6")
        else:
            colors.append("#94a3b8")

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(mat_rep["material_name"], mat_rep["avg_rate"] * 100, color=colors)
    ax.axvline(x=0, color="black", linewidth=0.8)
    ax.axvline(x=20, color="#ef4444", linestyle="--", linewidth=0.8, label="急騰ライン(+20%)")
    ax.axvline(x=-20, color="#3b82f6", linestyle="--", linewidth=0.8, label="急落ライン(-20%)")
    ax.set_title("単価変動率 上位10品目（赤=急騰 / 青=急落 / 灰=安定）", fontsize=13)
    ax.set_xlabel("平均変動率(%)")
    ax.legend(fontsize=8)
    for bar in bars:
        w = bar.get_width()
        x_pos = w + 0.5 if w >= 0 else w - 0.5
        ha = "left" if w >= 0 else "right"
        ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                f"{w:.1f}%", va="center", ha=ha, fontsize=8)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "bar_material_price_change.png", dpi=150)
    plt.close()
    print("Saved: bar_material_price_change.png")
else:
    # フォールバック: 単純な変動率棒グラフ
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title("単価変動率（データなし）", fontsize=13)
    plt.savefig(CHARTS_DIR / "bar_material_price_change.png", dpi=150)
    plt.close()
    print("Saved: bar_material_price_change.png (fallback)")

# 3. 仕入先別コスト構成の円グラフ
sup_cost = df.groupby("supplier")["total_cost"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(
    sup_cost.values,
    labels=sup_cost.index,
    autopct="%1.1f%%",
    startangle=90,
    colors=["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe"],
)
for t in autotexts:
    t.set_fontsize(10)
ax.set_title("仕入先別コスト構成（2024年1月）", fontsize=14)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "pie_supplier_cost.png", dpi=150)
plt.close()
print("Saved: pie_supplier_cost.png")

print("Chart generation complete.")
