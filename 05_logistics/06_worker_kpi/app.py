# -*- coding: utf-8 -*-
"""
B-71: 物流 荷役作業員KPI集計ダッシュボード
Streamlit ダッシュボード
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_worker_kpi_202401.csv"


@st.cache_data
def load_logistics_worker_kpi_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    for col in ["throughput", "error_rate", "processed_qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("📦 B-71 物流 荷役作業員KPI集計ダッシュボード")
st.caption("B-71 | ゾーン・作業区分別スループット・エラー率・KPI評価")

df_all = load_logistics_worker_kpi_data()

if df_all.empty:
    st.error(f"データファイルが見つかりません: {CSV_PATH}")
    st.info("先に cleanse.py を実行してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    zones = sorted(df_all["zone"].dropna().unique().tolist()) if "zone" in df_all.columns else []
    selected_zones = st.multiselect("ゾーン選択", zones, default=zones, key="b71_zone_filter")
    tasks = sorted(df_all["task_type"].dropna().unique().tolist()) if "task_type" in df_all.columns else []
    selected_tasks = st.multiselect("作業区分選択", tasks, default=tasks, key="b71_task_filter")

# フィルタリング
mask = pd.Series([True] * len(df_all), index=df_all.index)
if selected_zones and "zone" in df_all.columns:
    mask &= df_all["zone"].isin(selected_zones)
if selected_tasks and "task_type" in df_all.columns:
    mask &= df_all["task_type"].isin(selected_tasks)
filtered = df_all[mask].copy()

tab1, tab2, tab3 = st.tabs(["📊 KPIサマリー", "🗺️ ゾーン・作業区分分析", "👷 作業員別データ詳細"])

with tab1:
    st.subheader("KPIサマリー")
    total_qty = int(filtered["processed_qty"].sum()) if "processed_qty" in filtered.columns else 0
    avg_err = filtered["error_rate"].mean() if "error_rate" in filtered.columns else None
    excellent = (
        filtered[filtered["kpi_flag"] == "優秀"]["worker_id"].nunique()
        if "kpi_flag" in filtered.columns and "worker_id" in filtered.columns else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("総処理件数", f"{total_qty:,} 件")
    col2.metric("平均エラー率", f"{avg_err:.2%}" if avg_err is not None and pd.notna(avg_err) else "N/A")
    col3.metric("優秀作業員数", f"{excellent} 名")

    st.divider()

    if "kpi_flag" in filtered.columns:
        st.subheader("KPI評価分布")
        kpi_dist = filtered["kpi_flag"].value_counts().sort_values(ascending=True)
        st.bar_chart(kpi_dist)

with tab2:
    st.subheader("ゾーン・作業区分分析")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**ゾーン別 処理件数**")
        if "zone" in filtered.columns and "processed_qty" in filtered.columns:
            zone_qty = filtered.groupby("zone")["processed_qty"].sum().sort_values(ascending=True)
            st.bar_chart(zone_qty)
    with col_r:
        st.markdown("**作業区分別 平均スループット**")
        if "task_type" in filtered.columns and "throughput" in filtered.columns:
            task_tp = filtered.groupby("task_type")["throughput"].mean().sort_values(ascending=True)
            st.bar_chart(task_tp)

    st.subheader("エラー率 上位作業員")
    if "worker_id" in filtered.columns and "error_rate" in filtered.columns:
        err_top = (
            filtered.groupby("worker_id")["error_rate"]
            .mean()
            .sort_values(ascending=False)
            .head(10)
        )
        st.bar_chart(err_top)

with tab3:
    st.subheader("作業員別データ詳細")
    if "worker_id" in filtered.columns:
        _agg = {}
        if "throughput" in filtered.columns:
            _agg["avg_throughput"] = ("throughput", "mean")
        if "error_rate" in filtered.columns:
            _agg["avg_error_rate"] = ("error_rate", "mean")
        if "processed_qty" in filtered.columns:
            _agg["total_processed"] = ("processed_qty", "sum")
        if "kpi_flag" in filtered.columns:
            _agg["kpi_flag"] = ("kpi_flag", lambda x: x.value_counts().index[0] if len(x) > 0 else "N/A")

        worker_detail = filtered.groupby("worker_id").agg(**_agg).reset_index()
        if "avg_throughput" in worker_detail.columns:
            worker_detail["avg_throughput"] = worker_detail["avg_throughput"].round(2)
        if "avg_error_rate" in worker_detail.columns:
            worker_detail["avg_error_rate"] = worker_detail["avg_error_rate"].round(4)
        st.dataframe(worker_detail, use_container_width=True, hide_index=True)
