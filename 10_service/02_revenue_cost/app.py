# -*- coding: utf-8 -*-
"""
B-69: サービス 売上・原価分析ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "output" / "cleaned_revenue_cost_202401.csv"
REPORT_PATH = BASE / "output" / "analysis_report.md"


@st.cache_data
def load_service_revenue_cost_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    if "is_completed" in df.columns:
        df["is_completed"] = df["is_completed"].astype(str).map(
            lambda x: True if x.lower() in ("true", "1") else False
        )
    for col in ["revenue", "direct_cost", "allocated_overhead", "total_cost",
                "gross_profit", "operating_profit", "gross_margin_ratio",
                "operating_margin_ratio", "revenue_per_hour", "hours_spent"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_service_revenue_report() -> str:
    if REPORT_PATH.exists():
        return REPORT_PATH.read_text(encoding="utf-8")
    return "レポートが見つかりません"


st.title("💼 B-69 サービス 売上・原価分析ダッシュボード")
st.caption("B-69 | 2024年1〜3月 | ITサービス案件別売上・原価・利益率")

df_all = load_service_revenue_cost_data()

if df_all.empty:
    st.error(f"データファイルが見つかりません: {CSV_PATH}")
    st.info("先に cleanse.py を実行してください。")
    st.stop()

# フィルター
with st.sidebar:
    st.header("🔍 フィルター")
    if "service_type" in df_all.columns:
        service_types = sorted(df_all["service_type"].dropna().unique().tolist())
        selected = st.multiselect("サービス区分", service_types, default=service_types,
                                  key="b69_service_type_filter")
    else:
        selected = []

df = df_all[df_all["service_type"].isin(selected)].copy() if selected else df_all.copy()

# KPI
total_revenue = df["revenue"].sum() if "revenue" in df.columns else 0
gross_profit_sum = df["gross_profit"].sum() if "gross_profit" in df.columns else 0
avg_gm = (gross_profit_sum / total_revenue * 100) if total_revenue > 0 else 0
total_op = df["operating_profit"].sum() if "operating_profit" in df.columns else 0
red_count = int((df["profit_flag"] == "赤字").sum()) if "profit_flag" in df.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("売上合計", f"¥{total_revenue:,.0f}")
c2.metric("平均粗利率", f"{avg_gm:.1f}%")
c3.metric("営業利益合計", f"¥{total_op:,.0f}",
          delta="注意" if total_op < 0 else None,
          delta_color="inverse" if total_op < 0 else "normal")
c4.metric("赤字案件数", f"{red_count}件",
          delta="要対応" if red_count > 0 else "問題なし",
          delta_color="inverse" if red_count > 0 else "normal")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 サービス別利益率", "🏢 部門別売上", "📋 案件一覧"])

with tab1:
    st.subheader("サービス別 粗利率")
    if "service_type" in df.columns and "gross_profit" in df.columns and "revenue" in df.columns:
        svc_gm = df.groupby("service_type").apply(
            lambda g: (g["gross_profit"].sum() / g["revenue"].sum() * 100)
            if g["revenue"].sum() > 0 else 0
        ).sort_values(ascending=True)
        st.bar_chart(svc_gm)

    st.subheader("サービス別 収益サマリー")
    if "service_type" in df.columns:
        _agg = {"案件数": ("project_id", "count")} if "project_id" in df.columns else {}
        if "revenue" in df.columns:
            _agg["売上合計"] = ("revenue", "sum")
        if "gross_profit" in df.columns:
            _agg["粗利合計"] = ("gross_profit", "sum")
        if "operating_profit" in df.columns:
            _agg["営業利益合計"] = ("operating_profit", "sum")
        if _agg:
            svc_tbl = df.groupby("service_type", as_index=False).agg(**_agg)
            if "売上合計" in svc_tbl.columns and "粗利合計" in svc_tbl.columns:
                svc_tbl["粗利率(%)"] = (
                    svc_tbl["粗利合計"] / svc_tbl["売上合計"].replace(0, np.nan) * 100
                ).round(1)
            for col in ["売上合計", "粗利合計", "営業利益合計"]:
                if col in svc_tbl.columns:
                    svc_tbl[col] = svc_tbl[col].apply(lambda x: f"¥{x:,.0f}")
            st.dataframe(svc_tbl, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("部門別 売上")
    if "department" in df.columns and "revenue" in df.columns:
        dept_rev = df.groupby("department")["revenue"].sum().sort_values(ascending=True)
        st.bar_chart(dept_rev)

    st.subheader("部門別 営業利益")
    if "department" in df.columns and "operating_profit" in df.columns:
        dept_op = df.groupby("department")["operating_profit"].sum().sort_values(ascending=True)
        st.bar_chart(dept_op)

with tab3:
    st.subheader("案件一覧")
    _cols = ["project_id", "client_name", "service_type", "department",
             "contract_month", "revenue", "gross_margin_ratio",
             "operating_margin_ratio", "profit_flag", "is_completed"]
    _avail = [c for c in _cols if c in df.columns]
    disp_df = df[_avail].copy()
    if "revenue" in disp_df.columns:
        disp_df["revenue"] = disp_df["revenue"].apply(
            lambda x: f"¥{x:,.0f}" if pd.notna(x) else "N/A")
    for rate_col in ["gross_margin_ratio", "operating_margin_ratio"]:
        if rate_col in disp_df.columns:
            disp_df[rate_col] = disp_df[rate_col].apply(
                lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")
    st.dataframe(disp_df, use_container_width=True, hide_index=True)

st.divider()

# 赤字・低収益アラート
if "profit_flag" in df.columns:
    alert_df = df[df["profit_flag"].isin(["赤字", "低収益"])].copy()
    if len(alert_df) > 0:
        st.subheader(f"⚠️ 要注意案件 ({len(alert_df)}件)")
        _a_cols = [c for c in ["project_id", "client_name", "service_type", "department",
                                "contract_month", "revenue", "operating_margin_ratio", "profit_flag"]
                   if c in alert_df.columns]
        alert_disp = alert_df[_a_cols].copy()
        if "revenue" in alert_disp.columns:
            alert_disp["revenue"] = alert_disp["revenue"].apply(lambda x: f"¥{x:,.0f}")
        if "operating_margin_ratio" in alert_disp.columns:
            alert_disp["operating_margin_ratio"] = alert_disp["operating_margin_ratio"].apply(
                lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")
        st.dataframe(alert_disp, use_container_width=True, hide_index=True)

st.divider()

with st.expander("📄 分析レポートを表示", expanded=False):
    st.markdown(load_service_revenue_report())
