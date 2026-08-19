# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_orders_202401.csv"


@st.cache_data
def load_automotive_repair_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


st.title("🚗 B-57 車両整備依頼・完了率分析ダッシュボード")

df_all = load_automotive_repair_data()

if df_all.empty:
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("フィルター")
    shops = ["全店舗"] + (sorted(df_all["shop_name"].unique().tolist()) if "shop_name" in df_all.columns else [])
    selected_shop = st.selectbox("店舗選択", shops)
    work_types = ["全作業区分"] + (sorted(df_all["work_type"].unique().tolist()) if "work_type" in df_all.columns else [])
    selected_wtype = st.selectbox("作業区分選択", work_types)

df = df_all.copy()
if "shop_name" in df.columns and selected_shop != "全店舗":
    df = df[df["shop_name"] == selected_shop]
if "work_type" in df.columns and selected_wtype != "全作業区分":
    df = df[df["work_type"] == selected_wtype]

if df.empty:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

tab1, tab2, tab3 = st.tabs(["KPIサマリー", "店舗・作業区分分析", "整備依頼明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    completed = (df["status"] == "完了").sum() if "status" in df.columns else 0
    avg_delay = df["delay_days"].mean() if "delay_days" in df.columns else 0.0
    returned_rate = df["is_returned"].mean() if "is_returned" in df.columns else 0.0
    total_rev = df["total_cost"].sum() if "total_cost" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("完了件数", f"{completed}件")
    c2.metric("平均遅延日数", f"{avg_delay:.2f}日")
    c3.metric("再入庫率", f"{returned_rate:.1%}")
    c4.metric("総売上", f"{total_rev:,.0f}円")

with tab2:
    st.subheader("店舗・作業区分分析")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**店舗別売上合計**")
        if "shop_name" in df.columns and "total_cost" in df.columns:
            shop_rev = df.groupby("shop_name")["total_cost"].sum().sort_values(ascending=False)
            st.bar_chart(shop_rev)
    with col2:
        st.markdown("**作業区分別平均遅延日数**")
        if "work_type" in df.columns and "delay_days" in df.columns:
            wtype_delay = df.groupby("work_type")["delay_days"].mean().sort_values(ascending=False)
            st.bar_chart(wtype_delay)

    st.markdown("**技術者別遅延率 上位10名**")
    if "tech_id" in df.columns and "is_delayed" in df.columns:
        tech_delay = df.groupby("tech_id")["is_delayed"].mean().sort_values(ascending=False).head(10)
        st.bar_chart(tech_delay)

with tab3:
    st.subheader("整備依頼明細データ")
    st.dataframe(df, use_container_width=True)
    st.caption(f"表示件数: {len(df)}件")
