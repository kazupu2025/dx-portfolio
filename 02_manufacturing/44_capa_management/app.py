import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from analyze import analyze

st.set_page_config(page_title="CAPA完了率・期限遵守率レポート", layout="wide")
st.title("C-98 CAPA完了率・期限遵守率レポート")

sample_csv_path = Path(__file__).parent / "sample_capa.csv"

with st.sidebar:
    st.header("データ入力")

    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

    if st.button("サンプルデータを読み込む"):
        st.session_state.use_sample = True

    if uploaded_file is not None:
        st.session_state.use_sample = False
        df = pd.read_csv(uploaded_file)
    elif st.session_state.get("use_sample", False) or uploaded_file is None:
        try:
            df = pd.read_csv(sample_csv_path)
        except:
            st.error("サンプルデータが見つかりません")
            st.stop()

    st.success("✓ データを読み込みました")

result = analyze(df)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("完了率", f"{result['completion_rate']:.1f}%")

with col2:
    st.metric("期限遵守率", f"{result['on_time_rate']:.1f}%")

with col3:
    st.metric("超過件数", f"{result['overdue']} 件")

with col4:
    verdict_colors = {"good": "🟢", "warning": "🟡", "alert": "🔴"}
    verdict_labels = {"good": "良好", "warning": "注意", "alert": "警告"}
    st.metric("判定", f"{verdict_colors[result['verdict']]} {verdict_labels[result['verdict']]}")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("カテゴリ別件数")
    category_df = result["category_df"].sort_values("count", ascending=False)
    fig_category = px.bar(category_df, x="category", y="count", labels={"category": "カテゴリ", "count": "件数"})
    fig_category.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_category, use_container_width=True)

with col2:
    st.subheader("完了 / 未完了")
    completed = result["completed"]
    incomplete = result["total"] - completed
    fig_donut = go.Figure(data=[go.Pie(
        labels=["完了", "未完了"],
        values=[completed, incomplete],
        hole=0.3,
        marker=dict(colors=["#00CC88", "#FF6B6B"])
    )])
    fig_donut.update_layout(height=400)
    st.plotly_chart(fig_donut, use_container_width=True)

st.divider()

st.subheader("詳細データ")
display_df = df.copy()
st.dataframe(display_df, use_container_width=True)

with st.expander("統計サマリー"):
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        st.write(f"**総件数:** {result['total']}")
        st.write(f"**完了件数:** {result['completed']}")
    with summary_col2:
        st.write(f"**未完了件数:** {result['total'] - result['completed']}")
        st.write(f"**超過件数:** {result['overdue']}")
    with summary_col3:
        st.write(f"**期限内完了:** {int(result['completed'] * result['on_time_rate'] / 100)}")
        st.write(f"**期限超過完了:** {result['completed'] - int(result['completed'] * result['on_time_rate'] / 100)}")
