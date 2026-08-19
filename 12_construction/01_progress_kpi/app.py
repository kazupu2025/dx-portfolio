# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_progress_202401.csv"


@st.cache_data
def load_construction_progress_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


st.title("🏗️ B-55 工程進捗・作業員稼働KPIダッシュボード")

df_all = load_construction_progress_data()

if df_all.empty:
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("フィルター")
    sites = ["すべて"] + (sorted(df_all["site_name"].unique().tolist()) if "site_name" in df_all.columns else [])
    selected_site = st.selectbox("現場選択", sites)

    processes = ["すべて"] + (sorted(df_all["process"].unique().tolist()) if "process" in df_all.columns else [])
    selected_process = st.selectbox("工程選択", processes)

# Apply filters
filtered = df_all.copy()
if "site_name" in filtered.columns and selected_site != "すべて":
    filtered = filtered[filtered["site_name"] == selected_site]
if "process" in filtered.columns and selected_process != "すべて":
    filtered = filtered[filtered["process"] == selected_process]

if filtered.empty:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs(["進捗サマリー", "現場・工程分析", "作業員データ詳細"])

with tab1:
    st.subheader("KPIカード")
    col1, col2, col3 = st.columns(3)
    avg_progress = filtered["progress_pct"].mean() if "progress_pct" in filtered.columns else 0.0
    delay_count = int(filtered["is_delayed"].sum()) if "is_delayed" in filtered.columns else 0
    defect_total = int(filtered["defect_count"].sum()) if "defect_count" in filtered.columns else 0
    col1.metric("平均進捗率 (%)", f"{avg_progress:.1f}")
    col2.metric("遅延件数", delay_count)
    col3.metric("不具合合計", defect_total)

with tab2:
    st.subheader("現場・工程分析")

    if "site_name" in filtered.columns and "progress_pct" in filtered.columns:
        st.markdown("**現場別 平均進捗率**")
        site_prog = filtered.groupby("site_name")["progress_pct"].mean().sort_values(ascending=False)
        st.bar_chart(site_prog)

    if "process" in filtered.columns and "actual_hours" in filtered.columns:
        st.markdown("**工程別 累積稼働時間**")
        proc_hours = filtered.groupby("process")["actual_hours"].sum().sort_values(ascending=False)
        st.bar_chart(proc_hours)

    if "site_name" in filtered.columns and "defect_count" in filtered.columns:
        st.markdown("**現場別 不具合件数**")
        site_defect = filtered.groupby("site_name")["defect_count"].sum().sort_values(ascending=False)
        st.bar_chart(site_defect)

with tab3:
    st.subheader("作業員データ詳細")
    if "worker_id" in filtered.columns:
        _agg = {k: v for k, v in {
            "actual_hours": "sum",
            "progress_pct": "mean",
            "defect_count": "sum",
        }.items() if k in filtered.columns}
        if _agg:
            worker_summary = filtered.groupby("worker_id").agg(_agg).reset_index()
            if "actual_hours" in worker_summary.columns:
                worker_summary["actual_hours"] = worker_summary["actual_hours"].round(1)
            if "progress_pct" in worker_summary.columns:
                worker_summary["progress_pct"] = worker_summary["progress_pct"].round(1)
            st.dataframe(worker_summary, use_container_width=True)
    else:
        st.dataframe(filtered, use_container_width=True)
