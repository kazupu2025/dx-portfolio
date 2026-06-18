# -*- coding: utf-8 -*-
"""Streamlit ダッシュボード - 配送コスト・利益率管理"""
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_deliveries_202401.csv"
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"
CHARTS_DIR = BASE_DIR / "output" / "charts"

st.set_page_config(page_title="配送コスト・利益率管理ダッシュボード", layout="wide")
st.title("配送コスト・利益率管理ダッシュボード")

if not CSV_PATH.exists():
    st.error("データが見つかりません。パイプラインを実行してください。")
    st.stop()

df_all = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# サイドバー: フィルター
st.sidebar.header("フィルター")
delivery_types = sorted(df_all["delivery_type"].unique())
selected_types = st.sidebar.multiselect(
    "配送区分を選択", delivery_types, default=delivery_types
)
areas = sorted(df_all["area"].unique())
selected_areas = st.sidebar.multiselect(
    "エリアを選択", areas, default=areas
)

df = df_all.copy()
if selected_types:
    df = df[df["delivery_type"].isin(selected_types)]
if selected_areas:
    df = df[df["area"].isin(selected_areas)]

if len(df) == 0:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

# タブ
tab1, tab2, tab3 = st.tabs(["KPIサマリー", "区分・エリア分析", "配送明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総配送件数", f"{len(df):,}件")
    with col2:
        avg_margin = df["profit_margin"].mean()
        st.metric("平均利益率", f"{avg_margin*100:.1f}%")
    with col3:
        total_profit = df["gross_profit"].sum()
        st.metric("総粗利", f"{total_profit:,.0f}円")
    with col4:
        avg_cpkm = df["cost_per_km"].mean()
        st.metric("平均km単価", f"{avg_cpkm:.2f}円/km")

    st.divider()

    st.subheader("利益グレード分布")
    grade_counts = df["margin_grade"].value_counts().reset_index()
    grade_counts.columns = ["グレード", "件数"]
    st.dataframe(grade_counts, use_container_width=True)

with tab2:
    st.subheader("区分・エリア分析")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**配送区分別利益率**")
        chart_type = CHARTS_DIR / "bar_type_margin.png"
        if chart_type.exists():
            st.image(str(chart_type))
        else:
            st.info("visualize.py を実行してください。")

    with col_right:
        st.markdown("**エリア別粗利合計**")
        chart_area = CHARTS_DIR / "bar_area_profit.png"
        if chart_area.exists():
            st.image(str(chart_area))
        else:
            st.info("visualize.py を実行してください。")

    st.markdown("**車両タイプ別km単価**")
    chart_vehicle = CHARTS_DIR / "bar_vehicle_cpkm.png"
    if chart_vehicle.exists():
        st.image(str(chart_vehicle))
    else:
        st.info("visualize.py を実行してください。")

    st.divider()

    st.subheader("配送区分別集計テーブル")
    type_tbl = df.groupby("delivery_type").agg(
        avg_profit_margin=("profit_margin", "mean"),
        avg_delivery_charge=("delivery_charge", "mean"),
        total_gross_profit=("gross_profit", "sum"),
        record_count=("delivery_id", "count"),
    ).reset_index().sort_values("avg_profit_margin", ascending=False)
    type_tbl["avg_profit_margin"] = (type_tbl["avg_profit_margin"] * 100).round(1)
    type_tbl["avg_delivery_charge"] = type_tbl["avg_delivery_charge"].round(0)
    type_tbl["total_gross_profit"] = type_tbl["total_gross_profit"].round(0)
    type_tbl.columns = ["配送区分", "平均利益率(%)", "平均配送料(円)", "総粗利(円)", "件数"]
    st.dataframe(type_tbl, use_container_width=True)

    st.subheader("エリア別集計テーブル")
    area_tbl = df.groupby("area").agg(
        avg_profit_margin=("profit_margin", "mean"),
        avg_total_cost=("total_cost", "mean"),
        total_gross_profit=("gross_profit", "sum"),
        record_count=("delivery_id", "count"),
    ).reset_index().sort_values("avg_profit_margin", ascending=False)
    area_tbl["avg_profit_margin"] = (area_tbl["avg_profit_margin"] * 100).round(1)
    area_tbl["avg_total_cost"] = area_tbl["avg_total_cost"].round(0)
    area_tbl["total_gross_profit"] = area_tbl["total_gross_profit"].round(0)
    area_tbl.columns = ["エリア", "平均利益率(%)", "平均総コスト(円)", "総粗利(円)", "件数"]
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
