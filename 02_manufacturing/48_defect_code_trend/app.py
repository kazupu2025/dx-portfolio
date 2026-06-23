import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from analyze import analyze, REQUIRED_COLUMNS

st.set_page_config(page_title="工程別不良コード頻度・月次トレンド", layout="wide")

st.title("C-102 工程別不良コード頻度・月次トレンド")

# サイドバー
with st.sidebar:
    st.header("データ入力")

    # サンプルデータボタン
    if st.button("📊 サンプルデータを読み込む", use_container_width=True):
        sample_path = Path(__file__).parent / "sample_defect_code.csv"
        st.session_state.df = pd.read_csv(sample_path)
        st.success("サンプルデータを読み込みました")

    # CSVアップロード
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.df = df
            st.success("ファイルをアップロードしました")
        except Exception as e:
            st.error(f"エラー: {e}")

    # 工程フィルタ
    if "df" in st.session_state and not st.session_state.df.empty:
        processes = st.session_state.df["process"].unique()
        selected_processes = st.multiselect(
            "工程を選択（全工程を表示）",
            options=sorted(processes),
            default=sorted(processes)
        )

# データの検証と分析
if "df" in st.session_state and not st.session_state.df.empty:
    df = st.session_state.df

    # 工程フィルタを適用
    if "selected_processes" in locals():
        df = df[df["process"].isin(selected_processes)]

    # 必要な列の確認
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        st.error(f"必要な列が見つかりません: {', '.join(missing_cols)}")
    else:
        try:
            result = analyze(df)

            # KPIカード
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("総不良数", result["total_defects"])

            with col2:
                st.metric("最多不良コード", result["top_code"])

            with col3:
                st.metric("上位コード占有率(%)", f"{result['top_code_pct']:.1f}%")

            with col4:
                verdict_display = {
                    "good": ("✅ 良好", "green"),
                    "warning": ("⚠️ 注意", "orange"),
                    "alert": ("❌ 警告", "red")
                }
                status_text, status_color = verdict_display.get(result["verdict"], ("不明", "gray"))
                st.markdown(f"<div style='background-color: {status_color}; color: white; padding: 20px; border-radius: 10px; text-align: center;'><h3>{status_text}</h3></div>", unsafe_allow_html=True)

            # グラフ
            st.subheader("不良コード別分析")
            col1, col2 = st.columns(2)

            with col1:
                # 不良コード別 棒グラフ（件数）
                fig_count = px.bar(
                    result["code_df"],
                    x="defect_code",
                    y="count",
                    title="不良コード別 件数",
                    labels={"defect_code": "不良コード", "count": "件数"},
                    color="count",
                    color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig_count, use_container_width=True)

            with col2:
                # 不良コード別 棒グラフ（%）
                fig_pct = px.bar(
                    result["code_df"],
                    x="defect_code",
                    y="pct",
                    title="不良コード別 占有率(%)",
                    labels={"defect_code": "不良コード", "pct": "占有率(%)"},
                    color="pct",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig_pct, use_container_width=True)

            # 月次トレンド 折れ線グラフ
            st.subheader("月次トレンド分析")
            fig_trend = px.line(
                result["trend_df"],
                x="month",
                y="count",
                color="defect_code",
                title="月別不良コード発生数トレンド",
                labels={"month": "月", "count": "件数", "defect_code": "不良コード"},
                markers=True
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            # 工程別集計
            st.subheader("工程別集計")
            fig_process = px.bar(
                result["process_df"],
                x="process",
                y="count",
                title="工程別 不良発生数",
                labels={"process": "工程", "count": "件数"},
                color="count",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_process, use_container_width=True)

            # データテーブル
            with st.expander("📋 詳細データ"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**不良コード別集計**")
                    st.dataframe(result["code_df"], use_container_width=True)
                with col2:
                    st.write("**工程別集計**")
                    st.dataframe(result["process_df"], use_container_width=True)

        except Exception as e:
            st.error(f"分析エラー: {e}")

else:
    st.info("👈 左のサイドバーからサンプルデータを読み込むか、CSVをアップロードしてください")
