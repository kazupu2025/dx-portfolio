# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = 'MS Gothic'
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "output", "cleaned_orders_202401.csv")

st.set_page_config(page_title="車両整備依頼・完了率分析ダッシュボード", layout="wide")
st.title("車両整備依頼・完了率分析ダッシュボード")

@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")

df_all = load_data()

# Sidebar filters
st.sidebar.header("フィルター")
shops = ["全店舗"] + sorted(df_all["shop_name"].unique().tolist())
selected_shop = st.sidebar.selectbox("店舗選択", shops)
work_types = ["全作業区分"] + sorted(df_all["work_type"].unique().tolist())
selected_wtype = st.sidebar.selectbox("作業区分選択", work_types)

df = df_all.copy()
if selected_shop != "全店舗":
    df = df[df["shop_name"] == selected_shop]
if selected_wtype != "全作業区分":
    df = df[df["work_type"] == selected_wtype]

tab1, tab2, tab3 = st.tabs(["KPIサマリー", "店舗・作業区分分析", "整備依頼明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    if len(df) == 0:
        st.warning("データがありません")
    else:
        completed = (df["status"] == "完了").sum()
        avg_delay = df["delay_days"].mean()
        returned_rate = df["is_returned"].mean()
        total_rev = df["total_cost"].sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("完了件数", f"{completed}件")
        c2.metric("平均遅延日数", f"{avg_delay:.2f}日")
        c3.metric("再入庫率", f"{returned_rate:.1%}")
        c4.metric("総売上", f"{total_rev:,.0f}円")

with tab2:
    st.subheader("店舗・作業区分分析")
    if len(df) == 0:
        st.warning("データがありません")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**店舗別売上合計**")
            shop_rev = df.groupby("shop_name")["total_cost"].sum().sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(shop_rev.index, shop_rev.values, color=["#2196F3", "#FF9800", "#4CAF50"])
            ax.set_title("店舗別売上合計")
            ax.set_ylabel("売上（円）")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        with col2:
            st.markdown("**作業区分別平均遅延日数**")
            wtype_delay = df.groupby("work_type")["delay_days"].mean().sort_values()
            fig, ax = plt.subplots(figsize=(6, 4))
            colors = ["#4CAF50" if v <= 0 else "#F44336" for v in wtype_delay.values]
            ax.barh(wtype_delay.index, wtype_delay.values, color=colors)
            ax.set_title("作業区分別平均遅延日数")
            ax.set_xlabel("平均遅延日数（日）")
            ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        st.markdown("**技術者別遅延率**")
        tech_delay = df.groupby("tech_id")["is_delayed"].mean().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(tech_delay.index, tech_delay.values, color="#FF5722")
        ax.set_title("技術者別遅延率 上位10名")
        ax.set_ylabel("遅延率")
        ax.set_ylim(0, 1)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

with tab3:
    st.subheader("整備依頼明細データ")
    st.dataframe(df, use_container_width=True)
    st.caption(f"表示件数: {len(df)}件")
