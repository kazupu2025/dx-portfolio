import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from analyze import analyze

st.set_page_config(page_title="品質フィードバックループ", layout="wide")

st.title("市場品質フィードバックループ分析")

# Sidebar: Data input
with st.sidebar:
    st.header("データ入力")

    # Sample data button
    if st.button("サンプルデータを読み込む"):
        sample_path = Path(__file__).parent / "sample_feedback_loop.csv"
        st.session_state.df = pd.read_csv(sample_path)
        st.success("サンプルデータを読み込みました")

    # File uploader
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file is not None:
        try:
            st.session_state.df = pd.read_csv(uploaded_file)
            st.success("ファイルをアップロードしました")
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {e}")

# Check if data is loaded
if "df" not in st.session_state or st.session_state.df is None:
    st.info("サイドバーからサンプルデータをロードするか、CSVをアップロードしてください")
    st.stop()

# Analyze data
df = st.session_state.df
try:
    result = analyze(df)
except Exception as e:
    st.error(f"分析エラー: {e}")
    st.stop()

# KPI Cards
st.header("KPI指標")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "平均改善率",
        f"{result['avg_improvement']:.1f}%",
        delta=f"{result['avg_improvement']-30:.1f}% vs 目標30%",
    )

with col2:
    st.metric("平均リードタイム（日数）", f"{result['avg_lead_time']:.1f}日")

with col3:
    st.metric("総ケース数", result["total_cases"])

with col4:
    verdict_text = {"good": "良好", "warning": "注意", "alert": "警告"}
    verdict_color = {"good": "🟢", "warning": "🟡", "alert": "🔴"}
    st.metric("判定", f"{verdict_color[result['verdict']]} {verdict_text[result['verdict']]}")

st.divider()

# Feedback Loop Diagram (Sankey)
st.header("フィードバックループフロー")

# Create aggregated flow data
df_analysis = result["df"]

# Claim → Root Process
claim_process = df_analysis.groupby(["claim_type", "root_process"]).size().reset_index(name="count")
# Root Process → Action
process_action = (
    df_analysis.groupby(["root_process", "action_taken"]).size().reset_index(name="count")
)

# Create nodes and links for Sankey
claim_types = claim_process["claim_type"].unique().tolist()
root_processes = (
    pd.concat([claim_process["root_process"], process_action["root_process"]]).unique().tolist()
)
actions = process_action["action_taken"].unique().tolist()

# All nodes
all_nodes = ["クレーム"] + claim_types + root_processes + actions + ["効果確認"]
node_indices = {node: i for i, node in enumerate(all_nodes)}

# Build links
source_indices = []
target_indices = []
values = []
link_colors = []

# Claim → Root Process
for _, row in claim_process.iterrows():
    source_indices.append(node_indices.get("クレーム", 0))
    target_indices.append(node_indices.get(row["root_process"], 0))
    values.append(row["count"])
    link_colors.append("rgba(100, 149, 237, 0.4)")  # Cornflower blue

# Root Process → Action
for _, row in process_action.iterrows():
    source_indices.append(node_indices.get(row["root_process"], 0))
    target_indices.append(node_indices.get(row["action_taken"], 0))
    values.append(row["count"])
    link_colors.append("rgba(144, 238, 144, 0.4)")  # Light green

# Action → 効果確認
action_counts = df_analysis.groupby("action_taken").size()
for action, count in action_counts.items():
    source_indices.append(node_indices.get(action, 0))
    target_indices.append(node_indices.get("効果確認", 0))
    values.append(count)
    link_colors.append("rgba(255, 165, 0, 0.4)")  # Orange

fig_sankey = go.Figure(
    data=[
        go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color=link_colors,
            ),
        )
    ]
)
fig_sankey.update_layout(title="市場クレーム → 改善 → 効果確認フロー", height=500)
st.plotly_chart(fig_sankey, use_container_width=True)

st.divider()

# Process improvement effectiveness
st.header("工程別改善効果")
process_df = result["process_df"]
fig_process = px.bar(
    process_df,
    x="root_process",
    y="avg_improvement",
    title="工程別平均改善率",
    labels={"root_process": "工程", "avg_improvement": "改善率(%)"},
    color="avg_improvement",
    color_continuous_scale="RdYlGn",
)
st.plotly_chart(fig_process, use_container_width=True)

st.divider()

# Action effectiveness ranking
st.header("改善策別効果ランキング")
action_df = result["action_df"]
st.dataframe(
    action_df.rename(
        columns={
            "action_taken": "改善策",
            "count": "実施件数",
            "avg_improvement": "平均改善率(%)",
        }
    ).sort_values("平均改善率(%)", ascending=False),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# Product claim volume
st.header("製品別クレーム件数")
product_df = result["product_df"]
fig_product = px.bar(
    product_df,
    x="product",
    y="claim_count",
    title="製品別クレーム件数",
    labels={"product": "製品", "claim_count": "クレーム件数"},
    color="avg_improvement",
    color_continuous_scale="Blues",
)
st.plotly_chart(fig_product, use_container_width=True)

st.divider()

# Detailed data table
st.header("詳細データ")
display_df = (
    result["df"]
    .copy()
    .round(
        {
            "before_rate": 1,
            "after_rate": 1,
            "improvement_rate": 1,
            "lead_time_days": 0,
        }
    )
    .rename(
        columns={
            "date": "クレーム日",
            "product": "製品",
            "claim_type": "クレーム種類",
            "root_process": "工程",
            "action_taken": "改善策",
            "before_rate": "改善前不良率(%)",
            "after_rate": "改善後不良率(%)",
            "action_date": "改善実施日",
            "improvement_rate": "改善率(%)",
            "lead_time_days": "リードタイム(日)",
        }
    )
)
st.dataframe(display_df, use_container_width=True, hide_index=True)
