import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from analyze import analyze

# ページ設定
st.set_page_config(page_title="工程進捗・原価差異レポート", layout="wide")

# タイトル
st.title("🏗️ 工程進捗・原価差異レポート")
st.markdown("工事プロジェクトの進捗状況と原価差異を可視化します")

# ============================================================================
# サイドバー
# ============================================================================
st.sidebar.header("📥 データ入力")

# サンプルデータ読み込み
SAMPLE_FILE = Path(__file__).parent / "sample_progress_cost.csv"

uploaded_file = st.sidebar.file_uploader(
    "CSVファイルをアップロード",
    type="csv",
    help="列: project_id, project_name, phase, planned_start, planned_end, actual_start, actual_end, planned_cost, actual_cost, progress_pct"
)

# データの取得
if uploaded_file:
    df_input = pd.read_csv(uploaded_file)
    st.sidebar.success("✅ ファイルアップロード完了")
elif SAMPLE_FILE.exists():
    df_input = pd.read_csv(SAMPLE_FILE)
    st.sidebar.info("📊 サンプルデータを使用中")
else:
    st.error("❌ サンプルデータが見つかりません")
    st.stop()

# 分析実行
result = analyze(df_input)

# プロジェクト選択フィルタ
st.sidebar.markdown("---")
st.sidebar.header("🔍 フィルタ")
selected_projects = st.sidebar.multiselect(
    "プロジェクトを選択（複数選択可）",
    options=result["project_df"]["project_name"].unique(),
    default=result["project_df"]["project_name"].unique()
)

# 選択されたプロジェクトでデータをフィルタ
df_filtered = result["df"][result["df"]["project_name"].isin(selected_projects)]
project_df_filtered = result["project_df"][result["project_df"]["project_name"].isin(selected_projects)]

# ============================================================================
# KPIカード
# ============================================================================
st.markdown("---")
st.header("📊 KPI ダッシュボード")

col1, col2, col3, col4 = st.columns(4)

# 計画総額
with col1:
    st.metric(
        "計画総額",
        f"¥{result['total_planned']/1e6:.1f}M",
        delta=None,
        delta_color="off"
    )

# 実績総額
with col2:
    st.metric(
        "実績総額",
        f"¥{result['total_actual']/1e6:.1f}M",
        delta=f"¥{(result['total_actual']-result['total_planned'])/1e6:.1f}M",
        delta_color="inverse" if result["overall_variance_pct"] > 0 else "off"
    )

# 原価超過率
with col3:
    variance_pct = result["overall_variance_pct"]
    color = "🔴" if variance_pct > 15 else "🟡" if variance_pct > 5 else "🟢"
    st.metric(
        "原価超過率",
        f"{variance_pct:.1f}%",
        delta=None,
        delta_color="off",
        help=f"{color} {result['verdict'].upper()}"
    )

# 判定
with col4:
    verdict_emoji = {
        "good": "🟢 GOOD",
        "warning": "🟡 WARNING",
        "alert": "🔴 ALERT"
    }
    st.metric(
        "判定",
        verdict_emoji.get(result["verdict"], "？"),
        delta=None,
        delta_color="off"
    )

st.markdown(f"**平均開始遅延**: {result['avg_delay']:.1f}日 | **平均進捗率**: {result['avg_progress']:.1f}%")

# ============================================================================
# プロジェクト別原価差異（棒グラフ）
# ============================================================================
st.markdown("---")
st.header("📈 プロジェクト別原価差異")

if len(project_df_filtered) > 0:
    # 色分け: 範囲内（グリーン）vs 超過（レッド）
    colors = [
        "#2ecc71" if v <= 5 else "#f39c12" if v <= 15 else "#e74c3c"
        for v in project_df_filtered["total_variance_pct"]
    ]

    fig_variance = px.bar(
        project_df_filtered,
        x="project_name",
        y="total_variance_pct",
        title="プロジェクト別原価差異率",
        labels={"project_name": "プロジェクト", "total_variance_pct": "原価差異率（%）"},
        text="total_variance_pct",
        color="total_variance_pct"
    )
    fig_variance.update_traces(
        marker=dict(color=colors),
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )
    fig_variance.add_hline(y=5, line_dash="dash", line_color="green", annotation_text="目標（±5%）")
    fig_variance.update_layout(showlegend=False, hovermode="x unified")
    st.plotly_chart(fig_variance, use_container_width=True)

    # プロジェクト別詳細テーブル
    st.subheader("プロジェクト別集計")
    display_df = project_df_filtered[[
        "project_name", "total_planned", "total_actual", "total_variance_pct", "avg_progress", "phase_count"
    ]].copy()
    display_df["total_planned"] = display_df["total_planned"].apply(lambda x: f"¥{x/1e6:.1f}M")
    display_df["total_actual"] = display_df["total_actual"].apply(lambda x: f"¥{x/1e6:.1f}M")
    display_df["total_variance_pct"] = display_df["total_variance_pct"].apply(lambda x: f"{x:.1f}%")
    display_df["avg_progress"] = display_df["avg_progress"].apply(lambda x: f"{x:.0f}%")
    display_df.columns = ["プロジェクト", "計画額", "実績額", "差異率", "進捗率", "フェーズ数"]

    st.dataframe(display_df, use_container_width=True)
