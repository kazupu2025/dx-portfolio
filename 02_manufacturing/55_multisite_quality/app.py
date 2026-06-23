import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import numpy as np
from analyze import analyze, REQUIRED_COLUMNS

# Set page config
st.set_page_config(
    page_title="多拠点リアルタイム品質比較ダッシュボード",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🏭 多拠点リアルタイム品質比較ダッシュボード")
st.markdown("複数拠点の品質KPIを一画面で横断比較し、ベンチマーク・ランキング・トレンドを表示します。")

# Sidebar
with st.sidebar:
    st.header("⚙️ 設定")

    # Upload CSV or use sample data
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
    else:
        if st.button("📊 サンプルデータを読み込む"):
            sample_path = Path(__file__).parent / "sample_multisite_quality.csv"
            df = pd.read_csv(sample_path)
            st.session_state["df"] = df
            st.success("サンプルデータを読み込みました")

    # Get df from session state or use uploaded
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.session_state["df"] = df
    elif "df" not in st.session_state:
        st.info("サンプルデータボタンをクリックするか、CSVをアップロードしてください")
        st.stop()
    else:
        df = st.session_state["df"]

    # Validate columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        st.error(f"必要な列が不足しています: {missing_cols}")
        st.stop()

    # Sidebar filters
    st.markdown("---")
    st.subheader("フィルタ")

    # Site multiselect
    available_sites = sorted(df["site"].unique())
    selected_sites = st.multiselect(
        "拠点を選択 (複数選択可)",
        available_sites,
        default=available_sites
    )

    # KPI selector
    st.markdown("---")
    st.subheader("表示KPI選択")
    show_radar = st.checkbox("📊 拠点別KPI比較(レーダーチャート)", value=True)
    show_trend = st.checkbox("📈 月次不良率トレンド", value=True)
    show_comparison = st.checkbox("📉 拠点別詳細KPI比較", value=True)

# Filter data by selected sites
df_filtered = df[df["site"].isin(selected_sites)].copy()

if df_filtered.empty:
    st.warning("選択された拠点にデータがありません")
    st.stop()

# Run analysis
result = analyze(df_filtered)
site_df = result["site_df"]
trend_df = result["trend_df"]
best_site = result["best_site"]
worst_site = result["worst_site"]
avg_defect = result["avg_defect"]
n_sites = result["n_sites"]
verdict = result["verdict"]

# KPI Cards
st.markdown("---")
st.subheader("📊 主要KPI")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🥇 最優良拠点",
        value=best_site,
        delta=f"スコア: {site_df.iloc[0]['score']:.1f}"
    )

with col2:
    st.metric(
        label="🔴 最低拠点",
        value=worst_site,
        delta=f"スコア: {site_df.iloc[-1]['score']:.1f}"
    )

with col3:
    st.metric(
        label="📌 平均不良率",
        value=f"{avg_defect:.2f}%",
        delta=f"拠点数: {n_sites}"
    )

with col4:
    # Color based on verdict
    verdict_display = {
        "good": "✅ 良好",
        "warning": "⚠️ 要注視",
        "alert": "🔴 要改善"
    }
    st.metric(
        label="判定",
        value=verdict_display.get(verdict, verdict),
        delta=f"レベル: {verdict}"
    )

# Site Ranking Table
st.markdown("---")
st.subheader("🏆 拠点ランキング（スコア付き）")

ranking_display = site_df[[
    "site", "avg_defect_rate", "avg_cpk", "total_claims", "avg_yield", "score"
]].copy()
ranking_display.columns = ["拠点", "平均不良率(%)", "平均Cpk", "累計クレーム数", "平均歩留まり率(%)", "総合スコア"]

# Style the table
def highlight_score(s):
    return ["background-color: #90EE90" if v > 70 else "background-color: #FFB6C1" if v < 40 else "" for v in s]

styled_df = ranking_display.style.format({
    "平均不良率(%)": "{:.2f}",
    "平均Cpk": "{:.2f}",
    "平均歩留まり率(%)": "{:.2f}",
    "総合スコア": "{:.1f}"
}).apply(highlight_score, subset=["総合スコア"])

st.dataframe(styled_df, use_container_width=True)

# Radar chart
if show_radar and len(selected_sites) > 1:
    st.markdown("---")
    st.subheader("📊 拠点別KPI比較（レーダーチャート）")

    # Normalize metrics to 0-100 scale for radar chart
    radar_df = site_df[["site"]].copy()
    radar_df["不良率(逆)"] = (1 - site_df["avg_defect_rate"] / site_df["avg_defect_rate"].max()) * 100
    radar_df["Cpk指数"] = (site_df["avg_cpk"] / site_df["avg_cpk"].max()) * 100
    radar_df["クレーム対応"] = (1 - site_df["total_claims"] / (site_df["total_claims"].max() + 1)) * 100
    radar_df["歩留まり率"] = (site_df["avg_yield"] / 100) * 100

    fig = go.Figure()

    for idx, row in radar_df.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row["不良率(逆)"], row["Cpk指数"], row["クレーム対応"], row["歩留まり率"]],
            theta=["不良率(逆)", "Cpk指数", "クレーム対応", "歩留まり率"],
            fill="toself",
            name=row["site"],
            line=dict(width=2)
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=500,
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

# Trend chart
if show_trend:
    st.markdown("---")
    st.subheader("📈 月次不良率トレンド（拠点別）")

    # Filter trend data by selected sites
    trend_filtered = trend_df[trend_df["site"].isin(selected_sites)].copy()

    fig = px.line(
        trend_filtered,
        x="month",
        y="defect_rate",
        color="site",
        markers=True,
        title="月次不良率トレンド",
        labels={"defect_rate": "不良率(%)", "month": "月"},
        height=400
    )

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# Detailed KPI comparison bar chart
if show_comparison:
    st.markdown("---")
    st.subheader("📉 拠点別詳細KPI比較")

    # Create subplots for 4 KPIs
    col1, col2 = st.columns(2)

    with col1:
        # Defect rate
        fig1 = px.bar(
            site_df,
            x="site",
            y="avg_defect_rate",
            title="平均不良率(%)",
            labels={"avg_defect_rate": "不良率(%)", "site": "拠点"},
            height=350,
            color="avg_defect_rate",
            color_continuous_scale="RdYlGn_r"
        )
        fig1.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

        # Cpk
        fig3 = px.bar(
            site_df,
            x="site",
            y="avg_cpk",
            title="平均Cpk指数",
            labels={"avg_cpk": "Cpk", "site": "拠点"},
            height=350,
            color="avg_cpk",
            color_continuous_scale="Viridis"
        )
        fig3.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        # Claims
        fig2 = px.bar(
            site_df,
            x="site",
            y="total_claims",
            title="累計クレーム件数",
            labels={"total_claims": "クレーム数", "site": "拠点"},
            height=350,
            color="total_claims",
            color_continuous_scale="Reds"
        )
        fig2.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        # Yield rate
        fig4 = px.bar(
            site_df,
            x="site",
            y="avg_yield",
            title="平均歩留まり率(%)",
            labels={"avg_yield": "歩留まり率(%)", "site": "拠点"},
            height=350,
            color="avg_yield",
            color_continuous_scale="Greens"
        )
        fig4.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.markdown("*データ最終更新: 2024年12月*")
