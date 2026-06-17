# -*- coding: utf-8 -*-
"""
C-45: サービス別売上・原価レポート
Streamlit アプリ
"""

import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")

st.set_page_config(page_title="サービス別売上・原価レポート", layout="wide")
st.title("サービス別売上・原価レポート")


@st.cache_data
def load_data():
    path = os.path.join(OUTPUT_DIR, "cleaned_revenue_202401.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df["gross_profit"] = pd.to_numeric(df["gross_profit"], errors="coerce")
    df["gross_margin"] = pd.to_numeric(df["gross_margin"], errors="coerce")
    return df


df_all = load_data()

# --- サイドバーフィルタ ---
st.sidebar.header("フィルタ")
all_categories = sorted(df_all["category"].dropna().unique().tolist())
selected_cats = st.sidebar.multiselect("カテゴリ", all_categories, default=all_categories)

all_services = sorted(df_all["service_name"].dropna().unique().tolist())
selected_svcs = st.sidebar.multiselect("サービス", all_services, default=all_services)

df = df_all[
    df_all["category"].isin(selected_cats) &
    df_all["service_name"].isin(selected_svcs)
]

# --- タブ ---
tab1, tab2, tab3 = st.tabs(["収益サマリー", "サービス別分析", "明細データ"])

with tab1:
    st.subheader("KPI カード")
    total_rev = df["revenue"].sum()
    total_gross = df["gross_profit"].sum()
    avg_margin = df["gross_margin"].mean()
    deficit_count = (df["profit_flag"] == "赤字").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総売上", f"{total_rev:,.0f} 円")
    c2.metric("総粗利", f"{total_gross:,.0f} 円")
    c3.metric("平均粗利率", f"{avg_margin:.1%}")
    c4.metric("赤字レコード数", f"{deficit_count:,}")

with tab2:
    st.subheader("サービス別グラフ")
    for fname, title in [
        ("bar_service_revenue.png", "売上・原価"),
        ("bar_service_margin.png", "粗利率"),
        ("bar_category_profit.png", "カテゴリ別粗利"),
    ]:
        path = os.path.join(CHARTS_DIR, fname)
        if os.path.exists(path):
            st.image(path, caption=title, use_container_width=True)
        else:
            st.warning(f"グラフが見つかりません: {fname}")

with tab3:
    st.subheader("明細データ")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
    st.caption(f"表示件数: {len(df):,} 件")
