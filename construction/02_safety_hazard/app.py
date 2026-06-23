import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from analyze import analyze

# ページ設定
st.set_page_config(page_title="安全管理・ヒヤリハット集計", layout="wide")

# タイトル
st.title("🛡️ 安全管理・ヒヤリハット集計レポート")
st.markdown("建設プロジェクトのヒヤリハット・安全事案を集計・分析し、安全管理の進捗を可視化します")

# ============================================================================
# サイドバー
# ============================================================================
st.sidebar.header("📥 データ入力")

# サンプルデータ読み込み
SAMPLE_FILE = Path(__file__).parent / "sample_safety.csv"

uploaded_file = st.sidebar.file_uploader(
    "CSVファイルをアップロード",
    type="csv",
    help="列: date, project_id, location, category, severity, description, corrective_action, reporter, resolved"
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
all_projects = sorted(result["project_stats"]["project_id"].unique())
selected_projects = st.sidebar.multiselect(
    "プロジェクトを選択（複数選択可）",
    options=all_projects,
    default=all_projects
)

# 選択されたプロジェクトでデータをフィルタ
df_filtered = result["df"][result["df"]["project_id"].isin(selected_projects)]
project_stats_filtered = result["project_stats"][result["project_stats"]["project_id"].isin(selected_projects)]

# ============================================================================
# KPIカード
# ============================================================================
st.markdown("---")
st.header("📊 KPI ダッシュボード")

col1, col2, col3, col4 = st.columns(4)

# 総インシデント件数
with col1:
    st.metric(
        "総件数",
        f"{result['total_incidents']}件",
        delta=None,
        delta_color="off"
    )

# 重大事案件数
with col2:
    critical_color = "🔴" if result["critical_count"] > 2 else "🟡" if result["critical_count"] > 0 else "🟢"
    st.metric(
        "重大事案",
        f"{result['critical_count']}件",
        delta=f"{critical_color}",
        delta_color="off"
    )

# 解決率
with col3:
    resolution_rate = result["resolution_rate"]
    color_emoji = "🟢" if resolution_rate >= 90 else "🟡" if resolution_rate >= 70 else "🔴"
    st.metric(
        "解決率",
        f"{resolution_rate:.1f}%",
        delta=f"{color_emoji}",
        delta_color="off"
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

st.markdown(f"**未解決件数**: {result['unresolved_count']}件")

# ============================================================================
# カテゴリ別件数（棒グラフ、重篤度色分け）
# ============================================================================
st.markdown("---")
st.header("📈 カテゴリ別インシデント件数")

if len(df_filtered) > 0:
    category_severity = df_filtered.groupby(["category", "severity"]).size().reset_index(name="件数")

    # 色定義: 重大（赤）, 軽微（黄）, ヒヤリハット（青）
    color_map = {
        "重大": "#e74c3c",
        "軽微": "#f39c12",
        "ヒヤリハット": "#3498db",
    }

    fig_category = px.bar(
        category_severity,
        x="category",
        y="件数",
        color="severity",
        title="カテゴリ別インシデント件数（重篤度別）",
        labels={"category": "カテゴリ", "件数": "件数", "severity": "重篤度"},
        color_discrete_map=color_map,
        text="件数"
    )
    fig_category.update_traces(textposition="outside")
    fig_category.update_layout(showlegend=True, hovermode="x unified")
    st.plotly_chart(fig_category, use_container_width=True)

    # カテゴリ別集計テーブル
    st.subheader("カテゴリ別集計")
    display_category = result["category_stats"].copy()
    st.dataframe(display_category, use_container_width=True)
else:
    st.warning("⚠️ 選択されたプロジェクトがありません")

# ============================================================================
# 月別発生トレンド（折れ線グラフ）
# ============================================================================
st.markdown("---")
st.header("📅 月別発生トレンド")

if len(df_filtered) > 0:
    # 月別トレンドを再計算（フィルタ後のデータ）
    df_filtered_copy = df_filtered.copy()
    df_filtered_copy["year_month"] = df_filtered_copy["date"].dt.strftime("%Y-%m")
    monthly_filtered = df_filtered_copy.groupby("year_month").agg(
        発生件数=("year_month", "count"),
        重大=("severity", lambda x: (x == "重大").sum()),
        軽微=("severity", lambda x: (x == "軽微").sum()),
        ヒヤリハット=("severity", lambda x: (x == "ヒヤリハット").sum()),
    ).reset_index()

    fig_monthly = go.Figure()

    fig_monthly.add_trace(go.Scatter(
        x=monthly_filtered["year_month"],
        y=monthly_filtered["発生件数"],
        mode="lines+markers",
        name="発生件数",
        line=dict(color="#2ecc71", width=3),
        marker=dict(size=8)
    ))

    fig_monthly.update_layout(
        title="月別インシデント発生件数トレンド",
        xaxis_title="月",
        yaxis_title="発生件数",
        hovermode="x unified",
        height=400
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

    # 月別詳細テーブル
    st.subheader("月別詳細")
    st.dataframe(monthly_filtered, use_container_width=True)
else:
    st.warning("⚠️ 表示するデータがありません")

# ============================================================================
# 未解決案件一覧（重大順）
# ============================================================================
st.markdown("---")
st.header("⚠️ 未解決案件一覧")

unresolved = df_filtered[df_filtered["resolved"] == False].copy()

if len(unresolved) > 0:
    # 重大度順でソート
    severity_order = {"重大": 0, "軽微": 1, "ヒヤリハット": 2}
    unresolved["severity_order"] = unresolved["severity"].map(severity_order)
    unresolved = unresolved.sort_values("severity_order").reset_index(drop=True)

    display_unresolved = unresolved[[
        "date", "project_id", "category", "severity", "description", "corrective_action", "reporter"
    ]].copy()

    display_unresolved.columns = ["日付", "プロジェクト", "カテゴリ", "重篤度", "事案説明", "是正措置", "報告者"]
    display_unresolved["日付"] = display_unresolved["日付"].dt.strftime("%Y-%m-%d")

    # 重篤度で色分け（展示用）
    st.dataframe(display_unresolved, use_container_width=True)

    st.metric("未解決件数", f"{len(unresolved)}件")
else:
    st.success("✅ すべてのインシデントが解決済みです")

# ============================================================================
# プロジェクト別集計
# ============================================================================
st.markdown("---")
st.header("🏗️ プロジェクト別集計")

if len(project_stats_filtered) > 0:
    # 重大件数順でソート
    project_stats_sorted = project_stats_filtered.sort_values("重大", ascending=False)

    display_project = project_stats_sorted[[
        "project_id", "件数", "重大", "未解決", "解決率"
    ]].copy()

    display_project.columns = ["プロジェクト", "総件数", "重大件数", "未解決件数", "解決率(%)"]
    display_project["解決率(%)"] = display_project["解決率(%)"].apply(lambda x: f"{x:.1f}%")

    st.dataframe(display_project, use_container_width=True)

    # プロジェクト別の重大件数と解決率の関係（バブルチャート）
    fig_project = px.scatter(
        project_stats_sorted,
        x="解決率",
        y="重大",
        size="件数",
        hover_name="project_id",
        title="プロジェクト別: 重大件数 vs 解決率",
        labels={"解決率": "解決率(%)", "重大": "重大件数", "project_id": "プロジェクト"},
    )
    fig_project.add_hline(y=2, line_dash="dash", line_color="orange", annotation_text="警戒レベル（重大=2）")
    fig_project.add_vline(x=70, line_dash="dash", line_color="blue", annotation_text="警戒レベル（解決率=70%）")
    st.plotly_chart(fig_project, use_container_width=True)
else:
    st.warning("⚠️ 選択されたプロジェクトがありません")

# ============================================================================
# データサマリー
# ============================================================================
st.markdown("---")
st.header("📋 詳細分析")

col1, col2 = st.columns(2)

with col1:
    st.subheader("重篤度別内訳")
    severity_stats = result["severity_stats"].copy()
    fig_severity = px.pie(
        severity_stats,
        values="件数",
        names="severity",
        title="重篤度別件数の構成比",
        color_discrete_map={
            "重大": "#e74c3c",
            "軽微": "#f39c12",
            "ヒヤリハット": "#3498db",
        }
    )
    st.plotly_chart(fig_severity, use_container_width=True)

with col2:
    st.subheader("解決状況")
    resolved_count = result["total_incidents"] - result["unresolved_count"]
    resolved_data = pd.DataFrame({
        "状態": ["解決済", "未解決"],
        "件数": [resolved_count, result["unresolved_count"]]
    })
    fig_resolved = px.pie(
        resolved_data,
        values="件数",
        names="状態",
        title="解決状況の構成比",
        color_discrete_map={
            "解決済": "#2ecc71",
            "未解決": "#e74c3c",
        }
    )
    st.plotly_chart(fig_resolved, use_container_width=True)
