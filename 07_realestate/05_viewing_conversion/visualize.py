# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_visits_202401.csv")
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["is_contracted"] = pd.to_numeric(df["is_contracted"], errors="coerce")
df["asking_price"] = pd.to_numeric(df["asking_price"], errors="coerce")

# 1. bar_type_conversion.png - Property type conversion rate (vertical bar)
type_group = df.groupby("property_type").agg(
    visit_count=("visit_id", "count"),
    contract_count=("is_contracted", "sum"),
).reset_index()
type_group["conversion_rate"] = type_group["contract_count"] / type_group["visit_count"]

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(type_group["property_type"], type_group["conversion_rate"], color="#4C72B0")
ax.set_title("物件タイプ別成約率")
ax.set_xlabel("物件タイプ")
ax.set_ylabel("成約率")
ax.set_ylim(0, 1)
for i, v in enumerate(type_group["conversion_rate"]):
    ax.text(i, v + 0.01, "{:.1%}".format(v), ha="center", fontsize=10)
plt.tight_layout()
out1 = os.path.join(CHARTS_DIR, "bar_type_conversion.png")
plt.savefig(out1, dpi=100)
plt.close()
print("[OK] Saved: {}".format(out1))

# 2. bar_area_visit.png - Area visit count (horizontal bar)
area_group = df.groupby("area").agg(visit_count=("visit_id", "count")).reset_index()
area_group = area_group.sort_values("visit_count", ascending=True)

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(area_group["area"], area_group["visit_count"], color="#55A868")
ax.set_title("エリア別内見件数")
ax.set_xlabel("内見件数")
ax.set_ylabel("エリア")
for i, v in enumerate(area_group["visit_count"]):
    ax.text(v + 0.5, i, str(v), va="center", fontsize=10)
plt.tight_layout()
out2 = os.path.join(CHARTS_DIR, "bar_area_visit.png")
plt.savefig(out2, dpi=100)
plt.close()
print("[OK] Saved: {}".format(out2))

# 3. bar_price_tier_count.png - Price tier count (vertical bar)
tier_order = ["低価格帯", "中価格帯", "高価格帯"]
tier_group = df.groupby("price_tier").agg(count=("visit_id", "count")).reindex(tier_order).reset_index()

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(tier_group["price_tier"], tier_group["count"], color="#C44E52")
ax.set_title("価格帯別件数")
ax.set_xlabel("価格帯")
ax.set_ylabel("件数")
for i, v in enumerate(tier_group["count"]):
    ax.text(i, v + 0.5, str(v), ha="center", fontsize=10)
plt.tight_layout()
out3 = os.path.join(CHARTS_DIR, "bar_price_tier_count.png")
plt.savefig(out3, dpi=100)
plt.close()
print("[OK] Saved: {}".format(out3))

print("[OK] All charts saved to {}".format(CHARTS_DIR))
