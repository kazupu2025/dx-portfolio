# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "output", "cleaned_contracts_202401.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "output", "charts")

st.set_page_config(page_title="SaaS チャーン分析", layout="wide")
st.title("SaaSサブスクリプション解約率（チャーン）分析")


@st.cache_data
def load_data():
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df["monthly_fee"] = pd.to_numeric(df["monthly_fee"], errors="coerce")
    df["usage_months"] = pd.to_numeric(df["usage_months"], errors="coerce")
    df["login_count"] = pd.to_numeric(df["login_count"], errors="coerce")
    df["ltv"] = pd.to_numeric(df["ltv"], errors="coerce")
    df["is_churned"] = pd.to_numeric(df["is_churned"], errors="coerce")
    return df


df_all = load_data()

# ---- Sidebar filters ----
st.sidebar.header("フィルター")
plans = ["すべて"] + sorted(df_all["plan"].dropna().unique().tolist())
selected_plan = st.sidebar.selectbox("プラン選択", plans)

industries = ["すべて"] + sorted(df_all["industry"].dropna().unique().tolist())
selected_industry = st.sidebar.selectbox("業種選択", industries)

df = df_all.copy()
if selected_plan != "すべて":
    df = df[df["plan"] == selected_plan]
if selected_industry != "すべて":
    df = df[df["industry"] == selected_industry]

# ---- Tabs ----
tab1, tab2, tab3 = st.tabs(["チャーンサマリー", "プラン・業種分析", "契約明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    total = len(df)
    churned = int(df["is_churned"].sum()) if total > 0 else 0
    churn_rate = churned / total if total > 0 else 0
    avg_ltv = df["ltv"].mean() if total > 0 else 0
    high_risk = int((df["churn_risk"] == "高リスク").sum()) if total > 0 else 0
    avg_usage = df["usage_months"].mean() if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("全体解約率", f"{churn_rate:.1%}")
    col2.metric("平均LTV", f"{avg_ltv:,.0f}円")
    col3.metric("高リスク顧客数", f"{high_risk:,}件")
    col4.metric("平均利用月数", f"{avg_usage:.1f}ヶ月")

    st.markdown("---")
    st.subheader("解約理由の内訳")
    if total > 0:
        churned_df = df[df["is_churned"] == 1]
        if not churned_df.empty:
            reason_counts = churned_df["churn_reason"].value_counts()
            st.bar_chart(reason_counts)
        else:
            st.info("選択条件内に解約データがありません。")

with tab2:
    st.subheader("グラフ分析")
    col_a, col_b = st.columns(2)
    with col_a:
        chart1 = os.path.join(CHARTS_DIR, "bar_plan_churn_rate.png")
        if os.path.exists(chart1):
            st.image(chart1, caption="プラン別 解約率", use_container_width=True)
        else:
            st.warning("グラフが見つかりません。visualize.py を先に実行してください。")
    with col_b:
        chart2 = os.path.join(CHARTS_DIR, "bar_industry_ltv.png")
        if os.path.exists(chart2):
            st.image(chart2, caption="業種別 平均LTV", use_container_width=True)
        else:
            st.warning("グラフが見つかりません。")

    chart3 = os.path.join(CHARTS_DIR, "bar_churn_risk.png")
    if os.path.exists(chart3):
        st.image(chart3, caption="チャーンリスク分布", use_container_width=True)
    else:
        st.warning("グラフが見つかりません。")

with tab3:
    st.subheader("契約明細データ")
    risk_options = ["すべて", "高リスク", "中リスク", "低リスク"]
    selected_risk = st.selectbox("チャーンリスクでフィルタ", risk_options)

    df_detail = df.copy()
    if selected_risk != "すべて":
        df_detail = df_detail[df_detail["churn_risk"] == selected_risk]

    st.dataframe(df_detail.reset_index(drop=True), use_container_width=True)
    st.caption(f"表示件数: {len(df_detail):,} 件")
