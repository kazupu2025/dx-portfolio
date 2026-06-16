"""
C-19: app.py
Streamlit ダッシュボード
タイトル: 小売 月次収益ダッシュボード
"""
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_FILE = os.path.join(BASE_DIR, "output", "cleaned_pnl_202401.csv")
SUMMARY_FILE = os.path.join(BASE_DIR, "output", "pnl_summary_202401.csv")
REPORT_FILE = os.path.join(BASE_DIR, "output", "analysis_report.md")

st.set_page_config(page_title="小売 月次収益ダッシュボード", layout="wide")
st.title("小売 月次収益ダッシュボード")


@st.cache_data
def load_data():
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    return df


@st.cache_data
def load_summary():
    df = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
    return df


if not os.path.isfile(CLEANED_FILE):
    st.error(f"データファイルが見つかりません: {CLEANED_FILE}")
    st.info("先に `cleanse.py` → `analyze.py` を実行してください。")
    st.stop()

df = load_data()
summary = load_summary()

# --- サイドバー: 店舗フィルター ---
st.sidebar.header("フィルター")
all_stores = sorted(df["store_id"].unique())
selected_stores = st.sidebar.multiselect("店舗選択", all_stores, default=all_stores)

filtered = df[df["store_id"].isin(selected_stores)] if selected_stores else df

# --- メトリクス ---
total_revenue = filtered["actual_revenue"].sum()
total_planned_revenue = filtered["planned_revenue"].sum()
total_gp = filtered["actual_gross_profit"].sum()
total_op = filtered["actual_operating_profit"].sum()
revenue_rate = total_revenue / total_planned_revenue if total_planned_revenue > 0 else 0
gp_margin = total_gp / total_revenue if total_revenue > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("売上合計", f"{total_revenue/1e6:.1f}M円")
col2.metric("粗利率", f"{gp_margin*100:.1f}%")
col3.metric("営業利益", f"{total_op/1e6:.1f}M円")
col4.metric("売上達成率", f"{revenue_rate*100:.1f}%")

st.markdown("---")

# --- グラフ1: 店舗別 売上実績vs予算 ---
st.subheader("店舗別 売上実績 vs 予算")
store_grp = filtered.groupby(["store_id", "store_name"]).agg(
    planned_revenue=("planned_revenue", "sum"),
    actual_revenue=("actual_revenue", "sum"),
).reset_index()

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=store_grp["store_name"], y=store_grp["planned_revenue"] / 1e6,
    name="売上予算", marker_color="#4C72B0"
))
fig1.add_trace(go.Bar(
    x=store_grp["store_name"], y=store_grp["actual_revenue"] / 1e6,
    name="売上実績", marker_color="#DD8452"
))
fig1.update_layout(
    barmode="group",
    xaxis_title="店舗",
    yaxis_title="金額（百万円）",
    legend=dict(orientation="h"),
    height=400,
)
st.plotly_chart(fig1, use_container_width=True)

# --- グラフ2: 月次 営業利益推移 ---
st.subheader("月次 営業利益推移")
trend = filtered.groupby("year_month").agg(
    planned_op=("planned_operating_profit", "sum"),
    actual_op=("actual_operating_profit", "sum"),
).reset_index().sort_values("year_month")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=trend["year_month"], y=trend["planned_op"] / 1e6,
    mode="lines+markers", name="予算", line=dict(color="#4C72B0", width=2)
))
fig2.add_trace(go.Scatter(
    x=trend["year_month"], y=trend["actual_op"] / 1e6,
    mode="lines+markers", name="実績", line=dict(color="#DD8452", width=2)
))
fig2.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
fig2.update_layout(
    xaxis_title="期間",
    yaxis_title="営業利益（百万円）",
    legend=dict(orientation="h"),
    height=400,
)
st.plotly_chart(fig2, use_container_width=True)

# --- グラフ3: 店舗別 利益フラグ分布 ---
st.subheader("店舗別 利益フラグ分布")
flag_grp = (
    filtered.groupby(["store_name", "profit_flag"])
    .size()
    .reset_index(name="週数")
)
fig3 = px.bar(
    flag_grp, x="store_name", y="週数", color="profit_flag",
    color_discrete_map={"達成": "#55A868", "未達": "#F0E442", "赤字": "#C44E52"},
    barmode="stack",
    labels={"store_name": "店舗", "profit_flag": "判定"},
    height=400,
)
st.plotly_chart(fig3, use_container_width=True)

# --- アラート一覧 ---
st.subheader("赤字・未達アラート")
alerts = filtered[filtered["profit_flag"].isin(["赤字", "未達"])][
    ["store_id", "store_name", "year_month", "actual_operating_profit", "planned_operating_profit", "profit_flag"]
].sort_values(["profit_flag", "store_id"])
if len(alerts) > 0:
    st.dataframe(alerts.reset_index(drop=True), use_container_width=True)
else:
    st.success("赤字・未達の週はありません。")

# --- レポート表示 ---
st.markdown("---")
st.subheader("分析レポート")
if os.path.isfile(REPORT_FILE):
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        st.markdown(f.read())
else:
    st.warning("analysis_report.md が見つかりません。analyze.py を実行してください。")
