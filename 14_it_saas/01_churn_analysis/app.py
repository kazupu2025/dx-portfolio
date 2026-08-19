# -*- coding: utf-8 -*-
"""
B-48 IT・SaaS チャーン分析ダッシュボード（Streamlit）
"""
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
INPUT_FILE = OUTPUT_DIR / "cleaned_contracts_202401.csv"
CHARTS_DIR = OUTPUT_DIR / "charts"

st.title("💻 B-48 IT・SaaS チャーン分析ダッシュボード")
st.caption("2024年1月 | プラン別解約率・業種別LTV・チャーンリスク分布")


@st.cache_data
def load_churn_analysis_data() -> pd.DataFrame:
    """B-48専用ローダー（キャッシュキー衝突防止）"""
    if not INPUT_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    for col in ["monthly_fee", "usage_months", "login_count", "ltv", "is_churned"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


df_all = load_churn_analysis_data()

if df_all.empty:
    st.error("データが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# ---- サイドバー ----
with st.sidebar:
    st.header("🔍 フィルター")
    plans = ["すべて"] + sorted(df_all["plan"].dropna().unique().tolist()) if "plan" in df_all.columns else ["すべて"]
    selected_plan = st.selectbox("プラン選択", plans)

    industries = ["すべて"] + sorted(df_all["industry"].dropna().unique().tolist()) if "industry" in df_all.columns else ["すべて"]
    selected_industry = st.selectbox("業種選択", industries)

df = df_all.copy()
if selected_plan != "すべて" and "plan" in df.columns:
    df = df[df["plan"] == selected_plan]
if selected_industry != "すべて" and "industry" in df.columns:
    df = df[df["industry"] == selected_industry]

# ---- タブ ----
tab1, tab2, tab3 = st.tabs(["チャーンサマリー", "プラン・業種分析", "契約明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    total = len(df)
    churned = int(df["is_churned"].sum()) if "is_churned" in df.columns and total > 0 else 0
    churn_rate = churned / total if total > 0 else 0
    avg_ltv = df["ltv"].mean() if "ltv" in df.columns and total > 0 else 0
    high_risk = int((df["churn_risk"] == "高リスク").sum()) if "churn_risk" in df.columns and total > 0 else 0
    avg_usage = df["usage_months"].mean() if "usage_months" in df.columns and total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("全体解約率", f"{churn_rate:.1%}")
    col2.metric("平均LTV", f"{avg_ltv:,.0f}円")
    col3.metric("高リスク顧客数", f"{high_risk:,}件")
    col4.metric("平均利用月数", f"{avg_usage:.1f}ヶ月")

    st.markdown("---")
    st.subheader("解約理由の内訳")
    if total > 0 and "is_churned" in df.columns and "churn_reason" in df.columns:
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
        chart1 = CHARTS_DIR / "bar_plan_churn_rate.png"
        if chart1.exists():
            st.image(str(chart1), caption="プラン別 解約率", use_container_width=True)
        else:
            st.warning("グラフが見つかりません。visualize.py を先に実行してください。")
    with col_b:
        chart2 = CHARTS_DIR / "bar_industry_ltv.png"
        if chart2.exists():
            st.image(str(chart2), caption="業種別 平均LTV", use_container_width=True)
        else:
            st.warning("グラフが見つかりません。")

    chart3 = CHARTS_DIR / "bar_churn_risk.png"
    if chart3.exists():
        st.image(str(chart3), caption="チャーンリスク分布", use_container_width=True)
    else:
        st.warning("グラフが見つかりません。")

with tab3:
    st.subheader("契約明細データ")
    risk_options = ["すべて", "高リスク", "中リスク", "低リスク"]
    selected_risk = st.selectbox("チャーンリスクでフィルタ", risk_options)

    df_detail = df.copy()
    if selected_risk != "すべて" and "churn_risk" in df_detail.columns:
        df_detail = df_detail[df_detail["churn_risk"] == selected_risk]

    st.dataframe(df_detail.reset_index(drop=True), use_container_width=True)
    st.caption(f"表示件数: {len(df_detail):,} 件")
