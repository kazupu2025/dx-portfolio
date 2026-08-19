# -*- coding: utf-8 -*-
"""
B-47 不動産 物件内見・成約率分析ダッシュボード（Streamlit）
"""
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_visits_202401.csv"

st.title("🏠 B-47 不動産 物件内見・成約率分析ダッシュボード")
st.caption("2024年1月 | 物件タイプ別成約率・エリア別内見件数・成約日数分析")


@st.cache_data
def load_viewing_conversion_data() -> pd.DataFrame:
    """B-47専用ローダー（キャッシュキー衝突防止）"""
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    for col in ["is_contracted", "asking_price", "days_to_contract"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


df_all = load_viewing_conversion_data()

if df_all.empty:
    st.error("データが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# --- サイドバー ---
with st.sidebar:
    st.header("🔍 フィルター")
    all_types = sorted(df_all["property_type"].dropna().unique().tolist()) if "property_type" in df_all.columns else []
    selected_types = st.multiselect("物件タイプ", all_types, default=all_types)
    all_areas = sorted(df_all["area"].dropna().unique().tolist()) if "area" in df_all.columns else []
    selected_areas = st.multiselect("エリア", all_areas, default=all_areas)

filtered = df_all.copy()
if selected_types and "property_type" in filtered.columns:
    filtered = filtered[filtered["property_type"].isin(selected_types)]
if selected_areas and "area" in filtered.columns:
    filtered = filtered[filtered["area"].isin(selected_areas)]

tab1, tab2, tab3 = st.tabs(["KPIサマリー", "物件・エリア分析", "内見明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    total_visits = len(filtered)
    contracted = filtered["is_contracted"].sum() if "is_contracted" in filtered.columns else 0
    conv_rate = contracted / total_visits if total_visits > 0 else 0
    avg_days = filtered.loc[filtered["is_contracted"] == 1, "days_to_contract"].mean() if "days_to_contract" in filtered.columns else float("nan")
    avg_price = filtered["asking_price"].mean() if "asking_price" in filtered.columns else float("nan")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総内見数", f"{total_visits:,} 件")
    col2.metric("成約率", f"{conv_rate:.1%}")
    col3.metric("平均成約日数", f"{avg_days:.1f} 日" if pd.notna(avg_days) else "N/A")
    col4.metric("平均物件価格", f"{avg_price:,.0f} 万円" if pd.notna(avg_price) else "N/A")

with tab2:
    if "property_type" in filtered.columns and "is_contracted" in filtered.columns and total_visits > 0:
        st.subheader("物件タイプ別成約率")
        type_grp = filtered.groupby("property_type").agg(
            visit_count=("visit_id", "count"),
            contract_count=("is_contracted", "sum"),
        )
        type_grp["conversion_rate"] = (type_grp["contract_count"] / type_grp["visit_count"]).round(3)
        st.bar_chart(type_grp["conversion_rate"])

        # テーブル表示
        type_grp_disp = type_grp.copy()
        type_grp_disp["成約率(%)"] = (type_grp_disp["conversion_rate"] * 100).round(1)
        st.dataframe(type_grp_disp[["visit_count", "contract_count", "成約率(%)"]].rename(
            columns={"visit_count": "内見件数", "contract_count": "成約件数"}
        ), use_container_width=True)

    if "area" in filtered.columns and total_visits > 0:
        st.subheader("エリア別内見件数")
        area_grp = filtered.groupby("area")["visit_id"].count().sort_values(ascending=False)
        st.bar_chart(area_grp)

with tab3:
    st.subheader("内見明細データ")
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)
    st.caption(f"表示件数: {len(filtered):,} 件")
