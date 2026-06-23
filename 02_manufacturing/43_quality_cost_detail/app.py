import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from analyze import analyze

st.set_page_config(page_title="品質コスト明細集計", layout="wide")
st.title("品質コスト明細集計")
st.markdown("予防/評価/内部失敗/外部失敗コストの月別分析")

with st.sidebar:
    st.header("データ入力")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("サンプルデータを読み込む"):
            st.session_state.df = pd.read_csv(Path(__file__).parent / "sample_quality_cost.csv")
    with col2:
        uploaded_file = st.file_uploader("CSVをアップロード", type="csv")
        if uploaded_file:
            st.session_state.df = pd.read_csv(uploaded_file)

if "df" not in st.session_state:
    st.info("サイドバーからサンプルデータを読み込むか、CSVをアップロードしてください。")
else:
    df = st.session_state.df

    try:
        result = analyze(df)

        st.subheader("KPI概要")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "総コスト",
                f"¥{result['total_cost']:,.0f}",
            )

        with col2:
            failure_ratio = result["failure_ratio"]
            st.metric(
                "失敗コスト比率",
                f"{failure_ratio:.1f}%",
            )

        with col3:
            verdict_label = {
                "good": "良好 ✓",
                "warning": "注意 ⚠",
                "alert": "要対応 ✕"
            }
            st.metric(
                "判定",
                verdict_label.get(result["verdict"], "不明"),
            )

        st.divider()
        st.subheader("カテゴリ別コスト（円グラフ）")

        category_df = result["category_df"]
        fig_pie = px.pie(
            category_df,
            values="total_amount",
            names="cost_category",
            title="コスト配分",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.subheader("月別推移（積み上げ棒グラフ）")

        trend_df = result["trend_df"]
        fig_bar = px.bar(
            trend_df,
            x="month",
            y=["予防コスト", "評価コスト", "内部失敗コスト", "外部失敗コスト"],
            title="月別コスト推移",
            labels={"value": "金額（円）", "month": "月"},
            barmode="stack",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.subheader("詳細データ")

        tab1, tab2 = st.tabs(["カテゴリ別集計", "月別詳細"])

        with tab1:
            st.dataframe(
                category_df.assign(**{"total_amount": lambda x: x["total_amount"].apply(lambda v: f"¥{v:,.0f}")}),
                use_container_width=True,
            )

        with tab2:
            st.dataframe(trend_df, use_container_width=True)

    except Exception as e:
        st.error(f"分析エラー: {e}")
