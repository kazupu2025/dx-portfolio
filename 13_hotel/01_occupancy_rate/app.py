# -*- coding: utf-8 -*-
import os
import streamlit as st
import pandas as pd
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_reservations_202401.csv")

st.set_page_config(page_title="宿泊予約・稼働率分析ダッシュボード", layout="wide")
st.title("宿泊予約・稼働率分析ダッシュボード")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["checkin_date"] = pd.to_datetime(df["checkin_date"])
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("フィルタ")
room_types = ["すべて"] + sorted(df["room_type"].unique().tolist())
selected_room = st.sidebar.selectbox("客室タイプ", room_types)

statuses = ["すべて"] + sorted(df["status"].unique().tolist())
selected_status = st.sidebar.selectbox("ステータス", statuses)

filtered = df.copy()
if selected_room != "すべて":
    filtered = filtered[filtered["room_type"] == selected_room]
if selected_status != "すべて":
    filtered = filtered[filtered["status"] == selected_status]

tab1, tab2, tab3 = st.tabs(["稼働サマリー", "客室タイプ分析", "予約明細データ"])

with tab1:
    st.subheader("KPI サマリー")
    total_rev = filtered["total_revenue"].sum()
    stayed = (filtered["status"] == "宿泊済み").sum()
    total = len(filtered)
    occ_rate = stayed / total if total > 0 else 0.0
    cancel_count = filtered["is_cancel"].sum()
    cancel_rate = cancel_count / total if total > 0 else 0.0
    loss_rev = filtered["loss_revenue"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総売上", "{:,.0f} 円".format(total_rev))
    col2.metric("稼働率", "{:.1%}".format(occ_rate))
    col3.metric("キャンセル率", "{:.1%}".format(cancel_rate))
    col4.metric("損失金額", "{:,.0f} 円".format(loss_rev))

    st.markdown("---")
    st.subheader("ステータス内訳")
    status_counts = filtered["status"].value_counts().reset_index()
    status_counts.columns = ["ステータス", "件数"]
    st.dataframe(status_counts, use_container_width=True)

with tab2:
    st.subheader("客室タイプ別グラフ")
    rev_img = os.path.join(CHARTS_DIR, "bar_roomtype_revenue.png")
    cancel_img = os.path.join(CHARTS_DIR, "bar_roomtype_cancel_rate.png")
    occ_img = os.path.join(CHARTS_DIR, "line_daily_occupancy.png")

    col1, col2 = st.columns(2)
    if os.path.exists(rev_img):
        with col1:
            st.image(rev_img, caption="客室タイプ別総売上", use_container_width=True)
    if os.path.exists(cancel_img):
        with col2:
            st.image(cancel_img, caption="客室タイプ別キャンセル率", use_container_width=True)

    if os.path.exists(occ_img):
        st.image(occ_img, caption="日別稼働率推移", use_container_width=True)

with tab3:
    st.subheader("予約明細データ")
    st.info("表示件数: {} 件".format(len(filtered)))
    display_cols = ["checkin_date", "reserv_no", "room_type", "guest_count",
                    "nights", "room_rate", "status", "total_revenue", "source_file"]
    st.dataframe(filtered[display_cols].reset_index(drop=True), use_container_width=True)
    csv_data = filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("CSVダウンロード", data=csv_data,
                       file_name="filtered_reservations.csv", mime="text/csv")
