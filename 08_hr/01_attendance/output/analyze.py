import pandas as pd
import numpy as np
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

STANDARD_HRS = config.get("standard_work_hours", 8.0)
OT_WARNING = config.get("overtime_warning_hours", 45.0)
OT_DANGER = config.get("overtime_danger_hours", 60.0)
ANNUAL_PAID = config.get("annual_paid_leave_days", 20)

df = pd.read_csv("output/cleaned_attendance_202401.csv", encoding="utf-8-sig")
for col in ["actual_work_hours", "overtime_hours", "paid_leave", "break_minutes"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

lines = ["# 勤怠データ分析レポート（2024年1月）\n"]

# 1. 従業員別月次残業集計
lines.append("## 1. 従業員別月次残業集計（上位20名）\n")
emp_summary = df.groupby(["employee_id", "employee_name", "department"]).agg(
    月次残業時間=("overtime_hours", "sum"),
    月次労働時間=("actual_work_hours", "sum"),
    出勤日数=("date", "count"),
    有給取得日数=("paid_leave", "sum"),
).round(1).sort_values("月次残業時間", ascending=False)

emp_summary["アラート"] = emp_summary["月次残業時間"].apply(
    lambda x: "危険(60h超)" if x > OT_DANGER
    else ("警告(45h超)" if x > OT_WARNING else "正常")
)
fmt = emp_summary.head(20).copy()
fmt["月次残業時間_表示"] = fmt["月次残業時間"].map("{:.1f}h".format)
fmt["月次労働時間_表示"] = fmt["月次労働時間"].map("{:.1f}h".format)
lines.append(fmt[["月次残業時間_表示", "月次労働時間_表示", "出勤日数", "有給取得日数", "アラート"]].rename(
    columns={"月次残業時間_表示": "月次残業時間", "月次労働時間_表示": "月次労働時間"}
).to_markdown())
lines.append("")

# 2. 残業アラート
lines.append("## 2. 残業アラート\n")
danger_emp = emp_summary[emp_summary["月次残業時間"] > OT_DANGER]
warning_emp = emp_summary[(emp_summary["月次残業時間"] > OT_WARNING) & (emp_summary["月次残業時間"] <= OT_DANGER)]

if len(danger_emp) > 0:
    lines.append(f"- **危険（{OT_DANGER:.0f}h超）: {len(danger_emp)}名**")
    for (eid, ename, dept), row in danger_emp.iterrows():
        lines.append(f"  - {ename}（{dept}）: {row['月次残業時間']:.1f}h")
else:
    lines.append(f"- 危険（{OT_DANGER:.0f}h超）: 0名")

if len(warning_emp) > 0:
    lines.append(f"- **警告（{OT_WARNING:.0f}h超）: {len(warning_emp)}名**")
    for (eid, ename, dept), row in warning_emp.iterrows():
        lines.append(f"  - {ename}（{dept}）: {row['月次残業時間']:.1f}h")
else:
    lines.append(f"- 警告（{OT_WARNING:.0f}h超）: 0名")
lines.append("")

# 3. 部門別残業サマリー
lines.append("## 3. 部門別残業サマリー\n")
dept_ot = df.groupby("department")["overtime_hours"].sum()
dept_emp_count = df.groupby("department")["employee_id"].nunique()
dept_paid = df.groupby("department")["paid_leave"].sum()
dept_records = df.groupby("department")["date"].count()

dept_summary = pd.DataFrame({
    "人数": dept_emp_count,
    "総残業時間": dept_ot,
    "有給取得計": dept_paid,
    "出勤レコード数": dept_records,
})
dept_summary["平均残業時間"] = (dept_summary["総残業時間"] / dept_summary["人数"]).round(1)
dept_summary["有休消化率(%)"] = (
    dept_summary["有給取得計"] / (dept_summary["人数"] * ANNUAL_PAID / 12) * 100
).round(1)

fmt2 = dept_summary.copy()
fmt2["総残業時間_表示"] = fmt2["総残業時間"].map("{:.1f}h".format)
fmt2["平均残業時間_表示"] = fmt2["平均残業時間"].map("{:.1f}h".format)
lines.append(fmt2[["人数", "平均残業時間_表示", "総残業時間_表示", "有給取得計", "有休消化率(%)"]].rename(
    columns={"平均残業時間_表示": "平均残業時間", "総残業時間_表示": "総残業時間"}
).to_markdown())
lines.append("")

# 4. 日次出勤傾向（上位3部門）
lines.append("## 4. 日次出勤傾向\n")
if "date" in df.columns:
    top_depts = dept_summary.nlargest(3, "総残業時間").index.tolist()
    for dept in top_depts:
        dept_data = df[df["department"] == dept]
        daily = dept_data.groupby("date")["overtime_hours"].sum()
        total_ot = daily.sum()
        peak_date = daily.idxmax() if len(daily) > 0 else None
        if peak_date is not None:
            lines.append(f"- {dept}: 月残業合計 {total_ot:.1f}h、最多残業日 {str(peak_date)[:10]} ({daily.max():.1f}h)")
        else:
            lines.append(f"- {dept}: 月残業合計 {total_ot:.1f}h")
lines.append("")

# 5. 異常値検出（個人別残業 ±2σ）
lines.append("## 5. 異常値検出（残業時間 ±2σ）\n")
anomalies = []
for dept, grp in df.groupby("department"):
    daily_ot = grp.groupby(["employee_id", "date"])["overtime_hours"].sum().reset_index()
    if len(daily_ot) > 2:
        mean = daily_ot["overtime_hours"].mean()
        std = daily_ot["overtime_hours"].std()
        if std > 0:
            outliers = daily_ot[daily_ot["overtime_hours"] > mean + 2 * std]
            for _, row in outliers.iterrows():
                date_str = str(row["date"])[:10]
                anomalies.append(
                    f"- {dept} | {row['employee_id']} | {date_str} | {row['overtime_hours']:.1f}h残業"
                    f"（平均 {mean:.1f}h から {(row['overtime_hours']-mean)/std:+.1f}σ）"
                )

if anomalies:
    lines.extend(anomalies)
else:
    lines.append("- 異常値は検出されませんでした")
lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total_ot = df["overtime_hours"].sum()
total_emp = df["employee_id"].nunique()
avg_ot_per_person = total_ot / total_emp if total_emp > 0 else 0
top_dept_name = dept_summary["総残業時間"].idxmax() if not dept_summary.empty else "不明"

lines.append(f"- 対象従業員数: **{total_emp}名**")
lines.append(f"- 月次総残業時間: **{total_ot:.1f}h**（1人平均: {avg_ot_per_person:.1f}h）")
lines.append(f"- 残業最多部門: **{top_dept_name}**")
if len(danger_emp) > 0:
    lines.append(f"- **危険: {len(danger_emp)}名が月{OT_DANGER:.0f}h超の危険残業 — 即時対応が必要です**")
if len(warning_emp) > 0:
    lines.append(f"- **警告: {len(warning_emp)}名が月{OT_WARNING:.0f}h超の警告残業 — 業務分散を検討してください**")
if anomalies:
    lines.append(f"- 異常値 {len(anomalies)} 件検出 — 特定日に偏った長時間残業の原因を調査してください")
lines.append("")

Path("output/analysis_report.md").write_text("\n".join(lines), encoding="utf-8")
print("分析完了: output/analysis_report.md を生成しました")
