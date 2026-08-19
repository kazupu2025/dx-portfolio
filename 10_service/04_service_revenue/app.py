# -*- coding: utf-8 -*-
"""
B-54: サービス別売上・原価レポート
Streamlit アプリ
"""

import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_revenue_202401.csv"


@st.cache_data
def load_service_revenue_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    for col in ["revenue", "cost", "gross_profit", "gross_margin"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("⚙️ B-54 サービス別売上・原価レポート")

df_all = load_service_revenue_data()

if df_all.empty:
    st.error("データファイルが見つかりません。パイプラインを先に実行してください。")
    st.stop()

# --- サイドバーフィルタ ---
with st.sidebar:
    st.header("フィルタ")
    all_categories = sorted(df_all["category"].dropna().unique().tolist()) if "category" in df_all.columns else []
    selected_cats = st.multiselect("カテゴリ", all_categories, default=all_categories)

    all_services = sorted(df_all["service_name"].dropna().unique().tolist()) if "service_name" in df_all.columns else []
    selected_svcs = st.multiselect("サービス", all_services, default=all_services)

mask = pd.Series([True] * len(df_all), index=df_all.index)
if "category" in df_all.columns and selected_cats:
    mask &= df_all["category"].isin(selected_cats)
if "service_name" in df_all.columns and selected_svcs:
    mask &= df_all["service_name"].isin(selected_svcs)
df = df_all[mask].copy()

if df.empty:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

# --- タブ ---
tab1, tab2, tab3 = st.tabs(["収益サマリー", "サービス別分析", "明細データ"])

with tab1:
    st.subheader("KPI カード")
    total_rev = df["revenue"].sum() if "revenue" in df.columns else 0
    total_gross = df["gross_profit"].sum() if "gross_profit" in df.columns else 0
    avg_margin = df["gross_margin"].mean() if "gross_margin" in df.columns else 0.0
    deficit_count = (df["profit_flag"] == "赤字").sum() if "profit_flag" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総売上", f"{total_rev:,.0f} 円")
    c2.metric("総粗利", f"{total_gross:,.0f} 円")
    c3.metric("平均粗利率", f"{avg_margin:.1%}")
    c4.metric("赤字レコード数", f"{deficit_count:,}")

with tab2:
    st.subheader("サービス別分析")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**サービス別 売上**")
        if "service_name" in df.columns and "revenue" in df.columns:
            svc_rev = df.groupby("service_name")["revenue"].sum().sort_values(ascending=False)
            st.bar_chart(svc_rev)
    with col_right:
        st.markdown("**サービス別 粗利率**")
        if "service_name" in df.columns and "gross_margin" in df.columns:
            svc_margin = (df.groupby("service_name")["gross_margin"].mean() * 100).round(1)
            st.bar_chart(svc_margin)

    st.markdown("**カテゴリ別 粗利**")
    if "category" in df.columns and "gross_profit" in df.columns:
        cat_profit = df.groupby("category")["gross_profit"].sum().sort_values(ascending=False)
        st.bar_chart(cat_profit)

with tab3:
    st.subheader("明細データ")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
    st.caption(f"表示件数: {len(df):,} 件")
