"""
B-27 医療 来院スループット・待ち時間管理ダッシュボード（Streamlit）
"""
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_reception_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CHARTS_DIR = OUTPUT_DIR / "charts"


@st.cache_data
def load_reception_throughput_data() -> pd.DataFrame:
    """B-27専用ローダー（キャッシュキー衝突防止）"""
    if not CSV_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


st.title("🏥 B-27 医療 来院スループット・待ち時間管理ダッシュボード")
st.caption("B-27 | 2024年1月 | 診療科別待ち時間・時間帯別来院数・長待ちアラート")

df_all = load_reception_throughput_data()

if df_all.empty:
    st.error("データファイルが見つかりません。パイプラインを実行してください。")
    st.stop()

# サイドバー: 診療科フィルター
with st.sidebar:
    st.header("🔍 フィルター")
    departments = sorted(df_all["department"].unique().tolist())
    selected_depts = st.multiselect("診療科を選択", departments, default=departments)

df = df_all[df_all["department"].isin(selected_depts)].copy() if selected_depts else df_all.copy()

# KPI 4つ
total_visits = len(df)
avg_wait = df["wait_minutes"].mean() if total_visits > 0 else 0
long_wait_count = int((df["wait_level"] == "長待ち").sum())
long_wait_rate = long_wait_count / total_visits * 100 if total_visits > 0 else 0
avg_treat = df["treat_minutes"].mean() if total_visits > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("総来院数", f"{total_visits:,} 件")
col2.metric("平均待ち時間", f"{avg_wait:.1f} 分")
col3.metric("長待ち率", f"{long_wait_rate:.1f}%",
            delta=f"{long_wait_count} 件" if long_wait_count > 0 else None,
            delta_color="inverse")
col4.metric("平均診察時間", f"{avg_treat:.1f} 分")

st.divider()

# 3タブ
tab1, tab2, tab3 = st.tabs(["📊 診療科別待ち時間", "🕐 時間帯別来院数", "⏱️ 待ちレベル分布"])

with tab1:
    st.subheader("診療科別 平均待ち時間・長待ち率")
    dept_summary = df.groupby("department").agg(
        来院件数=("reception_no", "count"),
        平均待ち時間=("wait_minutes", "mean"),
        最大待ち時間=("wait_minutes", "max"),
        平均診察時間=("treat_minutes", "mean"),
    ).round(1).reset_index()
    long_wait_c = (
        df[df["wait_level"] == "長待ち"]
        .groupby("department").size()
        .reset_index(name="長待ち件数")
    )
    dept_summary = dept_summary.merge(long_wait_c, on="department", how="left")
    dept_summary["長待ち件数"] = dept_summary["長待ち件数"].fillna(0).astype(int)
    dept_summary["長待ち率(%)"] = (
        dept_summary["長待ち件数"] / dept_summary["来院件数"] * 100
    ).round(1)
    st.dataframe(
        dept_summary.sort_values("平均待ち時間", ascending=False),
        use_container_width=True
    )
    chart_path = CHARTS_DIR / "bar_dept_wait.png"
    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)

with tab2:
    st.subheader("時間帯別 来院件数")
    ts_counts = df.groupby("time_slot").agg(
        来院件数=("reception_no", "count"),
        平均待ち時間=("wait_minutes", "mean"),
    ).round(1).sort_index().reset_index()
    st.dataframe(ts_counts, use_container_width=True)
    chart_path = CHARTS_DIR / "heatmap_timeslot_dept.png"
    if chart_path.exists():
        st.subheader("時間帯 × 診療科 来院件数ヒートマップ")
        st.image(str(chart_path), use_container_width=True)

with tab3:
    st.subheader("待ち時間レベル別 件数")
    wait_level_counts = df["wait_level"].value_counts().reset_index()
    wait_level_counts.columns = ["待ちレベル", "件数"]
    st.dataframe(wait_level_counts, use_container_width=True)
    chart_path = CHARTS_DIR / "bar_wait_level.png"
    if chart_path.exists():
        st.image(str(chart_path), use_container_width=True)

st.divider()

# 長待ちアラートテーブル（60分超）
st.subheader("🚨 長待ちアラート（待ち時間 60分超）")
long_wait_df = df[df["wait_minutes"] > 60].sort_values("wait_minutes", ascending=False)
if len(long_wait_df) > 0:
    display_cols = [c for c in [
        "visit_date", "reception_no", "department", "arrival_time",
        "wait_minutes", "treat_minutes", "time_slot"
    ] if c in long_wait_df.columns]
    st.dataframe(
        long_wait_df[display_cols].reset_index(drop=True),
        use_container_width=True,
    )
    st.caption(f"長待ち（60分超）: {len(long_wait_df)} 件")
else:
    st.info("長待ち（60分超）の来院はありませんでした。")

st.divider()

# 分析レポート
if REPORT_PATH.exists():
    with st.expander("📄 分析レポートを表示", expanded=False):
        st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
