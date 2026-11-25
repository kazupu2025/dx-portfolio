# -*- coding: utf-8 -*-
"""
B-56: アルバイトシフト管理・人件費集計
Streamlit ダッシュボード
"""

import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_FILE = OUTPUT_DIR / "cleaned_shift_202401.csv"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_restaurant_shift_data() -> pd.DataFrame:
    if not CLEANED_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    for col in ["work_hours", "hourly_rate", "daily_wage", "is_overtime"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "work_date" in df.columns:
        df["work_date"] = pd.to_datetime(df["work_date"], format="%Y-%m-%d", errors="coerce")
    return df


st.title("🍽️ B-56 飲食 シフト・人件費ダッシュボード")
st.caption("2024年1月 アルバイトシフト管理・人件費集計")

df_all = load_restaurant_shift_data()

if df_all.empty:
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# ---- 店舗フィルター ----
with st.sidebar:
    stores = ["全店舗"] + (sorted(df_all["store_name"].dropna().unique().tolist()) if "store_name" in df_all.columns else [])
    selected_store = st.selectbox("店舗フィルター", stores)

if "store_name" in df_all.columns and selected_store != "全店舗":
    df = df_all[df_all["store_name"] == selected_store].copy()
else:
    df = df_all.copy()

if df.empty:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

# ---- KPI ----
total_labor_cost = df["daily_wage"].sum() if "daily_wage" in df.columns else 0
avg_hourly_rate = df["hourly_rate"].mean() if "hourly_rate" in df.columns else 0
overtime_rate = df["is_overtime"].mean() * 100 if "is_overtime" in df.columns else 0
total_work_hours = df["work_hours"].sum() if "work_hours" in df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("総人件費", f"{total_labor_cost:,.0f} 円")
col2.metric("平均時給", f"{avg_hourly_rate:,.0f} 円")
col3.metric("残業率", f"{overtime_rate:.1f} %")
col4.metric("総労働時間", f"{total_work_hours:,.1f} h")

st.divider()

# ---- タブ ----
tab1, tab2, tab3 = st.tabs(["店舗別人件費", "役職別分析", "スタッフ別労働時間"])

with tab1:
    st.subheader("店舗別 総人件費・残業率")
    if "store_name" in df.columns and "daily_wage" in df.columns:
        store_summary = df.groupby("store_name").agg(
            総人件費=("daily_wage", "sum"),
            平均時給=("hourly_rate", "mean") if "hourly_rate" in df.columns else ("daily_wage", "count"),
        ).sort_values("総人件費", ascending=False)
        st.dataframe(store_summary, use_container_width=True)
        st.markdown("**店舗別 総人件費**")
        st.bar_chart(store_summary["総人件費"])

with tab2:
    st.subheader("役職別 平均日次賃金・労働時間")
    if "role" in df.columns and "daily_wage" in df.columns:
        _role_agg = {k: v for k, v in {"daily_wage": "mean", "work_hours": "mean"}.items() if k in df.columns}
        role_summary = df.groupby("role").agg(_role_agg).sort_values("daily_wage", ascending=False)
        st.dataframe(role_summary, use_container_width=True)
        if "daily_wage" in role_summary.columns:
            st.markdown("**役職別 平均日次賃金**")
            st.bar_chart(role_summary["daily_wage"])

with tab3:
    st.subheader("スタッフ別 月間労働時間 上位10名")
    if "staff_id" in df.columns and "work_hours" in df.columns:
        staff_ranking = (
            df.groupby("staff_id")["work_hours"].sum()
            .sort_values(ascending=False)
            .head(10)
        )
        st.dataframe(staff_ranking.reset_index(), use_container_width=True)
        st.markdown("**スタッフ別 総労働時間（上位10）**")
        st.bar_chart(staff_ranking)

st.divider()

# ---- 高コストシフトテーブル ----
st.subheader("高コストシフト一覧")
if "labor_cost_flag" in df.columns:
    high_cost = df[df["labor_cost_flag"] == "高コスト"].copy()
    _hc_cols = [c for c in ["work_date", "staff_id", "store_name", "role", "work_hours", "hourly_rate", "daily_wage"] if c in high_cost.columns]
    st.dataframe(high_cost[_hc_cols].sort_values("daily_wage", ascending=False).head(20) if "daily_wage" in high_cost.columns else high_cost.head(20), use_container_width=True)
else:
    st.info("labor_cost_flag列がありません。")

with st.expander("分析レポート（Markdown）"):
    if REPORT_FILE.exists():
        st.markdown(REPORT_FILE.read_text(encoding="utf-8"))
    else:
        st.warning("レポートファイルが見つかりません。")
