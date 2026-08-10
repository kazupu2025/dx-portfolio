import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
# ── analyze.py インライン（Streamlit Cloud 互換）──
import pandas as pd

REQUIRED_COLUMNS = ["date", "customer", "category", "severity", "status"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly_df = df.groupby("month").size().reset_index(name="count")
    category_df = df.groupby("category").size().reset_index(name="count").sort_values("count", ascending=False)
    customer_df = df.groupby("customer").size().reset_index(name="count").sort_values("count", ascending=False)

    total_count = len(df)
    open_count = (df["status"] != "完了").sum()
    avg_monthly = monthly_df["count"].mean()

    if avg_monthly <= 5:
        verdict = "good"
    elif avg_monthly <= 10:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "monthly_df": monthly_df,
        "category_df": category_df,
        "customer_df": customer_df,
        "total_count": int(total_count),
        "open_count": int(open_count),
        "avg_monthly": float(avg_monthly),
        "top_category": category_df.iloc[0]["category"],
        "verdict": verdict,
    }

# ────────────────────────────────────────────────

st.title("C-96 顧客クレーム件数・原因分類 月次集計")

# Sidebar
st.sidebar.header("データ読み込み")

# Sample data button
if st.sidebar.button("サンプルデータを読み込む"):
    sample_path = Path(__file__).parent / "sample_customer_claims.csv"
    st.session_state.df = pd.read_csv(sample_path)
    st.session_state.filename = "sample_customer_claims.csv"

# CSV upload
uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type="csv")
if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.session_state.filename = uploaded_file.name

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None
    st.session_state.filename = None

# Check if data is loaded
if st.session_state.df is None:
    st.info("サイドバーからサンプルデータまたはCSVファイルを読み込んでください")
else:
    st.sidebar.write(f"読み込み済み: {st.session_state.filename}")

    # Analyze data
    result = analyze(st.session_state.df)

    # KPI Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="月平均件数",
            value=f"{result['avg_monthly']:.1f}",
            delta=f"総件数: {result['total_count']}"
        )

    with col2:
        st.metric(
            label="未完了件数",
            value=f"{result['open_count']}",
            delta=f"対応中のクレーム"
        )

    with col3:
        verdict_color = {"good": "🟢", "warning": "🟡", "alert": "🔴"}
        st.metric(
            label="最多カテゴリ",
            value=result['top_category'],
            delta=verdict_color[result['verdict']]
        )

    st.divider()

    # Monthly trend
    st.subheader("月次トレンド")
    fig_monthly = px.line(
        result['monthly_df'],
        x="month",
        y="count",
        markers=True,
        title="クレーム件数推移",
        labels={"month": "月", "count": "件数"}
    )
    fig_monthly.update_layout(hovermode="x unified")
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Category and Customer comparison
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("カテゴリ別クレーム件数")
        fig_category = px.bar(
            result['category_df'],
            x="category",
            y="count",
            title="原因分類別",
            labels={"category": "カテゴリ", "count": "件数"},
            color="count",
            color_continuous_scale="RdYlGn_r"
        )
        st.plotly_chart(fig_category, use_container_width=True)

    with col2:
        st.subheader("顧客別クレーム件数")
        fig_customer = px.bar(
            result['customer_df'],
            x="customer",
            y="count",
            title="顧客別",
            labels={"customer": "顧客", "count": "件数"},
            color="count",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_customer, use_container_width=True)

    st.divider()

    # Raw data
    st.subheader("生データ")
    st.dataframe(st.session_state.df, use_container_width=True)
