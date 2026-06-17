# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="工程進捗・作業員稼働KPIダッシュボード", layout="wide")
st.title("工程進捗・作業員稼働KPIダッシュボード")

FPATH = "output/cleaned_progress_202401.csv"

@st.cache_data
def load_data():
    return pd.read_csv(FPATH, encoding="utf-8-sig")

if not os.path.exists(FPATH):
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

df = load_data()

# Sidebar filters
st.sidebar.header("フィルター")
sites = ["すべて"] + sorted(df["site_name"].unique().tolist())
selected_site = st.sidebar.selectbox("現場選択", sites)

processes = ["すべて"] + sorted(df["process"].unique().tolist())
selected_process = st.sidebar.selectbox("工程選択", processes)

# Apply filters
filtered = df.copy()
if selected_site != "すべて":
    filtered = filtered[filtered["site_name"] == selected_site]
if selected_process != "すべて":
    filtered = filtered[filtered["process"] == selected_process]

# Tabs
tab1, tab2, tab3 = st.tabs(["進捗サマリー", "現場・工程分析", "作業員データ詳細"])

with tab1:
    st.subheader("KPIカード")
    col1, col2, col3 = st.columns(3)
    col1.metric("平均進捗率 (%)", f"{filtered['progress_pct'].mean():.1f}")
    col2.metric("遅延件数", int(filtered["is_delayed"].sum()))
    col3.metric("不具合合計", int(filtered["defect_count"].sum()))

with tab2:
    st.subheader("現場・工程分析")
    chart_dir = "output/charts"
    charts = {
        "現場別 平均進捗率": f"{chart_dir}/bar_site_progress.png",
        "工程別 平均稼働効率": f"{chart_dir}/bar_process_efficiency.png",
        "現場別 不具合件数": f"{chart_dir}/bar_site_defect.png",
    }
    for title, path in charts.items():
        if os.path.exists(path):
            st.image(path, caption=title, use_container_width=True)
        else:
            st.warning(f"{title}: グラフファイルが見つかりません ({path})")

with tab3:
    st.subheader("作業員データ詳細")
    worker_summary = filtered.groupby("worker_id").agg(
        累積稼働時間=("actual_hours", "sum"),
        平均進捗率=("progress_pct", "mean"),
        不具合合計=("defect_count", "sum")
    ).reset_index()
    worker_summary["平均進捗率"] = worker_summary["平均進捗率"].round(1)
    worker_summary["累積稼働時間"] = worker_summary["累積稼働時間"].round(1)
    st.dataframe(worker_summary, use_container_width=True)
