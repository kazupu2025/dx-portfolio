# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'
import matplotlib.pyplot as plt
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_visits_202401.csv")

st.set_page_config(page_title="物件内見予約・成約率分析ダッシュボード", layout="wide")
st.title("物件内見予約・成約率分析ダッシュボード")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["is_contracted"] = pd.to_numeric(df["is_contracted"], errors="coerce")
    df["asking_price"] = pd.to_numeric(df["asking_price"], errors="coerce")
    df["days_to_contract"] = pd.to_numeric(df["days_to_contract"], errors="coerce")
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("フィルター")
all_types = sorted(df["property_type"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect("物件タイプ", all_types, default=all_types)
all_areas = sorted(df["area"].dropna().unique().tolist())
selected_areas = st.sidebar.multiselect("エリア", all_areas, default=all_areas)

filtered = df[
    df["property_type"].isin(selected_types) &
    df["area"].isin(selected_areas)
]

tab1, tab2, tab3 = st.tabs(["KPIサマリー", "物件・エリア分析", "内見明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    total_visits = len(filtered)
    contracted = filtered["is_contracted"].sum()
    conv_rate = contracted / total_visits if total_visits > 0 else 0
    avg_days = filtered.loc[filtered["is_contracted"] == 1, "days_to_contract"].mean()
    avg_price = filtered["asking_price"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総内見数", f"{total_visits:,} 件")
    col2.metric("成約率", f"{conv_rate:.1%}")
    col3.metric("平均成約日数", f"{avg_days:.1f} 日" if pd.notna(avg_days) else "N/A")
    col4.metric("平均物件価格", f"{avg_price:,.0f} 万円" if pd.notna(avg_price) else "N/A")

with tab2:
    st.subheader("物件タイプ別成約率")
    type_grp = filtered.groupby("property_type").agg(
        visit_count=("visit_id", "count"),
        contract_count=("is_contracted", "sum"),
    ).reset_index()
    type_grp["conversion_rate"] = type_grp["contract_count"] / type_grp["visit_count"]

    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.bar(type_grp["property_type"], type_grp["conversion_rate"], color="#4C72B0")
    ax1.set_title("物件タイプ別成約率")
    ax1.set_xlabel("物件タイプ")
    ax1.set_ylabel("成約率")
    ax1.set_ylim(0, 1)
    st.pyplot(fig1)
    plt.close()

    st.subheader("エリア別内見件数")
    area_grp = filtered.groupby("area").agg(visit_count=("visit_id", "count")).reset_index()
    area_grp = area_grp.sort_values("visit_count", ascending=True)
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.barh(area_grp["area"], area_grp["visit_count"], color="#55A868")
    ax2.set_title("エリア別内見件数")
    ax2.set_xlabel("件数")
    st.pyplot(fig2)
    plt.close()

with tab3:
    st.subheader("内見明細データ")
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)
    st.caption(f"表示件数: {len(filtered):,} 件")