else:
    st.warning("⚠️ 選択されたプロジェクトがありません")

# ============================================================================
# 工程別進捗（ガントチャート風タイムライン）
# ============================================================================
st.markdown("---")
st.header("📅 工程別進捗（タイムライン）")

if len(df_filtered) > 0:
    # Plotly timeline用にデータを準備
    df_gantt = df_filtered[[
        "project_name", "phase", "planned_start", "planned_end", "actual_start", "actual_end", "progress_pct"
    ]].copy()
    df_gantt = df_gantt.sort_values(["project_name", "planned_start"])

    # ガントチャート（計画 vs 実績）
    fig_gantt = go.Figure()

    for idx, row in df_gantt.iterrows():
        project = f"{row['project_name']} - {row['phase']}"

        # 計画期間
        if pd.notna(row["planned_start"]) and pd.notna(row["planned_end"]):
            fig_gantt.add_trace(go.Scatter(
                x=[row["planned_start"], row["planned_end"]],
                y=[project, project],
                mode="lines",
                name="計画期間",
                line=dict(color="lightblue", width=8),
                hovertemplate=f"計画: {row['planned_start'].date()} → {row['planned_end'].date()}<extra></extra>"
            ))

        # 実績期間
        if pd.notna(row["actual_start"]):
            actual_end = row["actual_end"] if pd.notna(row["actual_end"]) else pd.Timestamp.now()
            fig_gantt.add_trace(go.Scatter(
                x=[row["actual_start"], actual_end],
                y=[project, project],
                mode="lines",
                name="実績期間",
                line=dict(color="orange", width=8),
                hovertemplate=f"実績: {row['actual_start'].date()} → {actual_end.date()}<extra></extra>"
            ))

    fig_gantt.update_layout(
        title="工程別進捗（計画 vs 実績）",
        xaxis_title="日付",
        yaxis_title="プロジェクト・工程",
        hovermode="closest",
        height=400 + len(df_gantt) * 25
    )
    st.plotly_chart(fig_gantt, use_container_width=True)
else:
    st.warning("⚠️ 表示するデータがありません")

# ============================================================================
# フェーズ別工期遅延テーブル
# ============================================================================
st.markdown("---")
st.header("⏰ フェーズ別工期遅延")

if len(df_filtered) > 0:
    phase_delay_df = df_filtered[[
        "project_name", "phase", "planned_start", "actual_start", "planned_end", "actual_end", "start_delay", "end_delay"
    ]].copy()

    phase_delay_df["start_delay_str"] = phase_delay_df["start_delay"].apply(lambda x: f"{x:.0f}日" if pd.notna(x) else "—")
    phase_delay_df["end_delay_str"] = phase_delay_df["end_delay"].apply(lambda x: f"{x:.0f}日" if pd.notna(x) else "進行中")

    display_phase_df = phase_delay_df[[
        "project_name", "phase", "planned_start", "actual_start", "planned_end", "actual_end", "start_delay_str", "end_delay_str"
    ]].copy()

    display_phase_df.columns = ["プロジェクト", "工程", "計画開始", "実績開始", "計画終了", "実績終了", "開始遅延", "終了遅延"]

    # 日付をフォーマット
    for col in ["計画開始", "実績開始", "計画終了", "実績終了"]:
        display_phase_df[col] = display_phase_df[col].dt.strftime("%Y-%m-%d")

    st.dataframe(display_phase_df, use_container_width=True)
else:
    st.warning("⚠️ 表示するデータがありません")

# ============================================================================
# データサマリー
# ============================================================================
st.markdown("---")
st.header("📋 詳細分析")

col1, col2 = st.columns(2)

with col1:
    st.subheader("進捗状況")
    progress_summary = df_filtered.groupby("project_name")["progress_pct"].mean().sort_values(ascending=False)
    fig_progress = px.bar(
        x=progress_summary.index,
        y=progress_summary.values,
        labels={"x": "プロジェクト", "y": "進捗率（%）"},
        title="プロジェクト別平均進捗率",
        text=progress_summary.values.round(0).astype(str) + "%"
    )
    fig_progress.update_traces(marker_color="steelblue", textposition="outside")
    fig_progress.update_layout(showlegend=False)
    st.plotly_chart(fig_progress, use_container_width=True)

with col2:
    st.subheader("原価内訳")
    if len(project_df_filtered) > 0:
        total_cost_data = {
            "区分": ["計画総額", "実績総額"],
            "金額": [result["total_planned"], result["total_actual"]]
        }
        fig_cost = px.pie(
            values=total_cost_data["金額"],
            names=total_cost_data["区分"],
            title="計画 vs 実績の構成比"
        )
        st.plotly_chart(fig_cost, use_container_width=True)
