# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")

st.set_page_config(page_title="荷役作業員KPI集計ダッシュボード", layout="wide")
st.title("荷役作業員KPI集計ダッシュボード")

CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_worker_kpi_202401.csv")

if not os.path.exists(CSV_PATH):
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# Sidebar filters
st.sidebar.header("フィルター")
zones = sorted(df["zone"].dropna().unique().tolist())
selected_zones = st.sidebar.multiselect("ゾーン選択", zones, default=zones)
tasks = sorted(df["task_type"].dropna().unique().tolist())
selected_tasks = st.sidebar.multiselect("作業区分選択", tasks, default=tasks)

filtered = df[df["zone"].isin(selected_zones) & df["task_type"].isin(selected_tasks)]

tab1, tab2, tab3 = st.tabs(["KPIサマリー", "ゾーン・作業区分分析", "作業員別データ詳細"])

with tab1:
    st.subheader("KPIサマリー")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総処理件数", f"{int(filtered['processed_qty'].sum()):,}")
    with col2:
        avg_err = filtered["error_rate"].mean()
        st.metric("平均エラー率", f"{avg_err:.2%}" if pd.notna(avg_err) else "N/A")
    with col3:
        excellent = filtered[filtered["kpi_flag"] == "優秀"]["worker_id"].nunique()
        st.metric("優秀作業員数", f"{excellent} 名")

with tab2:
    st.subheader("ゾーン・作業区分分析")
    c1, c2 = st.columns(2)
    with c1:
        img1 = os.path.join(CHARTS_DIR, "bar_zone_processed.png")
        if os.path.exists(img1):
            st.image(Image.open(img1), caption="ゾーン別処理件数", use_container_width=True)
        else:
            st.warning("グラフが見つかりません。visualize.py を実行してください。")
    with c2:
        img2 = os.path.join(CHARTS_DIR, "bar_task_throughput.png")
        if os.path.exists(img2):
            st.image(Image.open(img2), caption="作業区分別平均スループット", use_container_width=True)
        else:
            st.warning("グラフが見つかりません。visualize.py を実行してください。")

    img3 = os.path.join(CHARTS_DIR, "bar_worker_error_top10.png")
    if os.path.exists(img3):
        st.image(Image.open(img3), caption="エラー率上位10作業員", use_container_width=True)

with tab3:
    st.subheader("作業員別データ詳細")
    worker_detail = filtered.groupby("worker_id").agg(
        avg_throughput=("throughput", "mean"),
        avg_error_rate=("error_rate", "mean"),
        total_processed=("processed_qty", "sum"),
        kpi_flag=("kpi_flag", lambda x: x.value_counts().index[0]),
    ).reset_index()
    worker_detail["avg_throughput"] = worker_detail["avg_throughput"].round(2)
    worker_detail["avg_error_rate"] = worker_detail["avg_error_rate"].round(4)
    st.dataframe(worker_detail, use_container_width=True)
