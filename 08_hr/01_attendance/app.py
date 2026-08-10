"""人事 勤怠ダッシュボード — Plotly 動的チャート版"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from pathlib import Path

BASE = Path(__file__).parent
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
OT_WARNING = config.get("overtime_warning_hours", 45.0)
OT_DANGER  = config.get("overtime_danger_hours", 60.0)


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
st.caption("2024年1月 | 5部門 | サンプルデータ")

depts = sorted(df_all["department"].dropna().unique().tolist())
selected = st.multiselect("部門フィルター", depts, default=depts)
df = df_all[df_all["department"].isin(selected)] if selected else df_all

emp_ot          = df.groupby("employee_id")["overtime_hours"].sum()
total_employees = df["employee_id"].nunique()
total_ot        = df["overtime_hours"].sum()
avg_ot          = total_ot / total_employees if total_employees > 0 else 0
danger_count    = int((emp_ot > OT_DANGER).sum())
warning_count   = int(((emp_ot > OT_WARNING) & (emp_ot <= OT_DANGER)).sum())
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

tab1, tab2, tab3 = st.tabs(["📊 部門別残業", "🚨 残業アラート", "📅 日次出勤傾向"])

with tab1:
    dept_ot = df.groupby("department")["overtime_hours"].sum().reset_index()
    dept_ot.columns = ["部門", "総残業時間(h)"]
    dept_ot = dept_ot.sort_values("総残業時間(h)", ascending=False)
    dept_emp_count = df.groupby("department")["employee_id"].nunique().reset_index()
    dept_emp_count.columns = ["部門", "人数"]
    dept_ot = dept_ot.merge(dept_emp_count, on="部門")
    dept_ot["平均残業(h)"] = (dept_ot["総残業時間(h)"] / dept_ot["人数"]).round(1)

    fig = px.bar(dept_ot, x="部門", y="総残業時間(h)", title="部門別 月次総残業時間（2024年1月）",
                 text="総残業時間(h)", color_discrete_sequence=["#3b82f6"])
    fig.update_traces(texttemplate="%{text:.1f}h", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    emp_summary = df.groupby(["employee_id", "employee_name", "department"]).agg(
        月次残業時間=("overtime_hours", "sum")
    ).reset_index().round(1)
    emp_summary["アラート区分"] = emp_summary["月次残業時間"].apply(
        lambda x: "危険(60h超)" if x > OT_DANGER
        else ("警告(45h超)" if x > OT_WARNING else "正常")
    )
    color_map = {"危険(60h超)": "#ef4444", "警告(45h超)": "#f97316", "正常": "#3b82f6"}
    fig2 = px.bar(
        emp_summary.sort_values("月次残業時間", ascending=False),
        x="employee_name", y="月次残業時間",
        color="アラート区分", color_discrete_map=color_map,
        title="従業員別 月次残業時間（2024年1月）",
        hover_data=["department"],
        text="月次残業時間",
    )
    fig2.update_traces(texttemplate="%{text:.1f}h", textposition="outside")
    fig2.add_hline(y=OT_DANGER, line_dash="dash", line_color="#ef4444",
                   annotation_text=f"危険ライン ({OT_DANGER:.0f}h)")
    fig2.add_hline(y=OT_WARNING, line_dash="dot", line_color="#f97316",
                   annotation_text=f"警告ライン ({OT_WARNING:.0f}h)")
    fig2.update_layout(xaxis_title="従業員", yaxis_title="残業時間（h）")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    daily_att = df.groupby("date").agg(
        出勤人数=("employee_id", "nunique"),
        平均残業=("overtime_hours", "mean"),
    ).reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=daily_att["date"], y=daily_att["出勤人数"],
        name="出勤人数", marker_color="#93c5fd", yaxis="y1",
    ))
    fig3.add_trace(go.Scatter(
        x=daily_att["date"], y=daily_att["平均残業"].round(1),
        name="平均残業(h)", mode="lines+markers",
        marker=dict(color="#ef4444"), yaxis="y2",
    ))
    fig3.update_layout(
        title="日次 出勤人数 & 平均残業時間（2024年1月）",
        xaxis_title="日付",
        yaxis=dict(title="出勤人数（名）"),
        yaxis2=dict(title="平均残業時間（h）", overlaying="y", side="right"),
        legend=dict(x=0.01, y=0.99),
    )
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

st.subheader("残業アラート一覧（45h超）")
emp_tbl = df.groupby(["employee_id", "employee_name", "department"]).agg(
    月次残業時間=("overtime_hours", "sum"),
    出勤日数=("date", "count"),
    有給取得=("paid_leave", "sum"),
).round(1).reset_index()
emp_tbl["アラート"] = emp_tbl["月次残業時間"].apply(
    lambda x: "🔴 危険" if x > OT_DANGER else ("🟠 警告" if x > OT_WARNING else "✅ 正常")
)
alert_tbl = emp_tbl[emp_tbl["月次残業時間"] > OT_WARNING].sort_values("月次残業時間", ascending=False)
if len(alert_tbl) > 0:
    display = alert_tbl[["employee_name", "department", "月次残業時間", "出勤日数", "有給取得", "アラート"]].copy()
    display["月次残業時間"] = display["月次残業時間"].apply(lambda x: f"{x:.1f}h")
    st.dataframe(display, use_container_width=True)
else:
    st.success("✅ 残業アラート対象者なし（全員 45h 以下）")

st.divider()

st.subheader("部門別残業サマリー")
dept_emp_n = df.groupby("department")["employee_id"].nunique()
dept_tbl = df.groupby("department").agg(
    総残業時間=("overtime_hours", "sum"),
    有給取得計=("paid_leave", "sum"),
).copy()
dept_tbl["人数"] = dept_emp_n
dept_tbl["平均残業時間"] = (dept_tbl["総残業時間"] / dept_tbl["人数"]).round(1)
disp2 = dept_tbl[["人数", "平均残業時間", "総残業時間", "有給取得計"]].copy()
disp2["総残業時間"] = disp2["総残業時間"].apply(lambda x: f"{x:.1f}h")
disp2["平均残業時間"] = disp2["平均残業時間"].apply(lambda x: f"{x:.1f}h")
st.dataframe(disp2.sort_values("総残業時間", ascending=False), use_container_width=True)

st.divider()
with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
