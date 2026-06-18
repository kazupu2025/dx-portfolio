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

CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_attendance_202401.csv")
df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

# --- Chart 1: Staff type utilization rate (bar chart) ---
staff_util = df.groupby("staff_type")["utilization_rate"].mean().reset_index()
staff_util.columns = ["staff_type", "avg_utilization_rate"]
staff_util = staff_util.sort_values("avg_utilization_rate", ascending=False)

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(staff_util["staff_type"], staff_util["avg_utilization_rate"], color="#4472C4")
ax.set_title("スタッフ種別別 平均稼働率")
ax.set_xlabel("スタッフ種別")
ax.set_ylabel("平均稼働率")
ax.set_ylim(0, 1.4)
for i, v in enumerate(staff_util["avg_utilization_rate"]):
    ax.text(i, v + 0.01, "{:.1%}".format(v), ha="center", va="bottom", fontsize=10)
plt.tight_layout()
out1 = os.path.join(CHARTS_DIR, "bar_type_utilization.png")
plt.savefig(out1, dpi=100)
plt.close()
print("[OK] Saved: {}".format(out1))

# --- Chart 2: Department absence count (horizontal bar) ---
dept_absent = df.groupby("department")["is_absent"].sum().reset_index()
dept_absent.columns = ["department", "absent_count"]
dept_absent = dept_absent.sort_values("absent_count", ascending=True)

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(dept_absent["department"], dept_absent["absent_count"], color="#ED7D31")
ax.set_title("診療科別 欠勤件数")
ax.set_xlabel("欠勤件数")
ax.set_ylabel("診療科")
for i, v in enumerate(dept_absent["absent_count"]):
    ax.text(v + 0.1, i, str(int(v)), va="center", fontsize=10)
plt.tight_layout()
out2 = os.path.join(CHARTS_DIR, "bar_dept_absence.png")
plt.savefig(out2, dpi=100)
plt.close()
print("[OK] Saved: {}".format(out2))

# --- Chart 3: Staff type average overtime hours (bar chart) ---
staff_ot = df.groupby("staff_type")["overtime_hours"].mean().reset_index()
staff_ot.columns = ["staff_type", "avg_overtime_hours"]
staff_ot = staff_ot.sort_values("avg_overtime_hours", ascending=False)

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(staff_ot["staff_type"], staff_ot["avg_overtime_hours"], color="#70AD47")
ax.set_title("スタッフ種別別 平均残業時間")
ax.set_xlabel("スタッフ種別")
ax.set_ylabel("平均残業時間（時間）")
for i, v in enumerate(staff_ot["avg_overtime_hours"]):
    ax.text(i, v + 0.02, "{:.2f}h".format(v), ha="center", va="bottom", fontsize=10)
plt.tight_layout()
out3 = os.path.join(CHARTS_DIR, "bar_type_overtime.png")
plt.savefig(out3, dpi=100)
plt.close()
print("[OK] Saved: {}".format(out3))

print("[OK] All charts saved to {}".format(CHARTS_DIR))
