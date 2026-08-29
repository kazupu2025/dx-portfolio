# -*- coding: utf-8 -*-
"""
B-73: 小売 シフト充足率・人件費最適化ダッシュボード
Streamlit ダッシュボード
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_shift_202401.csv"


@st.cache_data
def load_retail_shift_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    for col in ["daily_wage", "actual_staff", "required_staff", "is_understaffed"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("🏪 B-73 小売 シフト充足率・人件費最適化ダッシュボード")
st.caption("B-73 | 店舗別シフトギャップ・不足件数・役割別時給分析")

df_all = load_retail_shift_data()

if df_all.empty:
    st.error(f"データファイルが見つかりません: {CSV_PATH}")
    st.info("先に cleanse.py を実行してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    stores = ["全店"] + (sorted(df_all["store_name"].dropna().unique().tolist())
                         if "store_name" in df_all.columns else [])
    selected_store = st.selectbox("店舗選択", stores, key="b73_store_filter")

df_filtered = (
    df_all[df_all["store_name"] == selected_store].copy()
    if selected_store != "全店" else df_all.copy()
)

tab1, tab2, tab3 = st.tabs(["📊 サマリー", "📈 店舗別分析", "📋 データ詳細"])

with tab1:
    st.subheader("KPI サマリー")
    total_cost = int(df_filtered["daily_wage"].sum()) if "daily_wage" in df_filtered.columns else 0
    understaffed_count = int(df_filtered["is_understaffed"].sum()) if "is_understaffed" in df_filtered.columns else 0
    if "actual_staff" in df_filtered.columns and "required_staff" in df_filtered.columns:
        avg_fill_rate = (df_filtered["actual_staff"] / df_filtered["required_staff"].replace(0, float("nan"))).mean()
    else:
        avg_fill_rate = None

    col1, col2, col3 = st.columns(3)
    col1.metric("総人件費", f"¥{total_cost:,}")
    col2.metric("不足シフト件数", f"{understaffed_count} 件",
                delta="要対応" if understaffed_count > 0 else "問題なし",
                delta_color="inverse" if understaffed_count > 0 else "normal")
    col3.metric("平均充足率",
                f"{avg_fill_rate:.1%}" if avg_fill_rate is not None and pd.notna(avg_fill_rate) else "N/A")

    st.divider()
    if "is_understaffed" in df_filtered.columns and "store_name" in df_filtered.columns:
        st.subheader("店舗別 不足シフト件数")
        under_by_store = df_filtered.groupby("store_name")["is_understaffed"].sum().sort_values(ascending=False)
        st.bar_chart(under_by_store)

with tab2:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("店舗別 総人件費")
        if "store_name" in df_all.columns and "daily_wage" in df_all.columns:
            store_cost = df_all.groupby("store_name")["daily_wage"].sum().sort_values(ascending=True)
            st.bar_chart(store_cost)
    with col_r:
        st.subheader("役割別 平均時給")
        if "role" in df_all.columns and "hourly_wage" in df_all.columns:
            role_wage = df_all.groupby("role")["hourly_wage"].mean().sort_values(ascending=True)
            st.bar_chart(role_wage)
        elif "role" in df_all.columns and "daily_wage" in df_all.columns:
            role_wage = df_all.groupby("role")["daily_wage"].mean().sort_values(ascending=True)
            st.bar_chart(role_wage)

    st.subheader("店舗別 平均シフトギャップ")
    if "store_name" in df_all.columns and "actual_staff" in df_all.columns and "required_staff" in df_all.columns:
        gap = (df_all["actual_staff"] - df_all["required_staff"])
        df_gap = df_all.copy()
        df_gap["shift_gap"] = gap
        store_gap = df_gap.groupby("store_name")["shift_gap"].mean().sort_values(ascending=True)
        st.bar_chart(store_gap)

with tab3:
    st.subheader("データ詳細")
    if "role" in df_all.columns:
        role_options = sorted(df_all["role"].dropna().unique().tolist())
        role_filter = st.multiselect("役割フィルタ", options=role_options, default=role_options,
                                     key="b73_role_filter")
        df_display = (df_filtered[df_filtered["role"].isin(role_filter)].copy()
                      if role_filter else df_filtered.copy())
    else:
        df_display = df_filtered.copy()
    st.dataframe(df_display, use_container_width=True, height=400, hide_index=True)
    st.caption(f"表示行数: {len(df_display):,} 行")
