# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")

st.set_page_config(page_title="シフト充足率・人件費最適化レポート", layout="wide")
st.title("シフト充足率・人件費最適化レポート")

CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_shift_202401.csv")
if not os.path.exists(CSV_PATH):
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# Sidebar: store filter
stores = ["全店"] + sorted(df["store_name"].unique().tolist())
selected_store = st.sidebar.selectbox("店舗選択", stores)

if selected_store != "全店":
    df_filtered = df[df["store_name"] == selected_store].copy()
else:
    df_filtered = df.copy()

tab1, tab2, tab3 = st.tabs(["サマリー", "店舗別分析", "データ詳細"])

with tab1:
    st.subheader("KPI サマリー")
    total_cost = int(df_filtered["daily_wage"].sum())
    understaffed_count = int(df_filtered["is_understaffed"].sum())
    avg_fill_rate = (df_filtered["actual_staff"] / df_filtered["required_staff"]).mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("総人件費", f"{total_cost:,} 円")
    col2.metric("不足シフト件数", f"{understaffed_count} 件")
    col3.metric("平均充足率", f"{avg_fill_rate:.3f}")

with tab2:
    st.subheader("店舗別分析グラフ")
    chart_files = {
        "店舗別総人件費": "bar_store_labor_cost.png",
        "役割別平均時給": "bar_role_avg_wage.png",
        "店舗別平均シフトギャップ": "bar_store_gap.png",
    }
    for title, fname in chart_files.items():
        fpath = os.path.join(CHARTS_DIR, fname)
        if os.path.exists(fpath):
            st.write(f"### {title}")
            img = Image.open(fpath)
            st.image(img, use_container_width=True)
        else:
            st.warning(f"{fname} が見つかりません。visualize.py を実行してください。")

with tab3:
    st.subheader("データ詳細")
    role_filter = st.multiselect("役割フィルタ", options=sorted(df["role"].unique().tolist()), default=sorted(df["role"].unique().tolist()))
    df_display = df_filtered[df_filtered["role"].isin(role_filter)] if role_filter else df_filtered
    st.dataframe(df_display, use_container_width=True, height=400)
    st.caption(f"表示行数: {len(df_display):,} 行")
