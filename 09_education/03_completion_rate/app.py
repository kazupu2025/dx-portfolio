import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="教育研修 受講・修了率ダッシュボード",
    page_icon="📚",
    layout="wide",
)

BASE = Path(__file__).parent


@st.cache_data
def load_data():
    p = BASE / "output" / "cleaned_enrollment_202401.csv"
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["study_hours", "test_score", "satisfaction", "is_completed"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "enroll_date" in df.columns:
        df["enroll_date"] = pd.to_datetime(df["enroll_date"], errors="coerce")
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("📚 教育研修 受講・修了率ダッシュボード")
st.caption("2024年1月 | 受講率・修了率レポートパイプライン")

# --- 講座フィルター ---
courses = sorted(df_all["course_name"].dropna().unique().tolist()) if "course_name" in df_all.columns else []
selected_courses = st.multiselect("講座フィルター", courses, default=courses)
df = df_all[df_all["course_name"].isin(selected_courses)] if selected_courses else df_all

# --- KPI 4つ ---
total_count = len(df)
completed_count = int(df["is_completed"].sum()) if "is_completed" in df.columns else 0
completion_rate = completed_count / total_count * 100 if total_count > 0 else 0.0
avg_score = float(df["test_score"].mean()) if "test_score" in df.columns else 0.0
avg_satisfaction = float(df["satisfaction"].mean()) if "satisfaction" in df.columns else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("総受講数", f"{total_count:,} 件")
c2.metric("修了率", f"{completion_rate:.1f}%")
c3.metric("平均スコア", f"{avg_score:.1f} 点")
c4.metric("平均満足度", f"{avg_satisfaction:.2f} / 5.0")

st.divider()

# --- 3タブ ---
charts_dir = BASE / "output" / "charts"
tab1, tab2, tab3 = st.tabs(["講座別修了率", "スコア分布", "受講者タイプ別"])

with tab1:
    p = charts_dir / "bar_course_completion.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を実行してください。")

    st.subheader("講座別 修了率テーブル")
    if "course_name" in df.columns and "is_completed" in df.columns:
        tbl = df.groupby("course_name").agg(
            総受講数=("enroll_no", "count"),
            修了数=("is_completed", "sum"),
            平均スコア=("test_score", "mean"),
            平均満足度=("satisfaction", "mean"),
        ).copy()
        tbl["修了率(%)"] = (tbl["修了数"] / tbl["総受講数"] * 100).round(1)
        tbl["平均スコア"] = tbl["平均スコア"].round(1)
        tbl["平均満足度"] = tbl["平均満足度"].round(2)
        tbl = tbl.sort_values("修了率(%)", ascending=False)
        st.dataframe(tbl, use_container_width=True)

with tab2:
    p = charts_dir / "bar_score_grade.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を実行してください。")

    if "score_grade" in df.columns:
        st.subheader("スコアグレード別 件数")
        grade_tbl = df["score_grade"].value_counts().reset_index()
        grade_tbl.columns = ["スコアグレード", "件数"]
        grade_tbl["割合(%)"] = (grade_tbl["件数"] / len(df) * 100).round(1)
        st.dataframe(grade_tbl, use_container_width=True)

with tab3:
    p = charts_dir / "bar_learnertype_completion.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。visualize.py を実行してください。")

    if "learner_type" in df.columns and "is_completed" in df.columns:
        st.subheader("受講者タイプ別 修了率テーブル")
        lt_tbl = df.groupby("learner_type").agg(
            総受講数=("enroll_no", "count"),
            修了数=("is_completed", "sum"),
            平均スコア=("test_score", "mean"),
            平均満足度=("satisfaction", "mean"),
        ).copy()
        lt_tbl["修了率(%)"] = (lt_tbl["修了数"] / lt_tbl["総受講数"] * 100).round(1)
        lt_tbl["平均スコア"] = lt_tbl["平均スコア"].round(1)
        lt_tbl["平均満足度"] = lt_tbl["平均満足度"].round(2)
        lt_tbl = lt_tbl.sort_values("修了率(%)", ascending=False)
        st.dataframe(lt_tbl, use_container_width=True)

st.divider()

# --- 中途離脱リスク高テーブル ---
st.subheader("中途離脱リスク「高」 受講者一覧")
if "dropout_risk" in df.columns:
    high_risk = df[df["dropout_risk"] == "高"].copy()
    if len(high_risk) > 0:
        disp_cols = [c for c in ["enroll_no", "enroll_date", "course_name", "learner_type",
                                   "study_hours", "test_score", "status"] if c in high_risk.columns]
        st.dataframe(high_risk[disp_cols].head(50), use_container_width=True)
        st.caption(f"リスク高: {len(high_risk)} 件")
    else:
        st.info("中途離脱リスク「高」の受講者はいません。")
else:
    st.info("dropout_risk列が見つかりません。")

st.divider()

# --- 分析レポート expander ---
with st.expander("分析レポートを見る", expanded=False):
    st.markdown(report_text)
