# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_claims_202401.csv")
os.makedirs(CHARTS_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# --- 1. bar_dept_claim.png: Dept total claim amount (horizontal bar) ---
dept_claim = df.groupby("dept")["claim_amount"].sum().sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(dept_claim.index, dept_claim.values, color="#4472C4")
ax.set_xlabel("請求金額合計 (円)")
ax.set_title("診療科別 請求金額合計")
for i, v in enumerate(dept_claim.values):
    ax.text(v + max(dept_claim.values) * 0.01, i, "{:,.0f}".format(v), va="center", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "bar_dept_claim.png"), dpi=100)
plt.close()
print("[OK] bar_dept_claim.png saved")

# --- 2. bar_insurance_reduction.png: Insurance avg reduction rate (vertical bar) ---
ins_red = df.groupby("insurance_type")["reduction_rate"].mean()
fig, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(ins_red.index, ins_red.values * 100, color="#ED7D31")
ax.set_ylabel("平均査定率 (%)")
ax.set_title("保険区分別 平均査定率")
for bar, v in zip(bars, ins_red.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
            "{:.2f}%".format(v * 100), ha="center", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "bar_insurance_reduction.png"), dpi=100)
plt.close()
print("[OK] bar_insurance_reduction.png saved")

# --- 3. bar_dept_collection.png: Dept collection rate (vertical bar) ---
dept_coll = df.groupby("dept").apply(
    lambda g: (g["payment_status"] == "支払済み").mean() * 100
)
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(dept_coll.index, dept_coll.values, color="#70AD47")
ax.set_ylabel("回収率 (%)")
ax.set_title("診療科別 回収率")
ax.set_ylim(0, 120)
for bar, v in zip(bars, dept_coll.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            "{:.1f}%".format(v), ha="center", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "bar_dept_collection.png"), dpi=100)
plt.close()
print("[OK] bar_dept_collection.png saved")
