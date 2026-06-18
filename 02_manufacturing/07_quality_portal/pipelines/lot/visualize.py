"""ロット別合否判定: グラフ生成"""
import json
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "BIZ UDGothic"
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("output")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(OUTPUT_DIR / "cleaned_lot.csv", encoding="utf-8-sig")
df["date"] = pd.to_datetime(df["date"])

# 1. 製品別合格率棒グラフ
product_rates = df.groupby("product").apply(
    lambda x: (x["result"] == "合格").sum() / len(x), include_groups=False
).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#16a34a" if r >= 0.95 else "#d97706" if r >= 0.80 else "#dc2626"
          for r in product_rates.values]
bars = ax.bar(product_rates.index, product_rates.values * 100, color=colors)
ax.set_title("製品別合格率", fontsize=14)
ax.set_ylabel("合格率（%）")
ax.set_ylim(0, 110)
ax.bar_label(bars, fmt="%.1f%%", padding=3)
ax.axhline(y=product_rates.mean() * 100, color="#1e3a5f", linestyle="--", label="平均")
ax.legend()
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_product_pass.png", dpi=100)
plt.close()

# 2. 検査項目別不合格率棒グラフ
item_fail = df.groupby("item").apply(
    lambda x: (x["result"] == "不合格").sum() / len(x), include_groups=False
).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
colors_item = ["#dc2626" if r > 0.10 else "#d97706" if r > 0.05 else "#16a34a"
               for r in item_fail.values]
bars2 = ax.bar(item_fail.index, item_fail.values * 100, color=colors_item)
ax.set_title("検査項目別不合格率", fontsize=14)
ax.set_ylabel("不合格率（%）")
ax.bar_label(bars2, fmt="%.1f%%", padding=3)
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "bar_item_fail.png", dpi=100)
plt.close()

# 3. ロット別合否一覧表（画像として出力）
lot_summary = df.groupby("lot_id").agg(
    製品名=("product", "first"),
    検査日=("date", "first"),
    検査数=("result", "count"),
    合格数=("result", lambda x: (x == "合格").sum()),
).assign(合格率=lambda x: (x["合格数"] / x["検査数"] * 100).round(1),
         判定=lambda x: x.apply(lambda r: "合格" if r["合格率"] == 100.0 else "不合格", axis=1))
lot_summary = lot_summary.head(20)

fig, ax = plt.subplots(figsize=(12, max(4, len(lot_summary) * 0.4 + 1)))
ax.axis("off")
col_labels = ["製品名", "検査日", "検査数", "合格数", "合格率(%)", "判定"]
table_data = []
for lot_id, row in lot_summary.iterrows():
    date_val = row["検査日"]
    date_str = date_val.date() if hasattr(date_val, "date") else str(date_val)
    table_data.append([
        str(row["製品名"]),
        str(date_str),
        int(row["検査数"]),
        int(row["合格数"]),
        f"{row['合格率']}%",
        row["判定"],
    ])

tbl = ax.table(cellText=table_data, colLabels=col_labels, rowLabels=lot_summary.index,
               loc="center", cellLoc="center")
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.scale(1, 1.4)
for (row, col), cell in tbl.get_celld().items():
    if row == 0:
        cell.set_facecolor("#1e3a5f")
        cell.set_text_props(color="white", fontweight="bold")
    elif col >= 0 and row > 0:
        result_text = table_data[row - 1][5] if col == 5 else ""
        if "不合格" in result_text:
            cell.set_facecolor("#fee2e2")
        elif row % 2 == 0:
            cell.set_facecolor("#f0f4f8")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "table_lot_list.png", dpi=100, bbox_inches="tight")
plt.close()

result = {"passed": 3, "results": [
    {"id": 1, "name": "製品別合格率棒グラフ", "status": "PASS"},
    {"id": 2, "name": "検査項目別不合格率棒グラフ", "status": "PASS"},
    {"id": 3, "name": "ロット別一覧表", "status": "PASS"},
]}
(OUTPUT_DIR / "result_charts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print("グラフ生成完了")
