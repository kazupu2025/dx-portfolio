# -*- coding: utf-8 -*-
"""
C-59 農場スタッフ勤怠・作業効率分析パイプライン
Streamlit ダッシュボード
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'MS Gothic'
import streamlit as st

BASE_DIR = os.path.dirname(__file__)
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_farm_work_202401.csv")

st.set_page_config(
    page_title="農場スタッフ勤怠・作業効率分析ダッシュボード",
    page_icon=None,
    layout="wide",
)


@st.cache_data
def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    df["work_date"] = pd.to_datetime(
        df["work_date"].astype(str).str.replace("/", "-"),
        format="%Y-%m-%d",
        errors="coerce",
    )
    return df


df_all = load_data()

# --- Sidebar filters ---
st.sidebar.title("フィルター")

work_types = sorted(df_all["work_type"].dropna().unique().tolist())
selected_work_types = st.sidebar.multiselect("作業区分選択", work_types, default=work_types)

crops = sorted(df_all["crop"].dropna().unique().tolist())
selected_crops = st.sidebar.multiselect("作物選択", crops, default=crops)

df = df_all[
    df_all["work_type"].isin(selected_work_types) &
    df_all["crop"].isin(selected_crops)
].copy()

st.title("農場スタッフ勤怠・作業効率分析ダッシュボード (2024年1月)")

tab1, tab2, tab3 = st.tabs(["KPIサマリー", "作物・作業区分分析", "作業明細データ"])

# --- Tab 1: KPI ---
with tab1:
    st.subheader("KPIサマリー")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総記録数", len(df))
    with col2:
        met_rate = df["is_target_met"].mean() if len(df) > 0 else 0
        st.metric("目標達成率", f"{met_rate:.1%}")
    with col3:
        avg_prod = df["productivity"].mean() if len(df) > 0 else 0
        st.metric("平均生産性 (単位/時間)", f"{avg_prod:.2f}" if pd.notna(avg_prod) else "N/A")
    with col4:
        avg_hours = df["work_hours"].mean() if len(df) > 0 else 0
        st.metric("平均作業時間 (時間)", f"{avg_hours:.2f}" if pd.notna(avg_hours) else "N/A")

    st.divider()
    grade_counts = df["efficiency_grade"].value_counts().reindex(["高効率", "中効率", "低効率"], fill_value=0)
    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric("高効率件数", int(grade_counts.get("高効率", 0)))
    with col6:
        st.metric("中効率件数", int(grade_counts.get("中効率", 0)))
    with col7:
        st.metric("低効率件数", int(grade_counts.get("低効率", 0)))

# --- Tab 2: Charts ---
with tab2:
    st.subheader("作物別目標達成率")
    crop_grp = df.groupby("crop")["achievement_rate"].mean().sort_values(ascending=False)
    if not crop_grp.empty:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.bar(crop_grp.index, crop_grp.values, color="steelblue")
        ax1.set_xlabel("作物")
        ax1.set_ylabel("平均達成率")
        ax1.set_title("作物別目標達成率")
        ax1.set_ylim(0, 1.3)
        ax1.tick_params(axis='x', rotation=15)
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    st.subheader("作業区分別平均生産性")
    wt_grp = df.groupby("work_type")["productivity"].mean().sort_values()
    if not wt_grp.empty:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.barh(wt_grp.index, wt_grp.values, color="seagreen")
        ax2.set_xlabel("平均生産性 (単位/時間)")
        ax2.set_ylabel("作業区分")
        ax2.set_title("作業区分別平均生産性")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

# --- Tab 3: Detail data ---
with tab3:
    st.subheader("作業明細データ")
    st.write(f"表示件数: {len(df)}")
    display_cols = [
        "work_date", "record_id", "staff_id", "work_type", "crop",
        "work_hours", "target_qty", "actual_qty", "is_target_met",
        "achievement_rate", "productivity", "efficiency_grade",
    ]
    show_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[show_cols], use_container_width=True)
