# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.rcParams

matplotlib.rcParams['font.family'] = 'MS Gothic'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "output", "cleaned_claims_202401.csv")

st.set_page_config(page_title="診療報酬・請求分析ダッシュボード", layout="wide")
st.title("診療報酬・請求分析ダッシュボード")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["claim_date"] = pd.to_datetime(df["claim_date"], format="%Y-%m-%d", errors="coerce")
    return df

df = load_data()

# --- Sidebar ---
st.sidebar.header("フィルター")
all_depts = sorted(df["dept"].unique().tolist())
selected_depts = st.sidebar.multiselect("診療科", all_depts, default=all_depts)

all_ins = sorted(df["insurance_type"].unique().tolist())
selected_ins = st.sidebar.multiselect("保険区分", all_ins, default=all_ins)

filtered = df[
    df["dept"].isin(selected_depts) &
    df["insurance_type"].isin(selected_ins)
]

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["収益サマリー", "診療科・保険区分分析", "請求明細データ"])

with tab1:
    st.subheader("KPI カード")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総請求額", "{:,.0f} 円".format(filtered["claim_amount"].sum()))
    c2.metric("総実収入", "{:,.0f} 円".format(filtered["net_amount"].sum()))
    c3.metric("平均査定率", "{:.2%}".format(filtered["reduction_rate"].mean()))
    c4.metric("返戾件数", "{}件".format((filtered["is_returned"] == 1).sum()))

with tab2:
    st.subheader("診療科別 請求金額合計")
    dept_claim = filtered.groupby("dept")["claim_amount"].sum().sort_values()
    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.barh(dept_claim.index, dept_claim.values, color="#4472C4")
    ax1.set_xlabel("請求金額合計 (円)")
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close()

    st.subheader("保険区分別 平均査定率")
    ins_red = filtered.groupby("insurance_type")["reduction_rate"].mean()
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    ax2.bar(ins_red.index, ins_red.values * 100, color="#ED7D31")
    ax2.set_ylabel("平均査定率 (%)")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

    st.subheader("診療科別 回収率")
    dept_coll = filtered.groupby("dept").apply(
        lambda g: (g["payment_status"] == "支払済み").mean() * 100
    )
    fig3, ax3 = plt.subplots(figsize=(7, 4))
    ax3.bar(dept_coll.index, dept_coll.values, color="#70AD47")
    ax3.set_ylabel("回収率 (%)")
    ax3.set_ylim(0, 120)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

with tab3:
    st.subheader("請求明細データ")
    st.dataframe(
        filtered[[
            "claim_date", "claim_id", "dept", "insurance_type",
            "patient_count", "total_points", "claim_amount",
            "reduction_amount", "payment_status", "net_amount",
            "reduction_rate", "collection_flag"
        ]].reset_index(drop=True),
        use_container_width=True
    )
    st.caption("表示件数: {}件".format(len(filtered)))
