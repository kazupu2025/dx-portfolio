# -*- coding: utf-8 -*-
"""
C-49 作物収量・品質検査レポートパイプライン
Streamlit アプリ
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'MS Gothic'
import streamlit as st

BASE_DIR = os.path.dirname(__file__)
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_harvest_202401.csv")

st.set_page_config(
    page_title="作物収量・品質検査レポート",
    page_icon=None,
    layout="wide",
)


@st.cache_data
def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    df["harvest_date"] = pd.to_datetime(
        df["harvest_date"].astype(str).str.replace("/", "-"),
        format="%Y-%m-%d",
        errors="coerce",
    )
    return df


df_all = load_data()

# --- Sidebar filters ---
st.sidebar.title("フィルター")
farms = sorted(df_all["farm_name"].dropna().unique().tolist())
selected_farms = st.sidebar.multiselect("農場選択", farms, default=farms)

crops = sorted(df_all["crop"].dropna().unique().tolist())
selected_crops = st.sidebar.multiselect("作物選択", crops, default=crops)

df = df_all[
    df_all["farm_name"].isin(selected_farms) &
    df_all["crop"].isin(selected_crops)
].copy()

st.title("作物収量・品質検査レポート (2024年1月)")

tab1, tab2, tab3 = st.tabs(["KPIサマリー", "農場・作物分析", "検査明細データ"])

# --- Tab 1: KPI ---
with tab1:
    st.subheader("KPIサマリー")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総収穫量 (kg)", f"{df['harvest_qty'].sum():,.1f}")
    with col2:
        avg_rate = df["grade_a_rate"].mean()
        st.metric("平均A等級率", f"{avg_rate:.1%}" if pd.notna(avg_rate) else "N/A")
    with col3:
        kaizen = int((df["quality_flag"] == "要改善").sum())
        st.metric("要改善件数", kaizen)

    st.divider()
    flag_counts = df["quality_flag"].value_counts().reindex(["優良", "合格", "要改善"], fill_value=0)
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("優良件数", int(flag_counts.get("優良", 0)))
    with col5:
        st.metric("合格件数", int(flag_counts.get("合格", 0)))
    with col6:
        st.metric("要改善件数", int(flag_counts.get("要改善", 0)))

# --- Tab 2: Charts ---
with tab2:
    st.subheader("農場別収穫量")
    farm_grp = df.groupby("farm_name")["harvest_qty"].sum().sort_values(ascending=False)
    if not farm_grp.empty:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.bar(farm_grp.index, farm_grp.values, color="steelblue")
        ax1.set_xlabel("農場名")
        ax1.set_ylabel("収穫量 (kg)")
        ax1.set_title("農場別収穫量合計")
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    st.subheader("作物別平均A等級率")
    crop_grp = df.groupby("crop")["grade_a_rate"].mean().sort_values()
    if not crop_grp.empty:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.barh(crop_grp.index, crop_grp.values, color="seagreen")
        ax2.set_xlabel("平均A等級率")
        ax2.set_ylabel("作物")
        ax2.set_title("作物別平均A等級率")
        ax2.set_xlim(0, 1)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    st.subheader("品質フラグ分布")
    flag_dist = df["quality_flag"].value_counts().reindex(["優良", "合格", "要改善"], fill_value=0)
    if not flag_dist.empty:
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        ax3.bar(flag_dist.index, flag_dist.values, color=["#2ecc71", "#f39c12", "#e74c3c"])
        ax3.set_xlabel("品質フラグ")
        ax3.set_ylabel("件数")
        ax3.set_title("品質フラグ分布")
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

# --- Tab 3: Detail data ---
with tab3:
    st.subheader("検査明細データ")
    st.write(f"表示件数: {len(df)}")
    display_cols = [
        "harvest_date", "record_id", "farm_name", "crop",
        "harvest_qty", "grade_a_qty", "defect_qty",
        "grade_a_rate", "defect_rate", "quality_flag", "inspector_id",
    ]
    show_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[show_cols], use_container_width=True)
