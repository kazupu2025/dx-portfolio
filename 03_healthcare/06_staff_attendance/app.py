# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'
import matplotlib.pyplot as plt
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_attendance_202401.csv")

st.set_page_config(
    page_title="医療スタッフ勤怠・稼働率分析ダッシュボード",
    page_icon=None,
    layout="wide",
)

st.title("医療スタッフ勤怠・稼働率分析ダッシュボード")

if not os.path.exists(CLEANED_FILE):
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

# --- Sidebar filters ---
st.sidebar.header("フィルター")

all_staff_types = sorted(df["staff_type"].dropna().unique().tolist())
selected_staff_types = st.sidebar.multiselect(
    "スタッフ種別",
    options=all_staff_types,
    default=all_staff_types,
)

all_departments = sorted(df["department"].dropna().unique().tolist())
selected_departments = st.sidebar.multiselect(
    "診療科",
    options=all_departments,
    default=all_departments,
)

df_filtered = df[
    df["staff_type"].isin(selected_staff_types) &
    df["department"].isin(selected_departments)
].copy()

if len(df_filtered) == 0:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["KPIサマリー", "種別・診療科分析", "勤怠明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    total_records = len(df_filtered)
    attendance_count = (df_filtered["is_absent"] == 0).sum()
    attendance_rate = attendance_count / total_records if total_records > 0 else 0.0
    avg_utilization = df_filtered["utilization_rate"].mean()
    avg_overtime = df_filtered["overtime_hours"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総勤務記録数", "{:,}件".format(total_records))
    col2.metric("出勤率", "{:.1%}".format(attendance_rate))
    col3.metric("平均稼働率", "{:.1%}".format(avg_utilization))
    col4.metric("平均残業時間", "{:.2f}h".format(avg_overtime))

    st.markdown("---")
    st.subheader("欠勤内訳")
    absent_df = df_filtered[df_filtered["is_absent"] == 1]
    if len(absent_df) > 0 and absent_df["absence_reason"].notna().any():
        reason_counts = absent_df["absence_reason"].value_counts()
        st.bar_chart(reason_counts)
    else:
        st.info("欠勤データがありません。")

with tab2:
    st.subheader("スタッフ種別別分析")

    staff_summary = df_filtered.groupby("staff_type").agg(
        total_records=("record_id", "count"),
        absent_count=("is_absent", "sum"),
        avg_utilization_rate=("utilization_rate", "mean"),
        avg_overtime_hours=("overtime_hours", "mean"),
    ).reset_index()
    staff_summary["attendance_rate"] = (
        (staff_summary["total_records"] - staff_summary["absent_count"])
        / staff_summary["total_records"]
    ).round(4)

    col_a, col_b = st.columns(2)

    with col_a:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        ax1.bar(staff_summary["staff_type"], staff_summary["avg_utilization_rate"], color="#4472C4")
        ax1.set_title("スタッフ種別別 平均稼働率")
        ax1.set_ylabel("稼働率")
        ax1.set_ylim(0, 1.4)
        for i, v in enumerate(staff_summary["avg_utilization_rate"]):
            ax1.text(i, v + 0.01, "{:.1%}".format(v), ha="center", va="bottom", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close()

    with col_b:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.bar(staff_summary["staff_type"], staff_summary["avg_overtime_hours"], color="#70AD47")
        ax2.set_title("スタッフ種別別 平均残業時間")
        ax2.set_ylabel("時間")
        for i, v in enumerate(staff_summary["avg_overtime_hours"]):
            ax2.text(i, v + 0.02, "{:.2f}h".format(v), ha="center", va="bottom", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    st.markdown("---")
    st.subheader("診療科別分析")

    dept_summary = df_filtered.groupby("department").agg(
        total_records=("record_id", "count"),
        absent_count=("is_absent", "sum"),
        avg_utilization_rate=("utilization_rate", "mean"),
    ).reset_index()
    dept_summary["attendance_rate"] = (
        (dept_summary["total_records"] - dept_summary["absent_count"])
        / dept_summary["total_records"]
    ).round(4)
    dept_summary_sorted = dept_summary.sort_values("absent_count", ascending=True)

    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.barh(dept_summary_sorted["department"], dept_summary_sorted["absent_count"], color="#ED7D31")
    ax3.set_title("診療科別 欠勤件数")
    ax3.set_xlabel("欠勤件数")
    for i, v in enumerate(dept_summary_sorted["absent_count"]):
        ax3.text(v + 0.1, i, str(int(v)), va="center", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

with tab3:
    st.subheader("勤怠明細データ")
    st.dataframe(df_filtered, use_container_width=True)
    csv_data = df_filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="CSVダウンロード",
        data=csv_data,
        file_name="attendance_filtered.csv",
        mime="text/csv",
    )
