# -*- coding: utf-8 -*-
"""Streamlit ダッシュボード - 配送コスト・利益率管理"""
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_deliveries_202401.csv"
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"


@st.cache_data
def load_logistics_cost_margin_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


st.title("📦 B-52 配送コスト・利益率管理ダッシュボード")

df_all = load_logistics_cost_margin_data()

if df_all.empty:
    st.error("データが見つかりません。パイプラインを実行してください。")
    st.stop()

# サイドバー: フィルター
with st.sidebar:
    st.header("フィルター")
    delivery_types = sorted(df_all["delivery_type"].unique().tolist()) if "delivery_type" in df_all.columns else []
    selected_types = st.multiselect("配送区分を選択", delivery_types, default=delivery_types)

    areas = sorted(df_all["area"].unique().tolist()) if "area" in df_all.columns else []
    selected_areas = st.multiselect("エリアを選択", areas, default=areas)

df = df_all.copy()
if "delivery_type" in df.columns and selected_types:
    df = df[df["delivery_type"].isin(selected_types)]
if "area" in df.columns and selected_areas:
    df = df[df["area"].isin(selected_areas)]

if df.empty:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

# タブ
tab1, tab2, tab3 = st.tabs(["KPIサマリー", "区分・エリア分析", "配送明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総配送件数", f"{len(df):,}件")

    avg_margin = df["profit_margin"].mean() if "profit_margin" in df.columns else 0.0
    col2.metric("平均利益率", f"{avg_margin*100:.1f}%")

    total_profit = df["gross_profit"].sum() if "gross_profit" in df.columns else 0
    col3.metric("総粗利", f"{total_profit:,.0f}円")

    avg_cpkm = df["cost_per_km"].mean() if "cost_per_km" in df.columns else 0.0
    col4.metric("平均km単価", f"{avg_cpkm:.2f}円/km")

    st.divider()
    st.subheader("利益グレード分布")
    if "margin_grade" in df.columns:
        grade_counts = df["margin_grade"].value_counts()
        st.bar_chart(grade_counts)
    else:
        st.info("margin_grade列がありません。")

with tab2:
    st.subheader("区分・エリア分析")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**配送区分別 平均利益率**")
        if "delivery_type" in df.columns and "profit_margin" in df.columns:
            type_margin = (df.groupby("delivery_type")["profit_margin"].mean() * 100).round(1)
            st.bar_chart(type_margin)
    with col_right:
        st.markdown("**エリア別 粗利合計**")
        if "area" in df.columns and "gross_profit" in df.columns:
            area_profit = df.groupby("area")["gross_profit"].sum()
            st.bar_chart(area_profit)

    st.markdown("**車両タイプ別 km単価**")
    if "vehicle_type" in df.columns and "cost_per_km" in df.columns:
        vehicle_cpkm = df.groupby("vehicle_type")["cost_per_km"].mean().round(2)
        st.bar_chart(vehicle_cpkm)

    st.divider()
    st.subheader("配送区分別集計テーブル")
    if "delivery_type" in df.columns:
        _agg_cols = {k: v for k, v in {
            "profit_margin": "mean", "delivery_charge": "mean",
            "gross_profit": "sum", "delivery_id": "count",
        }.items() if k in df.columns}
        if _agg_cols:
            type_tbl = df.groupby("delivery_type").agg(_agg_cols).reset_index().sort_values(
                "profit_margin", ascending=False
            )
            if "profit_margin" in type_tbl.columns:
                type_tbl["profit_margin"] = (type_tbl["profit_margin"] * 100).round(1)
            st.dataframe(type_tbl, use_container_width=True)

    st.subheader("エリア別集計テーブル")
    if "area" in df.columns:
        _agg_cols2 = {k: v for k, v in {
            "profit_margin": "mean", "total_cost": "mean",
            "gross_profit": "sum", "delivery_id": "count",
        }.items() if k in df.columns}
        if _agg_cols2:
            area_tbl = df.groupby("area").agg(_agg_cols2).reset_index().sort_values(
                "profit_margin", ascending=False
            )
            if "profit_margin" in area_tbl.columns:
                area_tbl["profit_margin"] = (area_tbl["profit_margin"] * 100).round(1)
            st.dataframe(area_tbl, use_container_width=True)

with tab3:
    st.subheader("配送明細データ")
    st.dataframe(df, use_container_width=True)

st.divider()
with st.expander("分析レポートを表示"):
    if REPORT_PATH.exists():
        st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
    else:
        st.info("analyze.py を実行してください。")
