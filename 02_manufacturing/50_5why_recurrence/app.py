import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# ── analyze.py インライン（Streamlit Cloud 互換）──
import pandas as pd

REQUIRED_COLUMNS = ["date", "issue_id", "root_cause_category", "recurrence_flag"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    total = len(df)
    recurrence_count = int(df["recurrence_flag"].sum())
    recurrence_rate = recurrence_count / total * 100 if total > 0 else 0

    category_df = df.groupby("root_cause_category").agg(
        count=("issue_id", "count"),
        recurrence=("recurrence_flag", "sum"),
    ).reset_index()
    category_df["recurrence_rate"] = category_df["recurrence"] / category_df["count"] * 100
    category_df = category_df.sort_values("count", ascending=False)

    monthly_df = df.groupby("month").agg(
        count=("issue_id", "count"),
        recurrence=("recurrence_flag", "sum"),
    ).reset_index()
    monthly_df["recurrence_rate"] = monthly_df["recurrence"] / monthly_df["count"] * 100

    top_category = category_df.iloc[0]["root_cause_category"]

    if recurrence_rate <= 5:
        verdict = "good"
    elif recurrence_rate <= 15:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "category_df": category_df,
        "monthly_df": monthly_df,
        "total": int(total),
        "recurrence_count": recurrence_count,
        "recurrence_rate": float(recurrence_rate),
        "top_category": top_category,
        "verdict": verdict,
    }

# ────────────────────────────────────────────────
import os

st.title("5Why分析 原因カテゴリ別集計・再発率トレンド")
st.markdown("---")

# ============================================
# サイドバー: データ入力
# ============================================
st.sidebar.title("データ入力")

uploaded_file = st.sidebar.file_uploader(
    "CSVファイルをアップロード",
    type="csv",
    help="必須列: date, issue_id, root_cause_category, recurrence_flag"
)

if st.sidebar.button("📥 サンプルデータを使用", use_container_width=True):
    sample_path = os.path.join(os.path.dirname(__file__), "sample_5why_recurrence.csv")
    uploaded_file = sample_path

# ============================================
# データ読み込み
# ============================================
df = None
try:
    if uploaded_file is not None:
        if isinstance(uploaded_file, str):  # ファイルパス
            df = pd.read_csv(uploaded_file)
        else:  # アップロードされたファイル
            df = pd.read_csv(uploaded_file)

        # バリデーション
        missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            st.error(f"❌ 必須列がありません: {', '.join(missing_cols)}")
            df = None
except Exception as e:
    st.error(f"❌ ファイル読み込みエラー: {e}")
    df = None

if df is None:
    st.warning("💡 サイドバーからCSVをアップロードするか、サンプルデータボタンをクリックしてください")
    st.stop()

# ============================================
# 分析実行
# ============================================
try:
    result = analyze(df)
except Exception as e:
    st.error(f"❌ 分析エラー: {e}")
    st.stop()

# ============================================
# KPIカード表示
# ============================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "再発率",
        f"{result['recurrence_rate']:.1f}%",
        delta=f"{result['recurrence_count']} 件",
    )

with col2:
    st.metric(
        "再発件数",
        result['recurrence_count'],
        delta=f"/ {result['total']} 件",
    )

with col3:
    st.metric(
        "最多原因カテゴリ",
        result['top_category'],
    )

with col4:
    verdict_emoji = {"good": "✅", "warning": "⚠️", "alert": "🚨"}
    verdict_text = {"good": "良好", "warning": "注意", "alert": "警告"}
    st.metric(
        "判定",
        verdict_text[result['verdict']],
        delta=verdict_emoji[result['verdict']],
    )

st.markdown("---")

# ============================================
# グラフ表示
# ============================================
col_left, col_right = st.columns(2)

# 月次再発率 折れ線グラフ
with col_left:
    st.subheader("月次再発率の推移")
    monthly_df = result['monthly_df']

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Scatter(
        x=monthly_df['month'],
        y=monthly_df['recurrence_rate'],
        mode='lines+markers',
        name='再発率',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=10),
    ))
    fig_monthly.update_layout(
        xaxis_title="月",
        yaxis_title="再発率 (%)",
        hovermode='x unified',
        height=400,
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

# 原因カテゴリ別 棒グラフ
with col_right:
    st.subheader("原因カテゴリ別 集計")
    category_df = result['category_df']

    fig_category = go.Figure()
    fig_category.add_trace(go.Bar(
        x=category_df['root_cause_category'],
        y=category_df['count'],
        name='件数',
        marker=dict(color='#4ECDC4'),
    ))
    fig_category_secondary = go.Figure()
    fig_category_secondary.add_trace(go.Scatter(
        x=category_df['root_cause_category'],
        y=category_df['recurrence_rate'],
        mode='lines+markers',
        name='再発率',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=10),
        yaxis='y2',
    ))

    fig_combined = go.Figure(data=fig_category.data + fig_category_secondary.data)
    fig_combined.update_layout(
        xaxis_title="原因カテゴリ",
        yaxis_title="件数",
        yaxis2=dict(
            title="再発率 (%)",
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=400,
    )
    st.plotly_chart(fig_combined, use_container_width=True)

st.markdown("---")

# ============================================
# 詳細テーブル表示
# ============================================
st.subheader("原因カテゴリ別 詳細")
category_df = result['category_df'].copy()
category_df.columns = ["原因カテゴリ", "件数", "再発件数", "再発率(%)"]
category_df["再発率(%)"] = category_df["再発率(%)"].round(1)
st.dataframe(category_df, use_container_width=True, hide_index=True)

st.subheader("月別 詳細")
monthly_df = result['monthly_df'].copy()
monthly_df.columns = ["月", "件数", "再発件数", "再発率(%)"]
monthly_df["再発率(%)"] = monthly_df["再発率(%)"].round(1)
st.dataframe(monthly_df, use_container_width=True, hide_index=True)
