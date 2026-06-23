import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from io import StringIO
from analyze import analyze, REQUIRED_COLUMNS
from pathlib import Path

st.set_page_config(page_title="C-111 研修効果測定レポート", layout="wide")
st.title("C-111 研修効果測定レポート")

# ─────────────────────────────────────────
# サイドバー: CSVアップロード + サンプルデータ
# ─────────────────────────────────────────
with st.sidebar:
    st.header("データアップロード")

    # サンプルデータの読み込みボタン
    if st.button("📊 サンプルデータを読み込む"):
        sample_path = Path(__file__).parent / "sample_training.csv"
        if sample_path.exists():
            df_upload = pd.read_csv(sample_path)
            st.session_state["df_upload"] = df_upload
            st.success("サンプルデータを読み込みました")

    # CSVアップロード
    uploaded_file = st.file_uploader("CSV ファイルをアップロード", type=["csv"])
    if uploaded_file:
        try:
            df_upload = pd.read_csv(uploaded_file)
            st.session_state["df_upload"] = df_upload
            st.success("CSVファイルをアップロードしました")
        except Exception as e:
            st.error(f"エラー: {e}")

# ─────────────────────────────────────────
# データの初期化と分析実行
# ─────────────────────────────────────────
if "df_upload" not in st.session_state:
    st.info("📝 サイドバーからデータをアップロードするか、サンプルデータを読み込んでください")
    st.stop()

df = st.session_state["df_upload"]

# 列の確認
missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing_cols:
    st.error(f"❌ 必須列が不足しています: {missing_cols}")
    st.stop()

# 分析実行
result = analyze(df)

# ─────────────────────────────────────────
# KPIカード（4つ）
# ─────────────────────────────────────────
st.subheader("📊 KPI サマリー")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "平均スコア改善",
        f"{result['avg_improvement']:.1f} 点",
        delta=None
    )

with col2:
    st.metric(
        "改善率（平均）",
        f"{result['avg_improvement_rate']:.1f} %",
        delta=None
    )

with col3:
    st.metric(
        "総研修費用",
        f"¥{result['total_cost']:,.0f}",
        delta=None
    )

with col4:
    verdict_colors = {
        "good": "✅ Good",
        "warning": "⚠️ Warning",
        "alert": "❌ Alert"
    }
    st.metric(
        "総合評価",
        verdict_colors.get(result["verdict"], result["verdict"]),
        delta=None
    )

# ─────────────────────────────────────────
# 詳細KPI
# ─────────────────────────────────────────
st.subheader("📈 詳細 KPI")
col_a, col_b = st.columns(2)

with col_a:
    st.metric(
        "参加者総数",
        f"{result['total_participants']} 人",
        delta=None
    )

with col_b:
    st.metric(
        "費用対効果（1000円あたり）",
        f"{result['cost_efficiency']:.2f} 点",
        delta=None
    )

# ─────────────────────────────────────────
# グラフ1: 研修別効果ランキング（平均スコア改善）
# ─────────────────────────────────────────
st.subheader("📊 研修別効果ランキング")
training_df = result["training_df"]
fig1 = px.bar(
    training_df,
    x="training_name",
    y="avg_improvement",
    color="avg_improvement",
    color_continuous_scale="Viridis",
    labels={"avg_improvement": "平均スコア改善", "training_name": "研修名"},
    title="研修名別 平均スコア改善"
)
fig1.update_layout(showlegend=False, height=400)
st.plotly_chart(fig1, use_container_width=True)

# ─────────────────────────────────────────
# グラフ2: 研修前後スコア比較（grouped棒グラフ）
# ─────────────────────────────────────────
st.subheader("📈 研修前後スコア比較")
training_comparison = training_df[["training_name", "avg_pre", "avg_post"]].copy()
training_comparison = training_comparison.melt(
    id_vars=["training_name"],
    var_name="時点",
    value_name="スコア"
)
training_comparison["時点"] = training_comparison["時点"].map({"avg_pre": "研修前", "avg_post": "研修後"})

fig2 = px.bar(
    training_comparison,
    x="training_name",
    y="スコア",
    color="時点",
    barmode="group",
    labels={"training_name": "研修名", "スコア": "スコア"},
    title="研修名別 研修前後スコア比較"
)
fig2.update_layout(height=400)
st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────
# グラフ3: 部署別効果（棒グラフ）
# ─────────────────────────────────────────
st.subheader("🏢 部署別効果")
dept_df = result["dept_df"]
fig3 = px.bar(
    dept_df,
    x="department",
    y="avg_improvement",
    color="avg_improvement",
    color_continuous_scale="Plasma",
    labels={"avg_improvement": "平均スコア改善", "department": "部署"},
    title="部署別 平均スコア改善"
)
fig3.update_layout(showlegend=False, height=400)
st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────
# テーブル: 費用対効果データ
# ─────────────────────────────────────────
st.subheader("💰 費用対効果テーブル")
cost_table = training_df[[
    "training_name",
    "count",
    "avg_improvement",
    "total_cost",
]].copy()
cost_table.columns = ["研修名", "参加者数", "平均改善", "総費用"]
cost_table["1人あたりコスト"] = cost_table["総費用"] / cost_table["参加者数"]
cost_table["改善点あたりコスト"] = cost_table["総費用"] / (cost_table["平均改善"] * cost_table["参加者数"])

# 数値フォーマット
cost_table["総費用"] = cost_table["総費用"].apply(lambda x: f"¥{x:,.0f}")
cost_table["1人あたりコスト"] = cost_table["1人あたりコスト"].apply(lambda x: f"¥{x:,.0f}")
cost_table["改善点あたりコスト"] = cost_table["改善点あたりコスト"].apply(lambda x: f"¥{x:,.0f}")

st.dataframe(cost_table, use_container_width=True)

# ─────────────────────────────────────────
# 詳細データ表示
# ─────────────────────────────────────────
st.subheader("📋 詳細データ")
display_df = result["df"][[
    "employee_id",
    "name",
    "department",
    "training_name",
    "training_date",
    "pre_score",
    "post_score",
    "score_improvement",
    "improvement_rate",
    "training_cost",
]].copy()
display_df.columns = [
    "社員ID",
    "氏名",
    "部署",
    "研修名",
    "実施日",
    "研修前",
    "研修後",
    "改善点数",
    "改善率（%）",
    "研修費用"
]
display_df["改善率（%）"] = display_df["改善率（%）"].apply(lambda x: f"{x:.1f}%")
display_df["研修費用"] = display_df["研修費用"].apply(lambda x: f"¥{x:,.0f}")

st.dataframe(display_df, use_container_width=True)
