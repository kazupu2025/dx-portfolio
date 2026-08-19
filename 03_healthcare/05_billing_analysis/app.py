# -*- coding: utf-8 -*-
"""
B-45 医療・介護 診療報酬・請求分析ダッシュボード（Streamlit）
"""
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_claims_202401.csv"

st.title("💊 B-45 医療・介護 診療報酬・請求分析ダッシュボード")
st.caption("2024年1月 | 診療科別・保険区分別 請求額・査定率・回収率分析")


@st.cache_data
def load_billing_analysis_data() -> pd.DataFrame:
    """B-45専用ローダー（キャッシュキー衝突防止）"""
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["claim_date"] = pd.to_datetime(df["claim_date"], format="%Y-%m-%d", errors="coerce")
    return df


df_all = load_billing_analysis_data()

if df_all.empty:
    st.error("データが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# --- サイドバー ---
with st.sidebar:
    st.header("🔍 フィルター")
    all_depts = sorted(df_all["dept"].unique().tolist()) if "dept" in df_all.columns else []
    selected_depts = st.multiselect("診療科", all_depts, default=all_depts)

    all_ins = sorted(df_all["insurance_type"].unique().tolist()) if "insurance_type" in df_all.columns else []
    selected_ins = st.multiselect("保険区分", all_ins, default=all_ins)

filtered = df_all.copy()
if selected_depts and "dept" in filtered.columns:
    filtered = filtered[filtered["dept"].isin(selected_depts)]
if selected_ins and "insurance_type" in filtered.columns:
    filtered = filtered[filtered["insurance_type"].isin(selected_ins)]

# --- タブ ---
tab1, tab2, tab3 = st.tabs(["収益サマリー", "診療科・保険区分分析", "請求明細データ"])

with tab1:
    st.subheader("KPI カード")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総請求額", "{:,.0f} 円".format(filtered["claim_amount"].sum()) if "claim_amount" in filtered.columns else "—")
    c2.metric("総実収入", "{:,.0f} 円".format(filtered["net_amount"].sum()) if "net_amount" in filtered.columns else "—")
    c3.metric("平均査定率", "{:.2%}".format(filtered["reduction_rate"].mean()) if "reduction_rate" in filtered.columns and len(filtered) > 0 else "—")
    c4.metric("返戾件数", "{}件".format((filtered["is_returned"] == 1).sum()) if "is_returned" in filtered.columns else "—")

with tab2:
    if "dept" in filtered.columns and "claim_amount" in filtered.columns:
        st.subheader("診療科別 請求金額合計")
        dept_claim = filtered.groupby("dept")["claim_amount"].sum().sort_values(ascending=False)
        st.bar_chart(dept_claim)

    if "insurance_type" in filtered.columns and "reduction_rate" in filtered.columns:
        st.subheader("保険区分別 平均査定率(%)")
        ins_red = (filtered.groupby("insurance_type")["reduction_rate"].mean() * 100).round(2)
        st.bar_chart(ins_red)

    if "dept" in filtered.columns and "payment_status" in filtered.columns:
        st.subheader("診療科別 回収率(%)")
        dept_coll = (
            filtered.groupby("dept")
            .apply(lambda g: (g["payment_status"] == "支払済み").mean() * 100)
            .round(1)
        )
        st.bar_chart(dept_coll)

    if "dept" in filtered.columns and len(filtered) > 0:
        st.subheader("診療科別サマリーテーブル")
        agg_cols = {}
        if "claim_amount" in filtered.columns:
            agg_cols["請求金額合計"] = ("claim_amount", "sum")
        if "reduction_rate" in filtered.columns:
            agg_cols["平均査定率"] = ("reduction_rate", "mean")
        if agg_cols:
            dept_tbl = filtered.groupby("dept").agg(**agg_cols).round(2)
            st.dataframe(dept_tbl, use_container_width=True)

with tab3:
    st.subheader("請求明細データ")
    want_cols = ["claim_date", "claim_id", "dept", "insurance_type",
                 "patient_count", "total_points", "claim_amount",
                 "reduction_amount", "payment_status", "net_amount",
                 "reduction_rate", "collection_flag"]
    disp_cols = [c for c in want_cols if c in filtered.columns]
    if len(filtered) > 0 and disp_cols:
        st.dataframe(filtered[disp_cols].reset_index(drop=True), use_container_width=True)
    st.caption("表示件数: {}件".format(len(filtered)))
