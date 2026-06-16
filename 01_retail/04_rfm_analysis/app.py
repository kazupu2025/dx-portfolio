# -*- coding: utf-8 -*-
"""
app.py
小売 顧客RFM分析ダッシュボード（Streamlit）
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
RFM_CSV = OUTPUT_DIR / "customer_rfm_202401.csv"
CLEANED_CSV = OUTPUT_DIR / "cleaned_purchases_202401.csv"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"

SEGMENT_ORDER = ["優良顧客", "成長顧客", "離反リスク", "休眠顧客"]
SEGMENT_COLORS = {
    "優良顧客": "#2196F3",
    "成長顧客": "#4CAF50",
    "離反リスク": "#FF9800",
    "休眠顧客": "#9E9E9E",
}

st.set_page_config(
    page_title="小売 顧客RFM分析ダッシュボード",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 小売 顧客RFM分析ダッシュボード")
st.caption("基準日: 2024-02-01 | システムID: C-27")


@st.cache_data
def load_rfm():
    if not RFM_CSV.exists():
        return None
    return pd.read_csv(RFM_CSV, encoding="utf-8-sig")


@st.cache_data
def load_cleaned():
    if not CLEANED_CSV.exists():
        return None
    return pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")


rfm = load_rfm()
df_cleaned = load_cleaned()

if rfm is None or df_cleaned is None:
    st.error("分析データが見つかりません。先に _gen_sample_data.py → cleanse.py → analyze.py を実行してください。")
    st.stop()

# ---- セグメントフィルター ----
st.sidebar.header("フィルター設定")
selected_segments = st.sidebar.multiselect(
    "セグメント選択",
    options=SEGMENT_ORDER,
    default=SEGMENT_ORDER,
)

rfm_filtered = rfm[rfm["segment"].isin(selected_segments)]

# ---- KPI ----
col1, col2, col3, col4 = st.columns(4)

total_customers = len(rfm_filtered)
premium_count = len(rfm_filtered[rfm_filtered["segment"] == "優良顧客"])
avg_frequency = rfm_filtered["frequency"].mean() if len(rfm_filtered) > 0 else 0
avg_monetary = rfm_filtered["monetary"].mean() if len(rfm_filtered) > 0 else 0

col1.metric("分析顧客数", f"{total_customers:,}名")
col2.metric("優良顧客数", f"{premium_count:,}名", f"{premium_count/max(total_customers,1)*100:.1f}%")
col3.metric("平均購買回数", f"{avg_frequency:.1f}回")
col4.metric("平均購買金額（累計）", f"{avg_monetary:,.0f}円")

st.divider()

# ---- 3タブ ----
tab1, tab2, tab3 = st.tabs(["セグメント分布", "RFMスコア散布図", "カテゴリ別売上"])

with tab1:
    st.subheader("セグメント別顧客数")
    seg_counts = (
        rfm_filtered["segment"]
        .value_counts()
        .reindex(SEGMENT_ORDER, fill_value=0)
        .reset_index()
    )
    seg_counts.columns = ["segment", "count"]

    fig_bar = px.bar(
        seg_counts,
        x="segment",
        y="count",
        color="segment",
        color_discrete_map=SEGMENT_COLORS,
        text="count",
        title="セグメント別顧客数",
        labels={"segment": "セグメント", "count": "顧客数（名）"},
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(showlegend=False, height=420)
    st.plotly_chart(fig_bar, use_container_width=True)

    # 割合パイチャート
    fig_pie = px.pie(
        seg_counts,
        names="segment",
        values="count",
        color="segment",
        color_discrete_map=SEGMENT_COLORS,
        title="セグメント構成比",
    )
    fig_pie.update_layout(height=380)
    st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("Frequency vs Monetary（RFMスコア散布図）")
    fig_scatter = px.scatter(
        rfm_filtered,
        x="frequency",
        y="monetary",
        color="segment",
        color_discrete_map=SEGMENT_COLORS,
        size="rfm_total",
        hover_data=["customer_code", "r_score", "f_score", "m_score", "rfm_total"],
        title="Frequency vs Monetary（セグメント別）",
        labels={
            "frequency": "購買回数（Frequency）",
            "monetary": "累計購買金額（Monetary）",
            "segment": "セグメント",
        },
        category_orders={"segment": SEGMENT_ORDER},
    )
    fig_scatter.update_layout(height=480)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # RFMスコア分布
    col_r, col_f, col_m = st.columns(3)
    with col_r:
        st.markdown("**Recency スコア分布**")
        st.bar_chart(rfm_filtered["r_score"].value_counts().sort_index())
    with col_f:
        st.markdown("**Frequency スコア分布**")
        st.bar_chart(rfm_filtered["f_score"].value_counts().sort_index())
    with col_m:
        st.markdown("**Monetary スコア分布**")
        st.bar_chart(rfm_filtered["m_score"].value_counts().sort_index())

with tab3:
    st.subheader("カテゴリ別累計売上")
    # フィルターされた顧客のみに絞る
    filtered_customers = rfm_filtered["customer_code"].tolist()
    df_cat = df_cleaned[df_cleaned["customer_code"].isin(filtered_customers)]

    cat_sales = df_cat.groupby("category")["amount"].sum().sort_values(ascending=False).reset_index()
    cat_sales.columns = ["category", "amount"]

    fig_cat = px.bar(
        cat_sales,
        x="category",
        y="amount",
        text=cat_sales["amount"].apply(lambda x: f"{x:,.0f}"),
        title="カテゴリ別累計売上",
        labels={"category": "カテゴリ", "amount": "累計売上（円）"},
        color="amount",
        color_continuous_scale="Blues",
    )
    fig_cat.update_traces(textposition="outside")
    fig_cat.update_layout(showlegend=False, height=420, coloraxis_showscale=False)
    st.plotly_chart(fig_cat, use_container_width=True)

    # 店舗別売上
    st.markdown("**店舗別累計売上**")
    store_sales = df_cat.groupby("store_name")["amount"].sum().sort_values(ascending=False).reset_index()
    store_sales.columns = ["store_name", "amount"]
    fig_store = px.pie(
        store_sales,
        names="store_name",
        values="amount",
        title="店舗別売上構成比",
    )
    fig_store.update_layout(height=360)
    st.plotly_chart(fig_store, use_container_width=True)

st.divider()

# ---- 顧客詳細テーブル ----
st.subheader("顧客詳細テーブル（セグメント別）")
display_df = rfm_filtered[
    ["customer_code", "segment", "recency", "frequency", "monetary", "r_score", "f_score", "m_score", "rfm_total"]
].sort_values("rfm_total", ascending=False)

display_df = display_df.rename(columns={
    "customer_code": "顧客コード",
    "segment": "セグメント",
    "recency": "Recency（日）",
    "frequency": "Frequency（回）",
    "monetary": "Monetary（円）",
    "r_score": "Rスコア",
    "f_score": "Fスコア",
    "m_score": "Mスコア",
    "rfm_total": "合計スコア",
})

st.dataframe(display_df, use_container_width=True, height=320)

# ---- 分析レポート expander ----
with st.expander("分析レポート（Markdown）を見る"):
    if REPORT_FILE.exists():
        report_text = REPORT_FILE.read_text(encoding="utf-8")
        st.markdown(report_text)
    else:
        st.warning("analysis_report.md が見つかりません。analyze.py を実行してください。")
