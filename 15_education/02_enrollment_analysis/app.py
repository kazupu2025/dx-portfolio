# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
Streamlit ダッシュボード
"""

import os
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'
import matplotlib.pyplot as plt
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CLEANED_FILE = os.path.join(OUTPUT_DIR, "cleaned_applications_202401.csv")

st.set_page_config(
    page_title="生徒入学申込・入学率分析ダッシュボード",
    page_icon=None,
    layout="wide",
)

st.title("生徒入学申込・入学率分析ダッシュボード")
st.markdown("**C-55** | 教育 x HR・採用 | 2024年1月度 入学申込分析")

# データ読み込み
if not os.path.exists(CLEANED_FILE):
    st.error(f"データファイルが見つかりません。先に cleanse.py を実行してください。\n{CLEANED_FILE}")
    st.stop()

df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

# --- サイドバー ---
st.sidebar.header("フィルター")

dept_options = sorted(df["department"].dropna().unique().tolist())
selected_depts = st.sidebar.multiselect(
    "学科を選択",
    options=dept_options,
    default=dept_options,
)

sel_options = sorted(df["selection_method"].dropna().unique().tolist())
selected_sels = st.sidebar.multiselect(
    "選考方法を選択",
    options=sel_options,
    default=sel_options,
)

# フィルター適用
df_filtered = df[
    df["department"].isin(selected_depts) &
    df["selection_method"].isin(selected_sels)
].copy()

if df_filtered.empty:
    st.warning("フィルター条件に合致するデータがありません。")
    st.stop()

# --- タブ ---
tab1, tab2, tab3 = st.tabs(["KPIサマリー", "学科・選考分析", "申込明細データ"])

# === タブ1: KPIサマリー ===
with tab1:
    st.subheader("KPI サマリー")

    total = len(df_filtered)
    pass_count = int(df_filtered["is_enrolled"].sum())
    pass_rate = pass_count / total * 100 if total > 0 else 0
    avg_score = df_filtered["score"].mean()
    interview_rate = (df_filtered["interview_flag"] == 1).sum() / total * 100 if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総申込数", f"{total} 件")
    col2.metric("合格率", f"{pass_rate:.1f} %")
    col3.metric("平均点", f"{avg_score:.1f} 点")
    col4.metric("面接実施率", f"{interview_rate:.1f} %")

    st.markdown("---")

    # 合格/不合格の内訳
    st.subheader("合否内訳")
    result_counts = df_filtered["result"].value_counts().reset_index()
    result_counts.columns = ["合否", "件数"]
    st.dataframe(result_counts, use_container_width=False)

# === タブ2: 学科・選考分析 ===
with tab2:
    st.subheader("学科別合格率")

    dept_group = df_filtered.groupby("department").agg(
        申込数=("app_id", "count"),
        合格数=("is_enrolled", "sum"),
        平均点=("score", "mean"),
    ).reset_index()
    dept_group["合格率(%)"] = (dept_group["合格数"] / dept_group["申込数"] * 100).round(1)
    dept_group["平均点"] = dept_group["平均点"].round(1)
    dept_group = dept_group.sort_values("合格率(%)", ascending=False)

    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(dept_group["department"], dept_group["合格率(%)"], color="#4C72B0")
    ax1.set_xlabel("学科")
    ax1.set_ylabel("合格率(%)")
    ax1.set_ylim(0, 100)
    ax1.set_title("学科別合格率")
    for i, (_, row) in enumerate(dept_group.iterrows()):
        ax1.text(i, row["合格率(%)"] + 1, f"{row['合格率(%)']:.1f}%", ha="center", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close()

    st.dataframe(dept_group.reset_index(drop=True), use_container_width=True)

    st.subheader("選考方法別合格率")

    sel_group = df_filtered.groupby("selection_method").agg(
        申込数=("app_id", "count"),
        合格数=("is_enrolled", "sum"),
    ).reset_index()
    sel_group["合格率(%)"] = (sel_group["合格数"] / sel_group["申込数"] * 100).round(1)
    sel_group = sel_group.sort_values("合格率(%)", ascending=True)

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.barh(sel_group["selection_method"], sel_group["合格率(%)"], color="#DD8452")
    ax2.set_xlabel("合格率(%)")
    ax2.set_ylabel("選考方法")
    ax2.set_xlim(0, 100)
    ax2.set_title("選考方法別合格率")
    for i, (_, row) in enumerate(sel_group.iterrows()):
        ax2.text(row["合格率(%)"] + 1, i, f"{row['合格率(%)']:.1f}%", va="center", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

    st.dataframe(sel_group.reset_index(drop=True), use_container_width=True)

# === タブ3: 申込明細データ ===
with tab3:
    st.subheader("申込明細データ")
    st.caption(f"表示件数: {len(df_filtered)} 件（フィルター適用後）")

    display_cols = [
        "app_date", "app_id", "department", "selection_method",
        "region", "result", "score", "interview_flag", "score_grade", "source_file"
    ]
    available_cols = [c for c in display_cols if c in df_filtered.columns]
    st.dataframe(df_filtered[available_cols].reset_index(drop=True), use_container_width=True)

    csv_data = df_filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="CSVダウンロード",
        data=csv_data,
        file_name="filtered_applications.csv",
        mime="text/csv",
    )
