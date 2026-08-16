"""
B-22 飲食 店舗別損益・P/L管理ダッシュボード（Streamlit）
起動: cd 06_restaurant/05_pl_management && streamlit run app.py
"""

import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

INPUT_FILE = OUTPUT_DIR / "cleaned_pl_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    for col in ["revenue", "food_cost", "labor_cost", "other_cost",
                "total_cost", "gross_profit", "food_cost_rate",
                "labor_cost_rate", "profit_margin"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["record_date"] = pd.to_datetime(df["record_date"], format="%Y-%m-%d", errors="coerce")
    return df


st.title("🍜 B-22 飲食 店舗別損益・P/L管理ダッシュボード")
st.caption("B-22 | 2024年1月 | 店舗別売上・原価率・利益率 P/L管理")

if not INPUT_FILE.exists():
    st.error(f"データファイルが見つかりません: {INPUT_FILE}")
    st.info("先に cleanse.py を実行してください。")
    st.stop()

df_all = load_data()

# サイドバー: 店舗選択
with st.sidebar:
    st.header("🔍 フィルター")
    stores = sorted(df_all["store_name"].dropna().unique().tolist())
    selected_stores = st.multiselect("店舗を選択", options=stores, default=stores)

if not selected_stores:
    st.warning("店舗を1つ以上選択してください。")
    st.stop()

df = df_all[df_all["store_name"].isin(selected_stores)].copy()

# -------------------------------------------------------------------
# KPI メトリクス
# -------------------------------------------------------------------
total_rev = df["revenue"].sum()
total_gp  = df["gross_profit"].sum()
avg_fcr   = df["food_cost_rate"].mean() * 100
avg_margin = df["profit_margin"].mean() * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("総売上", f"{total_rev:,.0f} 円")
col2.metric("総粗利", f"{total_gp:,.0f} 円")
col3.metric("平均食材費率", f"{avg_fcr:.1f}%")
col4.metric("平均利益率", f"{avg_margin:.1f}%")

st.divider()

# -------------------------------------------------------------------
# タブ
# -------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 損益サマリー", "📈 店舗別損益分析", "📋 日次P/L明細"])

with tab1:
    st.subheader("店舗別 損益フラグ集計")
    flag_counts = df["pl_flag"].value_counts().reset_index()
    flag_counts.columns = ["損益フラグ", "件数"]
    st.dataframe(flag_counts, use_container_width=True)

    st.subheader("店舗別 損益サマリーテーブル")
    summary = df.groupby("store_name", as_index=False).agg(
        総売上=("revenue", "sum"),
        総粗利=("gross_profit", "sum"),
        平均食材費率=("food_cost_rate", "mean"),
        平均人件費率=("labor_cost_rate", "mean"),
        平均利益率=("profit_margin", "mean"),
    )
    summary["平均食材費率"] = (summary["平均食材費率"] * 100).round(2).astype(str) + "%"
    summary["平均人件費率"] = (summary["平均人件費率"] * 100).round(2).astype(str) + "%"
    summary["平均利益率"]   = (summary["平均利益率"] * 100).round(2).astype(str) + "%"
    st.dataframe(summary, use_container_width=True)

with tab2:
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("店舗別 売上")
        chart_rev = CHARTS_DIR / "bar_store_revenue.png"
        if chart_rev.exists():
            st.image(str(chart_rev), use_container_width=True)
        else:
            st.warning("グラフが見つかりません。")
    with col_right:
        st.subheader("店舗別 利益率")
        chart_margin = CHARTS_DIR / "bar_store_margin.png"
        if chart_margin.exists():
            st.image(str(chart_margin), use_container_width=True)
        else:
            st.warning("グラフが見つかりません。")

    st.subheader("店舗別 コスト内訳")
    chart_cost = CHARTS_DIR / "bar_cost_breakdown.png"
    if chart_cost.exists():
        st.image(str(chart_cost), use_container_width=True)
    else:
        st.warning("グラフが見つかりません。")

with tab3:
    st.subheader("日次P/L明細データ")
    display_df = df[[
        "record_date", "record_id", "store_name",
        "revenue", "food_cost", "labor_cost", "other_cost",
        "total_cost", "gross_profit", "profit_margin", "pl_flag"
    ]].copy()
    display_df["record_date"] = display_df["record_date"].dt.strftime("%Y-%m-%d")
    display_df = display_df.sort_values(["record_date", "store_name"]).reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)

st.divider()

# -------------------------------------------------------------------
# 分析レポート
# -------------------------------------------------------------------
if REPORT_PATH.exists():
    with st.expander("📄 分析レポートを表示", expanded=False):
        st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
