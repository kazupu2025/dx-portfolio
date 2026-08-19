# -*- coding: utf-8 -*-
"""
B-58: 生徒入学申込・入学率分析
Streamlit ダッシュボード
"""

import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CLEANED_FILE = BASE_DIR / "output" / "cleaned_applications_202401.csv"


@st.cache_data
def load_enrollment_analysis_data() -> pd.DataFrame:
    if not CLEANED_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")


st.title("📚 B-58 生徒入学申込・入学率分析ダッシュボード")
st.markdown("教育 x HR・採用 | 2024年1月度 入学申込分析")

df_all = load_enrollment_analysis_data()

if df_all.empty:
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# --- サイドバー ---
with st.sidebar:
    st.header("フィルター")
    dept_options = sorted(df_all["department"].dropna().unique().tolist()) if "department" in df_all.columns else []
    selected_depts = st.multiselect("学科を選択", options=dept_options, default=dept_options)

    sel_options = sorted(df_all["selection_method"].dropna().unique().tolist()) if "selection_method" in df_all.columns else []
    selected_sels = st.multiselect("選考方法を選択", options=sel_options, default=sel_options)

# フィルター適用
mask = pd.Series([True] * len(df_all), index=df_all.index)
if "department" in df_all.columns and selected_depts:
    mask &= df_all["department"].isin(selected_depts)
if "selection_method" in df_all.columns and selected_sels:
    mask &= df_all["selection_method"].isin(selected_sels)
df_filtered = df_all[mask].copy()

if df_filtered.empty:
    st.warning("フィルター条件に合致するデータがありません。")
    st.stop()

# --- タブ ---
tab1, tab2, tab3 = st.tabs(["KPIサマリー", "学科・選考分析", "申込明細データ"])

with tab1:
    st.subheader("KPI サマリー")
    total = len(df_filtered)
    pass_count = int(df_filtered["is_enrolled"].sum()) if "is_enrolled" in df_filtered.columns else 0
    pass_rate = pass_count / total * 100 if total > 0 else 0
    avg_score = df_filtered["score"].mean() if "score" in df_filtered.columns else 0.0
    interview_rate = ((df_filtered["interview_flag"] == 1).sum() / total * 100) if "interview_flag" in df_filtered.columns else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総申込数", f"{total} 件")
    col2.metric("合格率", f"{pass_rate:.1f} %")
    col3.metric("平均点", f"{avg_score:.1f} 点")
    col4.metric("面接実施率", f"{interview_rate:.1f} %")

    st.markdown("---")
    st.subheader("合否内訳")
    if "result" in df_filtered.columns:
        result_counts = df_filtered["result"].value_counts()
        st.bar_chart(result_counts)

with tab2:
    st.subheader("学科別合格率")
    if "department" in df_filtered.columns and "is_enrolled" in df_filtered.columns:
        _id_col = "app_id" if "app_id" in df_filtered.columns else df_filtered.columns[0]
        dept_group = df_filtered.groupby("department").agg(
            申込数=(_id_col, "count"),
            合格数=("is_enrolled", "sum"),
        )
        dept_group["合格率(%)"] = (dept_group["合格数"] / dept_group["申込数"] * 100).round(1)
        dept_group = dept_group.sort_values("合格率(%)", ascending=False)
        st.bar_chart(dept_group["合格率(%)"])
        st.dataframe(dept_group.reset_index(), use_container_width=True)

    st.subheader("選考方法別合格率")
    if "selection_method" in df_filtered.columns and "is_enrolled" in df_filtered.columns:
        sel_group = df_filtered.groupby("selection_method").agg(
            申込数=(_id_col, "count"),
            合格数=("is_enrolled", "sum"),
        )
        sel_group["合格率(%)"] = (sel_group["合格数"] / sel_group["申込数"] * 100).round(1)
        sel_group = sel_group.sort_values("合格率(%)", ascending=False)
        st.bar_chart(sel_group["合格率(%)"])
        st.dataframe(sel_group.reset_index(), use_container_width=True)

with tab3:
    st.subheader("申込明細データ")
    st.caption(f"表示件数: {len(df_filtered)} 件（フィルター適用後）")
    display_cols = ["app_date", "app_id", "department", "selection_method",
                    "region", "result", "score", "interview_flag", "score_grade", "source_file"]
    available_cols = [c for c in display_cols if c in df_filtered.columns]
    st.dataframe(df_filtered[available_cols].reset_index(drop=True) if available_cols else df_filtered, use_container_width=True)
    csv_data = df_filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(label="CSVダウンロード", data=csv_data,
                       file_name="filtered_applications.csv", mime="text/csv")
