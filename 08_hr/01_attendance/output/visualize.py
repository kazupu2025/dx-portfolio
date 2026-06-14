import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
OT_WARNING = config.get("overtime_warning_hours", 45.0)
OT_DANGER = config.get("overtime_danger_hours", 60.0)

df = pd.read_csv("output/cleaned_attendance_202401.csv", encoding="utf-8-sig")
for col in ["overtime_hours", "actual_work_hours", "paid_leave"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

charts_dir = Path("output/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. 部門別平均残業時間棒グラフ
dept_emp = df.groupby("department")["employee_id"].nunique()
dept_ot = df.groupby("department")["overtime_hours"].sum()
dept_avg_ot = (dept_ot / dept_emp).sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#ef4444" if v > OT_WARNING/4.3 else "#2563eb" for v in dept_avg_ot.values]
bars = ax.bar(dept_avg_ot.index, dept_avg_ot.values, color=colors)
ax.axhline(y=OT_WARNING/4.3, color="#f97316", linestyle="--", label=f"月{OT_WARNING:.0f}h相当（日次換算）")
ax.set_title("部門別 平均残業時間（2024年1月・日次平均）", fontsize=14)
ax.set_ylabel("平均残業時間（時間/日）")
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + h*0.02,
            f"{h:.2f}h", ha="center", va="bottom", fontsize=9)
ax.legend()
plt.tight_layout()
plt.savefig(charts_dir / "bar_dept_overtime.png", dpi=150)
plt.close()
print("Saved: bar_dept_overtime.png")

# 2. 残業時間上位者棒グラフ
emp_ot = df.groupby(["employee_id", "employee_name", "department"])["overtime_hours"].sum().reset_index()
emp_ot = emp_ot.sort_values("overtime_hours", ascending=False).head(15)
labels = [f"{r['employee_name']}\n({r['department']})" for _, r in emp_ot.iterrows()]
colors2 = ["#ef4444" if v > OT_DANGER else ("#f97316" if v > OT_WARNING else "#2563eb")
           for v in emp_ot["overtime_hours"]]

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(range(len(emp_ot)), emp_ot["overtime_hours"], color=colors2)
ax.axhline(y=OT_WARNING, color="#f97316", linestyle="--", label=f"警告ライン({OT_WARNING:.0f}h)")
ax.axhline(y=OT_DANGER, color="#ef4444", linestyle="--", label=f"危険ライン({OT_DANGER:.0f}h)")
ax.set_title("月次残業時間 上位15名（赤=60h超、橙=45h超）", fontsize=14)
ax.set_ylabel("月次残業時間（h）")
ax.set_xticks(range(len(emp_ot)))
ax.set_xticklabels(labels, fontsize=8)
ax.legend()
plt.tight_layout()
plt.savefig(charts_dir / "bar_overtime_alert.png", dpi=150)
plt.close()
print("Saved: bar_overtime_alert.png")

# 3. 日次出勤数トレンド
if "date" in df.columns:
    daily_count = df.groupby("date")["employee_id"].count().reset_index()
    daily_count.columns = ["date", "count"]
    daily_count = daily_count.sort_values("date")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(daily_count["date"], daily_count["count"], color="#2563eb", marker="o", markersize=4)
    ax.fill_between(daily_count["date"], daily_count["count"], alpha=0.15, color="#2563eb")
    ax.set_title("日次出勤記録数トレンド（2024年1月）", fontsize=14)
    ax.set_ylabel("出勤記録数（件）")
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%m/%d"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(charts_dir / "line_daily_attendance.png", dpi=150)
    plt.close()
    print("Saved: line_daily_attendance.png")
else:
    print("WARN: date 列なし、line_daily_attendance.png をスキップ")

print("グラフ生成完了")
