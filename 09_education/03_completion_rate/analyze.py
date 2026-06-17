import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
CSV_PATH = OUTPUT_DIR / "cleaned_enrollment_202401.csv"

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["study_hours", "test_score", "satisfaction", "is_completed"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

lines = ["# 受講率・修了率分析レポート（2024年1月）\n"]

# 1. 講座別修了率・平均スコア・平均満足度
lines.append("## 1. 講座別 修了率・平均スコア・平均満足度\n")
course_summary = df.groupby("course_name").agg(
    総受講数=("enroll_no", "count"),
    修了数=("is_completed", "sum"),
    平均スコア=("test_score", "mean"),
    平均満足度=("satisfaction", "mean"),
    平均学習時間=("study_hours", "mean"),
).reset_index()
course_summary["修了率(%)"] = (
    course_summary["修了数"] / course_summary["総受講数"] * 100
).round(1)
course_summary["平均スコア"] = course_summary["平均スコア"].round(1)
course_summary["平均満足度"] = course_summary["平均満足度"].round(2)
course_summary["平均学習時間"] = course_summary["平均学習時間"].round(1)
course_summary = course_summary.sort_values("修了率(%)", ascending=False)
lines.append(course_summary.to_markdown(index=False))
lines.append("")

# 2. 受講者タイプ別修了率
lines.append("## 2. 受講者タイプ別 修了率\n")
learner_summary = df.groupby("learner_type").agg(
    総受講数=("enroll_no", "count"),
    修了数=("is_completed", "sum"),
    平均スコア=("test_score", "mean"),
    平均満足度=("satisfaction", "mean"),
).reset_index()
learner_summary["修了率(%)"] = (
    learner_summary["修了数"] / learner_summary["総受講数"] * 100
).round(1)
learner_summary["平均スコア"] = learner_summary["平均スコア"].round(1)
learner_summary["平均満足度"] = learner_summary["平均満足度"].round(2)
learner_summary = learner_summary.sort_values("修了率(%)", ascending=False)
lines.append(learner_summary.to_markdown(index=False))
lines.append("")

# 3. 中途離脱リスク分析
lines.append("## 3. 中途離脱リスク分析\n")
if "dropout_risk" in df.columns:
    risk_summary = df.groupby("dropout_risk").agg(
        件数=("enroll_no", "count"),
        平均スコア=("test_score", "mean"),
        平均学習時間=("study_hours", "mean"),
    ).reset_index()
    risk_summary["平均スコア"] = risk_summary["平均スコア"].round(1)
    risk_summary["平均学習時間"] = risk_summary["平均学習時間"].round(1)
    lines.append(risk_summary.to_markdown(index=False))
    lines.append("")

    high_risk = df[df["dropout_risk"] == "高"]
    if len(high_risk) > 0:
        lines.append(f"中途離脱リスク「高」の受講者数: **{len(high_risk)}名**")
        lines.append("")
        risk_by_course = high_risk.groupby("course_name").size().sort_values(ascending=False)
        lines.append("講座別 リスク高受講者数:")
        for course, cnt in risk_by_course.items():
            lines.append(f"- {course}: {cnt}名")
        lines.append("")
else:
    lines.append("dropout_risk列なし\n")

# 4. 月別受講・修了トレンド
lines.append("## 4. 月別 受講・修了トレンド\n")
if "enroll_date" in df.columns:
    df["enroll_month"] = pd.to_datetime(df["enroll_date"], errors="coerce").dt.to_period("M").astype(str)
    monthly = df.groupby("enroll_month").agg(
        受講数=("enroll_no", "count"),
        修了数=("is_completed", "sum"),
    ).reset_index()
    monthly["修了率(%)"] = (monthly["修了数"] / monthly["受講数"] * 100).round(1)
    lines.append(monthly.to_markdown(index=False))
    lines.append("")
else:
    lines.append("enroll_date列なし\n")

# 5. スコアグレード別集計
lines.append("## 5. スコアグレード別 集計\n")
if "score_grade" in df.columns:
    grade_summary = df.groupby("score_grade").agg(
        件数=("enroll_no", "count"),
        平均満足度=("satisfaction", "mean"),
    ).reset_index()
    grade_summary["割合(%)"] = (grade_summary["件数"] / len(df) * 100).round(1)
    grade_summary["平均満足度"] = grade_summary["平均満足度"].round(2)
    grade_order = {"優秀": 0, "合格": 1, "不合格": 2}
    grade_summary["sort_key"] = grade_summary["score_grade"].map(grade_order)
    grade_summary = grade_summary.sort_values("sort_key").drop(columns=["sort_key"])
    lines.append(grade_summary.to_markdown(index=False))
    lines.append("")

# 6. ビジネスインサイト
lines.append("## 6. ビジネスインサイト\n")
total_count = len(df)
completed_count = int(df["is_completed"].sum())
completion_rate = completed_count / total_count * 100 if total_count > 0 else 0.0
avg_score = float(df["test_score"].mean())
avg_satisfaction = float(df["satisfaction"].mean())
dropout_count = (df["status"] == "中途離脱").sum() if "status" in df.columns else 0

top_course = course_summary.iloc[0]["course_name"] if len(course_summary) > 0 else "不明"
bottom_course = course_summary.iloc[-1]["course_name"] if len(course_summary) > 0 else "不明"
top_learner = learner_summary.iloc[0]["learner_type"] if len(learner_summary) > 0 else "不明"

lines.append(f"- 総受講数: **{total_count} 件**")
lines.append(f"- 修了数: **{completed_count} 件**")
lines.append(f"- 全体修了率: **{completion_rate:.1f}%**")
lines.append(f"- 中途離脱数: **{dropout_count} 件**")
lines.append(f"- 平均スコア: **{avg_score:.1f} 点**")
lines.append(f"- 平均満足度: **{avg_satisfaction:.2f} / 5.0**")
lines.append(f"- 修了率最高講座: **{top_course}**")
lines.append(f"- 修了率最低講座: **{bottom_course}**")
lines.append(f"- 修了率最高受講者タイプ: **{top_learner}**")
lines.append("")

lines.append("### 改善示唆")
if completion_rate < 70.0:
    lines.append(f"- 全体修了率が{completion_rate:.1f}%と目標の70%を下回っています。受講環境・カリキュラムの見直しを検討してください。")
else:
    lines.append(f"- 全体修了率は{completion_rate:.1f}%と良好です。引き続き品質維持に努めてください。")

if "dropout_risk" in df.columns:
    high_risk_count = (df["dropout_risk"] == "高").sum()
    if high_risk_count > total_count * 0.15:
        lines.append(f"- 離脱リスク高受講者が{high_risk_count}名({high_risk_count/total_count*100:.1f}%)います。早期フォローアップ施策の実施を推奨します。")

bottom_rate = float(course_summary.iloc[-1]["修了率(%)"])
if bottom_rate < 55.0:
    lines.append(f"- 「{bottom_course}」の修了率が{bottom_rate:.1f}%と特に低く、コンテンツ難易度・学習サポートの改善が必要です。")

if avg_score < 65.0:
    lines.append(f"- 平均スコアが{avg_score:.1f}点と低い水準です。試験内容・学習教材の品質向上を検討してください。")
lines.append("")

# 出力: analysis_report.md
output_path = OUTPUT_DIR / "analysis_report.md"
output_path.write_text("\n".join(lines), encoding="utf-8")
print(f"分析完了: 総受講数={total_count}, 修了率={completion_rate:.1f}%, 平均スコア={avg_score:.1f}")

# 出力: course_summary_202401.csv
course_out = course_summary.copy()
course_out.to_csv(OUTPUT_DIR / "course_summary_202401.csv", index=False, encoding="utf-8-sig")
print(f"講座サマリーCSV出力: {len(course_out)} 件 -> output/course_summary_202401.csv")
