# -*- coding: utf-8 -*-
"""
B-67: 飲食 店舗別損益・P/L管理ダッシュボード
Streamlit ダッシュボード
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

INPUT_FILE = OUTPUT_DIR / "cleaned_pl_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_restaurant_pl_data() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    for col in ["revenue", "food_cost", "labor_cost", "other_cost",
                "total_cost", "gross_profit", "food_cost_rate",
                "labor_cost_rate", "profit_margin"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "record_date" in df.columns:
        df["record_date"] = pd.to_datetime(df["record_date"], format="%Y-%m-%d", errors="coerce")
    return df


st.title("🍜 B-67 飲食 店舗別損益・P/L管理ダッシュボード")
st.caption("B-67 | 2024年1月 | 店舗別売上・原価率・利益率 P/L管理")

df_all = load_restaurant_pl_data()

if df_all.empty:
    st.error(f"データファイルが見つかりません: {INPUT_FILE}")
    st.info("先に cleanse.py を実行してください。")
    st.stop()

# サイドバー: 店舗選択
with st.sidebar:
    st.header("🔍 フィルター")
    stores = sorted(df_all["store_name"].dropna().unique().tolist()) if "store_name" in df_all.columns else []
    selected_stores = st.multiselect("店舗を選択", options=stores, default=stores)

if not selected_stores:
    st.warning("店舗を1つ以上選択してください。")
    st.stop()

df = df_all[df_all["store_name"].isin(selected_stores)].copy()

# KPI
total_rev = df["revenue"].sum() if "revenue" in df.columns else 0
total_gp = df["gross_profit"].sum() if "gross_profit" in df.columns else 0
avg_fcr = df["food_cost_rate"].mean() * 100 if "food_cost_rate" in df.columns else 0
avg_margin = df["profit_margin"].mean() * 100 if "profit_margin" in df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("総売上", f"{total_rev:,.0f} 円")
col2.metric("総粗利", f"{total_gp:,.0f} 円")
col3.metric("平均食材費率", f"{avg_fcr:.1f}%")
col4.metric("平均利益率", f"{avg_margin:.1f}%")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 損益サマリー", "📈 店舗別損益分析", "📋 日次P/L明細"])

with tab1:
    if "pl_flag" in df.columns:
        st.subheader("店舗別 損益フラグ集計")
        flag_counts = df["pl_flag"].value_counts().reset_index()
        flag_counts.columns = ["損益フラグ", "件数"]
        st.dataframe(flag_counts, use_container_width=True)

    st.subheader("店舗別 損益サマリーテーブル")
    _agg = {"総売上": ("revenue", "sum")}
    if "gross_profit" in df.columns:
        _agg["総粗利"] = ("gross_profit", "sum")
    if "food_cost_rate" in df.columns:
        _agg["平均食材費率"] = ("food_cost_rate", "mean")
    if "labor_cost_rate" in df.columns:
        _agg["平均人件費率"] = ("labor_cost_rate", "mean")
    if "profit_margin" in df.columns:
        _agg["平均利益率"] = ("profit_margin", "mean")
    summary = df.groupby("store_name", as_index=False).agg(**_agg)
    for col in ["平均食材費率", "平均人件費率", "平均利益率"]:
        if col in summary.columns:
            summary[col] = (summary[col] * 100).round(2).astype(str) + "%"
    st.dataframe(summary, use_container_width=True)

with tab2:
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("店舗別 売上")
        if "store_name" in df.columns and "revenue" in df.columns:
            store_rev = df.groupby("store_name")["revenue"].sum().sort_values(ascending=True)
            st.bar_chart(store_rev)
    with col_right:
        st.subheader("店舗別 利益率")
        if "store_name" in df.columns and "profit_margin" in df.columns:
            store_margin = (df.groupby("store_name")["profit_margin"].mean() * 100).sort_values(ascending=True)
            st.bar_chart(store_margin)

    st.subheader("店舗別 コスト内訳")
    _cost_cols = [c for c in ["food_cost", "labor_cost", "other_cost"] if c in df.columns]
    if "store_name" in df.columns and _cost_cols:
        cost_breakdown = df.groupby("store_name")[_cost_cols].sum()
        cost_breakdown.columns = [c.replace("_cost", "コスト") for c in _cost_cols]
        st.bar_chart(cost_breakdown)

with tab3:
    st.subheader("日次P/L明細データ")
    _disp_cols = ["record_date", "record_id", "store_name", "revenue", "food_cost",
                  "labor_cost", "other_cost", "total_cost", "gross_profit", "profit_margin", "pl_flag"]
    _avail = [c for c in _disp_cols if c in df.columns]
    display_df = df[_avail].copy()
    if "record_date" in display_df.columns:
        display_df["record_date"] = display_df["record_date"].dt.strftime("%Y-%m-%d")
    if "store_name" in display_df.columns and "record_date" in display_df.columns:
        display_df = display_df.sort_values(["record_date", "store_name"]).reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)

st.divider()

if REPORT_PATH.exists():
    with st.expander("📄 分析レポートを表示", expanded=False):
        st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
