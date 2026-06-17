# -*- coding: utf-8 -*-
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams['font.family'] = 'MS Gothic'

os.makedirs("output/charts", exist_ok=True)

df = pd.read_csv("output/cleaned_progress_202401.csv", encoding="utf-8-sig")

# 1. bar_site_progress.png - Horizontal bar chart of avg progress per site
site_progress = df.groupby("site_name")["progress_pct"].mean().sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(site_progress.index, site_progress.values, color="steelblue")
ax.set_xlabel("平均進捗率 (%)")
ax.set_title("現場別 平均進捗率")
ax.set_xlim(0, 100)
plt.tight_layout()
plt.savefig("output/charts/bar_site_progress.png", dpi=100)
plt.close()
print("[OK] output/charts/bar_site_progress.png saved")

# 2. bar_process_efficiency.png - Vertical bar chart of avg efficiency per process
process_eff = df.groupby("process")["efficiency"].mean()
fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(process_eff.index, process_eff.values, color="teal")
ax.set_ylabel("平均稼働効率")
ax.set_title("工程別 平均稼働効率")
plt.tight_layout()
plt.savefig("output/charts/bar_process_efficiency.png", dpi=100)
plt.close()
print("[OK] output/charts/bar_process_efficiency.png saved")

# 3. bar_site_defect.png - Vertical bar chart of total defects per site (red)
site_defect = df.groupby("site_name")["defect_count"].sum()
fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(site_defect.index, site_defect.values, color="red")
ax.set_ylabel("不具合件数合計")
ax.set_title("現場別 不具合件数")
plt.tight_layout()
plt.savefig("output/charts/bar_site_defect.png", dpi=100)
plt.close()
print("[OK] output/charts/bar_site_defect.png saved")
