"""
analyze.py — 退学リスク分析・レポート生成
実行: cd 09_education/01_dropout_risk && python output/analyze.py
"""
import sys
from pathlib import Path
import pandas as pd
import yaml

BASE = Path(__file__).resolve().parent.parent
OUT  = BASE / "output"

def load_config() -> dict:
    with open(BASE / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    csv_path = OUT / "cleaned_dropout_202401.csv"

    if not csv_path.exists():
        print("ERROR: cleaned_dropout_202401.csv が存在しません。cleanse.py を先に実行してください。")
        sys.exit(1)

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    print(f"読み込み: {len(df)}行, {df['student_id'].nunique()}受講生")

    # 受講生単位集計（5科目の平均スコア）
    stu_df = df.groupby("student_id").agg(
        student_name=("student_name", "first"),
        course=("course", "first"),
        avg_dropout_score=("dropout_risk_score", "mean"),
        min_dropout_score=("dropout_risk_score", "min"),
        avg_attendance=("attendance_rate", "mean"),
        avg_midterm=("midterm_score", "mean"),
        avg_final=("final_score", "mean"),
        avg_assignment=("assignment_rate", "mean"),
    ).reset_index()
    stu_df["avg_dropout_score"] = stu_df["avg_dropout_score"].round(1)

    high_thresh = config["high_risk_threshold"]
    med_thresh  = config["medium_risk_threshold"]

    def classify(score):
        if score < high_thresh: return "高リスク"
        elif score < med_thresh: return "中リスク"
        else: return "低リスク"

    stu_df["student_risk"] = stu_df["avg_dropout_score"].apply(classify)

    # 1. リスク分類別サマリー
    risk_summary = stu_df.groupby("student_risk").agg(
        受講生数=("student_id", "count"),
        平均スコア=("avg_dropout_score", "mean"),
    ).round(1)
    risk_summary["割合(%)"] = (risk_summary["受講生数"] / len(stu_df) * 100).round(1)

    # 2. 科目別リスク統計
    subject_stats = df.groupby("subject").agg(
        平均スコア=("dropout_risk_score", "mean"),
        高リスク率=("risk_category", lambda x: (x=="高リスク").mean() * 100),
        平均出席率=("attendance_rate", "mean"),
    ).round(1)

    # 3. コース別リスク分析
    course_stats = stu_df.groupby("course").agg(
        受講生数=("student_id", "count"),
        高リスク率=("student_risk", lambda x: (x=="高リスク").mean() * 100),
        平均スコア=("avg_dropout_score", "mean"),
        平均出席率=("avg_attendance", "mean"),
    ).round(1)

    # 4. アラート受講生リスト（最もリスクの高い受講生TOP20）
    alert_df = stu_df.sort_values("avg_dropout_score").head(20)[
        ["student_id","student_name","course","avg_dropout_score","min_dropout_score","avg_attendance","avg_midterm","avg_final"]
    ].copy()
    alert_df.columns = ["student_id","student_name","course","avg_score","min_score","avg_attendance","avg_midterm","avg_final"]
    alert_df = alert_df.round(1)
    alert_df.to_csv(OUT / "alert_students_202401.csv", index=False, encoding="utf-8-sig")
    print(f"アラートCSV出力: {len(alert_df)}件")

    # 5. 低出席率アラート
    low_att_thresh = config["low_attendance_alert"]
    low_att = df[df["attendance_rate"] < low_att_thresh][["student_id","subject","attendance_rate"]].drop_duplicates()
    low_att_students = low_att["student_id"].nunique()

    # 6. ビジネスインサイト
    n_high = (stu_df["student_risk"] == "高リスク").sum()
    n_mid  = (stu_df["student_risk"] == "中リスク").sum()
    n_total = len(stu_df)

    worst_subject = subject_stats["平均スコア"].idxmin()
    best_course   = course_stats["高リスク率"].idxmin()
    worst_course  = course_stats["高リスク率"].idxmax()

    # レポート生成
    lines = []
    lines.append("# 退学リスク分析レポート（2024年1月末時点）")
    lines.append("")
    lines.append("## 1. リスク分類別受講生サマリー")
    lines.append("")
    lines.append(f"対象受講生: **{n_total}名** | 高リスク: **{n_high}名** | 中リスク: **{n_mid}名**")
    lines.append("")
    lines.append(risk_summary.to_markdown())
    lines.append("")

    lines.append("## 2. 科目別リスク統計")
    lines.append("")
    lines.append(subject_stats.to_markdown())
    lines.append("")
    lines.append(f"- 最もリスクが高い科目: **{worst_subject}**（平均スコア {subject_stats.loc[worst_subject,'平均スコア']:.1f}点）")
    lines.append("")

    lines.append("## 3. コース別リスク分析")
    lines.append("")
    lines.append(course_stats.to_markdown())
    lines.append("")
    lines.append(f"- 高リスク率最高コース: **{worst_course}**（{course_stats.loc[worst_course,'高リスク率']:.1f}%）")
    lines.append(f"- 高リスク率最低コース: **{best_course}**（{course_stats.loc[best_course,'高リスク率']:.1f}%）")
    lines.append("")

    lines.append("## 4. アラート受講生リスト（退学リスクスコア低位TOP20）")
    lines.append("")
    lines.append(alert_df.to_markdown(index=False))
    lines.append("")
    lines.append(f"詳細: `output/alert_students_202401.csv` を参照")
    lines.append("")

    lines.append("## 5. 低出席率アラート")
    lines.append("")
    lines.append(f"出席率{low_att_thresh:.0f}%未満の受講生: **{low_att_students}名**（延べ{len(low_att)}科目）")
    lines.append("")

    lines.append("## 6. ビジネスインサイトと介入推奨アクション")
    lines.append("")
    lines.append(f"**退学リスク概況**: 全{n_total}名中 高リスク{n_high}名（{n_high/n_total*100:.1f}%）が早急な支援介入を必要としています。")
    lines.append("")
    lines.append("### 推奨アクション")
    lines.append(f"1. **即時介入**: 退学リスクスコア{high_thresh}点未満の{n_high}名に対して、担任・チューターによる個別面談を優先的に実施する。")
    lines.append(f"2. **科目サポート強化**: {worst_subject}は全受講生の平均スコアが最低であり、補講・学習支援プログラムの導入を検討する。")
    lines.append(f"3. **出席管理強化**: 出席率{low_att_thresh:.0f}%未満の{low_att_students}名に対して、欠席理由の聞き取りと早期警戒通知を送付する。")
    lines.append(f"4. **コース別対策**: {worst_course}の高リスク率が最も高い。コースの難易度調整・追加サポートを検討する。")
    lines.append(f"5. **中リスク予防**: 中リスク{n_mid}名（{n_mid/n_total*100:.1f}%）についても月次フォローアップを実施し、高リスクへの移行を防ぐ。")
    lines.append("")

    report_path = OUT / "analysis_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"レポート出力: {report_path}")
    print("analyze.py 完了")

if __name__ == "__main__":
    main()
