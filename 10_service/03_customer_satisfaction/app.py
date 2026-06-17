# app.py — Streamlit ダッシュボード（C-36 顧客満足度）
# encoding: utf-8

from pathlib import Path

import pandas as pd
import streamlit as st

OUTPUT_DIR = Path(__file__).parent / "output"
CLEANED_FILE = OUTPUT_DIR / "cleaned_satisfaction_202401.csv"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
CHARTS_DIR = OUTPUT_DIR / "charts"

st.set_page_config(page_title="顧客満足度ダッシュボード", page_icon="⭐", layout="wide")
st.title("⭐ サービス 顧客満足度ダッシュボード")

# ── データロード ────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    if not CLEANED_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")


df_all = load_data()

if df_all.empty:
    st.error(f"データが見つかりません。先に cleanse.py を実行してください。\n対象: {CLEANED_FILE}")
    st.stop()

# ── サイドバー: サービス区分フィルター ───────────────────────────────────
st.sidebar.header("フィルター")
all_services = sorted(df_all["service_type"].dropna().unique().tolist())
selected_services = st.sidebar.multiselect(
    "サービス区分",
    options=all_services,
    default=all_services,
)

df = df_all[df_all["service_type"].isin(selected_services)] if selected_services else df_all.copy()

# ── KPI ────────────────────────────────────────────────────────────────────
total = len(df)
avg_csat = df["csat_score"].mean() if total > 0 else 0.0
promoters = (df["nps_category"] == "推奨者").sum()
detractors = (df["nps_category"] == "批判者").sum()
nps_score = round((promoters / total - detractors / total) * 100, 1) if total > 0 else 0.0
satisfaction_rate = round((df["satisfaction_flag"] == "満足").mean() * 100, 1) if total > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("総回答数", f"{total:,} 件")
col2.metric("平均CSAT", f"{avg_csat:.2f} / 5.0")
col3.metric("NPS", f"{nps_score}")
col4.metric("満足率", f"{satisfaction_rate}%")

st.divider()

# ── タブ ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["サービス別 CSAT", "NPS 分布", "担当者別満足度"])

with tab1:
    st.subheader("サービス区分別 CSAT 平均")
    chart_path = CHARTS_DIR / "bar_service_csat.png"
    if chart_path.exists():
        st.image(str(chart_path))
    else:
        st.info("グラフが見つかりません。visualize.py を実行してください。")

    svc_tbl = (
        df.groupby("service_type")["csat_score"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "平均CSAT", "count": "回答数"})
        .round({"平均CSAT": 2})
        .sort_values("平均CSAT", ascending=False)
        .reset_index()
        .rename(columns={"service_type": "サービス区分"})
    )
    st.dataframe(svc_tbl, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("NPS 区分別件数")
    chart_path = CHARTS_DIR / "bar_nps_category.png"
    if chart_path.exists():
        st.image(str(chart_path))
    else:
        st.info("グラフが見つかりません。visualize.py を実行してください。")

    nps_tbl = (
        df["nps_category"]
        .value_counts()
        .reindex(["推奨者", "中立者", "批判者"], fill_value=0)
        .reset_index()
        .rename(columns={"nps_category": "区分", "count": "件数"})
    )
    nps_tbl["比率"] = (nps_tbl["件数"] / total * 100).round(1).astype(str) + "%"
    st.dataframe(nps_tbl, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("担当者別 平均満足度")
    chart_path = CHARTS_DIR / "bar_agent_satisfaction.png"
    if chart_path.exists():
        st.image(str(chart_path))
    else:
        st.info("グラフが見つかりません。visualize.py を実行してください。")

    agent_tbl = (
        df.groupby("agent")["csat_score"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "平均CSAT", "count": "回答数"})
        .round({"平均CSAT": 2})
        .sort_values("平均CSAT", ascending=False)
        .reset_index()
        .rename(columns={"agent": "担当者"})
    )
    st.dataframe(agent_tbl, use_container_width=True, hide_index=True)

st.divider()

# ── 不満顧客リスト ──────────────────────────────────────────────────────────
st.subheader("不満顧客リスト (satisfaction_flag = 不満)")
dissatisfied = df[df["satisfaction_flag"] == "不満"][
    ["response_date", "customer_code", "service_type", "agent",
     "csat_score", "nps", "nps_category"]
].sort_values("csat_score")
st.dataframe(dissatisfied, use_container_width=True, hide_index=True)

# ── 分析レポート Expander ───────────────────────────────────────────────────
with st.expander("分析レポートを表示", expanded=False):
    if REPORT_FILE.exists():
        report_text = REPORT_FILE.read_text(encoding="utf-8")
        st.markdown(report_text)
    else:
        st.info("レポートが見つかりません。analyze.py を実行してください。")
