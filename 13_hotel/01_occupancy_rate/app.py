# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_reservations_202401.csv"


@st.cache_data
def load_hotel_occupancy_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    if "checkin_date" in df.columns:
        df["checkin_date"] = pd.to_datetime(df["checkin_date"], errors="coerce")
    return df


st.title("🏨 B-53 宿泊予約・稼働率分析ダッシュボード")

df_all = load_hotel_occupancy_data()

if df_all.empty:
    st.error("データファイルが見つかりません。パイプラインを先に実行してください。")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("フィルタ")
    room_types = ["すべて"] + (sorted(df_all["room_type"].unique().tolist()) if "room_type" in df_all.columns else [])
    selected_room = st.selectbox("客室タイプ", room_types)

    statuses = ["すべて"] + (sorted(df_all["status"].unique().tolist()) if "status" in df_all.columns else [])
    selected_status = st.selectbox("ステータス", statuses)

filtered = df_all.copy()
if "room_type" in filtered.columns and selected_room != "すべて":
    filtered = filtered[filtered["room_type"] == selected_room]
if "status" in filtered.columns and selected_status != "すべて":
    filtered = filtered[filtered["status"] == selected_status]

tab1, tab2, tab3 = st.tabs(["稼働サマリー", "客室タイプ分析", "予約明細データ"])

with tab1:
    st.subheader("KPI サマリー")
    total = len(filtered)
    total_rev = filtered["total_revenue"].sum() if "total_revenue" in filtered.columns else 0
    stayed = (filtered["status"] == "宿泊済み").sum() if "status" in filtered.columns else 0
    occ_rate = stayed / total if total > 0 else 0.0
    cancel_count = filtered["is_cancel"].sum() if "is_cancel" in filtered.columns else 0
    cancel_rate = cancel_count / total if total > 0 else 0.0
    loss_rev = filtered["loss_revenue"].sum() if "loss_revenue" in filtered.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総売上", f"{total_rev:,.0f} 円")
    col2.metric("稼働率", f"{occ_rate:.1%}")
    col3.metric("キャンセル率", f"{cancel_rate:.1%}")
    col4.metric("損失金額", f"{loss_rev:,.0f} 円")

    st.markdown("---")
    st.subheader("ステータス内訳")
    if "status" in filtered.columns:
        status_counts = filtered["status"].value_counts()
        st.bar_chart(status_counts)

with tab2:
    st.subheader("客室タイプ別分析")
    if "room_type" in filtered.columns:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**客室タイプ別 総売上**")
            if "total_revenue" in filtered.columns:
                rev_by_type = filtered.groupby("room_type")["total_revenue"].sum().sort_values(ascending=False)
                st.bar_chart(rev_by_type)
        with col2:
            st.markdown("**客室タイプ別 キャンセル率**")
            if "is_cancel" in filtered.columns:
                cancel_by_type = filtered.groupby("room_type")["is_cancel"].mean() * 100
                st.bar_chart(cancel_by_type)

        st.markdown("**客室タイプ別 件数推移**")
        if "checkin_date" in filtered.columns:
            daily = filtered.groupby(filtered["checkin_date"].dt.date)["room_type"].count()
            st.bar_chart(daily)

with tab3:
    st.subheader("予約明細データ")
    st.info(f"表示件数: {len(filtered):,} 件")
    display_cols = ["checkin_date", "reserv_no", "room_type", "guest_count",
                    "nights", "room_rate", "status", "total_revenue", "source_file"]
    show_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[show_cols].reset_index(drop=True) if show_cols else filtered, use_container_width=True)
    csv_data = filtered.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("CSVダウンロード", data=csv_data,
                       file_name="filtered_reservations.csv", mime="text/csv")
