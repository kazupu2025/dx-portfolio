import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="人事 勤怠ダッシュボード",
    page_icon="⏰",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
OT_WARNING = config.get("overtime_warning_hours", 45.0)
OT_DANGER = config.get("overtime_danger_hours", 60.0)


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_attendance_202401.csv", encoding="utf-8-sig")
    for col in ["overtime_hours", "actual_work_hours", "paid_leave", "break_minutes"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("⏰ 人事 勤怠ダッシュボード")
st.caption("2024年1月 | 5部門")

depts = sorted(df_all["department"].dropna().unique().tolist())
selected = st.multiselect("部門フィルター", depts, default=depts)
df = df_all[df_all["department"].isin(selected)] if selected else df_all

# メトリクス計算
emp_ot = df.groupby("employee_id")["overtime_hours"].sum()
total_employees = df["employee_id"].nunique()
total_ot = df["overtime_hours"].sum()
avg_ot = total_ot / total_employees if total_employees > 0 else 0
danger_count = int((emp_ot > OT_DANGER).sum())
warning_count = int(((emp_ot > OT_WARNING) & (emp_ot <= OT_DANGER)).sum())
total_paid_leave = df["paid_leave"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("対象従業員数", f"{total_employees}名")
c2.metric("月次総残業時間", f"{total_ot:.1f}h",
          delta=f"1人平均 {avg_ot:.1f}h")
c3.metric("危険（60h超）", f"{danger_count}名",
          delta="要即対応" if danger_count > 0 else "問題なし",
          delta_color="inverse" if danger_count > 0 else "normal")
c4.metric("警告（45h超）", f"{warning_count}名",
          delta="業務分散推奨" if warning_count > 0 else "問題なし",
          delta_color="inverse" if warning_count > 0 else "normal")
c5.metric("有給取得件数", f"{total_paid_leave:.0f}件")

st.divider()

tab1, tab2, tab3 = st.tabs(["部門別残業", "残業アラート", "日次出勤傾向"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_dept_overtime.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

with tab2:
    p = charts_dir / "bar_overtime_alert.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"赤棒 = {OT_DANGER:.0f}h超（危険）、橙棒 = {OT_WARNING:.0f}h超（警告）、青棒 = 正常")
    else:
        st.warning("グラフなし")

with tab3:
    p = charts_dir / "line_daily_attendance.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

st.divider()

# 残業アラートテーブル
st.subheader("残業アラート一覧（45h超）")
emp_tbl = df.groupby(["employee_id", "employee_name", "department"]).agg(
    月次残業時間=("overtime_hours", "sum"),
    出勤日数=("date", "count"),
    有給取得=("paid_leave", "sum"),
).round(1).reset_index()
emp_tbl["アラート"] = emp_tbl["月次残業時間"].apply(
    lambda x: "危険" if x > OT_DANGER else ("警告" if x > OT_WARNING else "正常")
)
alert_tbl = emp_tbl[emp_tbl["月次残業時間"] > OT_WARNING].sort_values("月次残業時間", ascending=False)
if len(alert_tbl) > 0:
    display = alert_tbl[["employee_name", "department", "月次残業時間", "出勤日数", "有給取得", "アラート"]].copy()
    display["月次残業時間"] = display["月次残業時間"].apply(lambda x: f"{x:.1f}h")
    st.dataframe(display, use_container_width=True)
else:
    st.success("残業アラート対象者なし（全員 45h 以下）")

st.divider()

# 部門別サマリーテーブル
st.subheader("部門別残業サマリー")
dept_emp = df.groupby("department")["employee_id"].nunique()
dept_tbl = df.groupby("department").agg(
    総残業時間=("overtime_hours", "sum"),
    有給取得計=("paid_leave", "sum"),
).copy()
dept_tbl["人数"] = dept_emp
dept_tbl["平均残業時間"] = (dept_tbl["総残業時間"] / dept_tbl["人数"]).round(1)
dept_tbl = dept_tbl.sort_values("総残業時間", ascending=False)
disp2 = dept_tbl[["人数", "平均残業時間", "総残業時間", "有給取得計"]].copy()
disp2["総残業時間"] = disp2["総残業時間"].apply(lambda x: f"{x:.1f}h")
disp2["平均残業時間"] = disp2["平均残業時間"].apply(lambda x: f"{x:.1f}h")
st.dataframe(disp2, use_container_width=True)

st.divider()

with st.expander("分析レポートを見る", expanded=False):
    st.markdown(report_text)
