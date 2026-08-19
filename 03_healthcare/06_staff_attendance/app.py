# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CLEANED_FILE = BASE_DIR / "output" / "cleaned_attendance_202401.csv"

st.title("🏥 B-50 医療スタッフ勤怠・稼働率分析ダッシュボード")


@st.cache_data
def load_staff_attendance_data() -> pd.DataFrame:
    if not CLEANED_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")


df_all = load_staff_attendance_data()

if df_all.empty:
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# --- Sidebar filters ---
with st.sidebar:
    st.header("フィルター")

    all_staff_types = sorted(df_all["staff_type"].dropna().unique().tolist()) if "staff_type" in df_all.columns else []
    selected_staff_types = st.multiselect(
        "スタッフ種別",
        options=all_staff_types,
        default=all_staff_types,
    )

    all_departments = sorted(df_all["department"].dropna().unique().tolist()) if "department" in df_all.columns else []
    selected_departments = st.multiselect(
        "診療科",
        options=all_departments,
        default=all_departments,
    )

mask = pd.Series([True] * len(df_all), index=df_all.index)
if "staff_type" in df_all.columns and selected_staff_types:
    mask &= df_all["staff_type"].isin(selected_staff_types)
if "department" in df_all.columns and selected_departments:
    mask &= df_all["department"].isin(selected_departments)
df_filtered = df_all[mask].copy()

if df_filtered.empty:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["KPIサマリー", "種別・診療科分析", "勤怠明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    total_records = len(df_filtered)
    is_absent_col = "is_absent" in df_filtered.columns
    utilization_col = "utilization_rate" in df_filtered.columns
    overtime_col = "overtime_hours" in df_filtered.columns

    attendance_rate = ((df_filtered["is_absent"] == 0).sum() / total_records) if is_absent_col else 0.0
    avg_utilization = df_filtered["utilization_rate"].mean() if utilization_col else 0.0
    avg_overtime = df_filtered["overtime_hours"].mean() if overtime_col else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総勤務記録数", f"{total_records:,}件")
    col2.metric("出勤率", f"{attendance_rate:.1%}")
    col3.metric("平均稼働率", f"{avg_utilization:.1%}")
    col4.metric("平均残業時間", f"{avg_overtime:.2f}h")

    st.markdown("---")
    st.subheader("欠勤内訳")
    if is_absent_col and "absence_reason" in df_filtered.columns:
        absent_df = df_filtered[df_filtered["is_absent"] == 1]
        if len(absent_df) > 0 and absent_df["absence_reason"].notna().any():
            reason_counts = absent_df["absence_reason"].value_counts()
            st.bar_chart(reason_counts)
        else:
            st.info("欠勤データがありません。")
    else:
        st.info("欠勤データがありません。")

with tab2:
    st.subheader("スタッフ種別別分析")

    if "staff_type" in df_filtered.columns:
        agg_dict = {"record_id": "count"} if "record_id" in df_filtered.columns else {}
        if "is_absent" in df_filtered.columns:
            agg_dict["is_absent"] = "sum"
        if "utilization_rate" in df_filtered.columns:
            agg_dict["utilization_rate"] = "mean"
        if "overtime_hours" in df_filtered.columns:
            agg_dict["overtime_hours"] = "mean"

        if agg_dict:
            staff_summary = df_filtered.groupby("staff_type").agg(agg_dict).reset_index()

            col_a, col_b = st.columns(2)
            with col_a:
                if "utilization_rate" in staff_summary.columns:
                    st.markdown("**スタッフ種別別 平均稼働率**")
                    util_chart = staff_summary.set_index("staff_type")["utilization_rate"]
                    st.bar_chart(util_chart)
            with col_b:
                if "overtime_hours" in staff_summary.columns:
                    st.markdown("**スタッフ種別別 平均残業時間**")
                    ot_chart = staff_summary.set_index("staff_type")["overtime_hours"]
                    st.bar_chart(ot_chart)

    st.markdown("---")
    st.subheader("診療科別 欠勤件数")
    if "department" in df_filtered.columns and "is_absent" in df_filtered.columns:
        dept_absent = df_filtered.groupby("department")["is_absent"].sum().sort_values(ascending=False)
        st.bar_chart(dept_absent)

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
