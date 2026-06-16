import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_instructor_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["lesson_count", "lesson_hours", "lesson_cost", "attendee_count", "hourly_rate", "cost_per_attendee"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

lines = ["# 講師稼働・コマ数管理分析レポート（2024年1月）\n"]

# 1. 講師別月間コマ数・稼働時間・報酬合計ランキング
lines.append("## 1. 講師別月間コマ数・稼働時間・報酬合計ランキング（上位15名）\n")
inst_summary = df.groupby(["instructor_id", "name", "specialty", "employment_type"]).agg(
    月間コマ数=("lesson_count", "sum"),
    月間稼働時間=("lesson_hours", "sum"),
    月間報酬合計=("lesson_cost", "sum"),
    総受講者数=("attendee_count", "sum"),
).reset_index()
inst_summary["月間稼働時間"] = inst_summary["月間稼働時間"].round(1)
inst_summary = inst_summary.sort_values("月間コマ数", ascending=False)
top15 = inst_summary.head(15).copy()
fmt1 = top15.copy()
fmt1["月間報酬合計"] = fmt1["月間報酬合計"].map("{:,.0f}円".format)
lines.append(fmt1.to_markdown(index=False))
lines.append("")

# 2. 専門分野別コスト・受講者数
lines.append("## 2. 専門分野別コスト・受講者数\n")
specialty_summary = df.groupby("specialty").agg(
    総コマ数=("lesson_count", "sum"),
    総稼働時間=("lesson_hours", "sum"),
    総コスト=("lesson_cost", "sum"),
    総受講者数=("attendee_count", "sum"),
    担当講師数=("instructor_id", "nunique"),
).reset_index()
specialty_summary["コスト割合(%)"] = (
    specialty_summary["総コスト"] / specialty_summary["総コスト"].sum() * 100
).round(2)
specialty_summary["受講者1人あたりコスト"] = (
    specialty_summary["総コスト"] / specialty_summary["総受講者数"].replace(0, 1)
).round(0)
specialty_summary = specialty_summary.sort_values("総コスト", ascending=False)
fmt2 = specialty_summary.copy()
fmt2["総コスト"] = fmt2["総コスト"].map("{:,.0f}円".format)
fmt2["受講者1人あたりコスト"] = fmt2["受講者1人あたりコスト"].map("{:,.0f}円".format)
lines.append(fmt2.to_markdown(index=False))
lines.append("")

# 3. 雇用区分別平均単価・稼働率比較
lines.append("## 3. 雇用区分別平均単価・稼働率比較\n")
emp_summary = df.groupby("employment_type").agg(
    平均時給単価=("hourly_rate", "mean"),
    総コマ数=("lesson_count", "sum"),
    総コスト=("lesson_cost", "sum"),
    講師数=("instructor_id", "nunique"),
).reset_index()
emp_summary["平均時給単価"] = emp_summary["平均時給単価"].round(0)
emp_summary["1講師あたり月間コマ数"] = (
    emp_summary["総コマ数"] / emp_summary["講師数"].replace(0, 1)
).round(1)
emp_summary["コスト割合(%)"] = (
    emp_summary["総コスト"] / emp_summary["総コスト"].sum() * 100
).round(2)
emp_summary = emp_summary.sort_values("平均時給単価", ascending=False)
fmt3 = emp_summary.copy()
fmt3["平均時給単価"] = fmt3["平均時給単価"].map("{:,.0f}円".format)
fmt3["総コスト"] = fmt3["総コスト"].map("{:,.0f}円".format)
lines.append(fmt3.to_markdown(index=False))
lines.append("")

# 4. 受講者1名あたりコスト（cost_per_attendee）上位コース
lines.append("## 4. 受講者1名あたりコスト 上位コース TOP10\n")
course_summary = df.groupby(["course_name", "specialty"]).agg(
    総コマ数=("lesson_count", "sum"),
    総受講者数=("attendee_count", "sum"),
    総コスト=("lesson_cost", "sum"),
).reset_index()
course_summary = course_summary[course_summary["総受講者数"] > 0].copy()
course_summary["受講者1名あたりコスト"] = (
    course_summary["総コスト"] / course_summary["総受講者数"]
).round(0)
top_courses = course_summary.sort_values("受講者1名あたりコスト", ascending=False).head(10)
fmt4 = top_courses.copy()
fmt4["総コスト"] = fmt4["総コスト"].map("{:,.0f}円".format)
fmt4["受講者1名あたりコスト"] = fmt4["受講者1名あたりコスト"].map("{:,.0f}円".format)
lines.append(fmt4.to_markdown(index=False))
lines.append("")

# 5. 高負荷講師リスト（workload_flag = 高負荷 の多い講師）
lines.append("## 5. 高負荷セッション 講師別集計\n")
if "workload_flag" in df.columns:
    high_load = df[df["workload_flag"] == "高負荷"].groupby(["instructor_id", "name", "employment_type"]).agg(
        高負荷セッション数=("lesson_count", "count"),
        高負荷コマ数合計=("lesson_count", "sum"),
    ).reset_index().sort_values("高負荷コマ数合計", ascending=False).head(10)
    if len(high_load) > 0:
        lines.append(f"1コマ数が3コマ超のセッション合計: {len(df[df['workload_flag']=='高負荷'])} 件")
        lines.append(high_load.to_markdown(index=False))
    else:
        lines.append("高負荷セッションなし")
lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total_lessons = int(df["lesson_count"].sum())
total_hours = float(df["lesson_hours"].sum())
total_cost = float(df["lesson_cost"].sum())
total_attendees = int(df["attendee_count"].sum())
avg_cost_per_attendee = total_cost / total_attendees if total_attendees > 0 else 0

top_specialty = specialty_summary.iloc[0]["specialty"] if len(specialty_summary) > 0 else "不明"
top_emp_cost = emp_summary.iloc[0]["employment_type"] if len(emp_summary) > 0 else "不明"
most_active_instructor = inst_summary.iloc[0]["name"] if len(inst_summary) > 0 else "不明"

lines.append(f"- 月次総コマ数: **{total_lessons} コマ**")
lines.append(f"- 月次総稼働時間: **{total_hours:.1f} 時間**（1コマ90分換算）")
lines.append(f"- 月次総講師コスト: **{total_cost:,.0f} 円**")
lines.append(f"- 総受講者数: **{total_attendees} 名**")
lines.append(f"- 平均受講者1名あたりコスト: **{avg_cost_per_attendee:,.0f} 円**")
lines.append(f"- コスト最大専門分野: **{top_specialty}**")
lines.append(f"- コスト最大雇用区分: **{top_emp_cost}**（平均時給単価が最高）")
lines.append(f"- 月間コマ数トップ講師: **{most_active_instructor}**")
lines.append("")
lines.append("### 改善提案")
if emp_summary[emp_summary["employment_type"] == "外部講師"]["総コスト"].sum() > \
   emp_summary["総コスト"].sum() * 0.4:
    lines.append("- 外部講師のコスト比率が高い。内製化（正社員・契約社員の育成）を検討してください。")
high_cost_courses = course_summary[course_summary["受講者1名あたりコスト"] > avg_cost_per_attendee * 1.5]
if len(high_cost_courses) > 0:
    lines.append(f"- {len(high_cost_courses)} コースで受講者1名あたりコストが平均の1.5倍超。集合研修化・オンライン化でコスト削減を検討してください。")
lines.append("")

output_path = OUTPUT_DIR / "analysis_report.md"
output_path.write_text("\n".join(lines), encoding="utf-8")
print(f"分析完了: 総コマ数={total_lessons}, 総コスト={total_cost:,.0f}円, 総受講者数={total_attendees}名")

# instructor_summary_202401.csv 出力（instructor_id別集計）
inst_out = inst_summary.copy()
inst_out.to_csv(OUTPUT_DIR / "instructor_summary_202401.csv", index=False, encoding="utf-8-sig")
print(f"講師サマリーCSV出力: {len(inst_out)} 件 -> output/instructor_summary_202401.csv")
