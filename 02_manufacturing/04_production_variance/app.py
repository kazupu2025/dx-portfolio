# -*- coding: utf-8 -*-
"""
B-75: 製造 生産計画差異ダッシュボード
Streamlit ダッシュボード
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_CSV = OUTPUT_DIR / "cleaned_production_202401.csv"
LINE_SUMMARY_CSV = OUTPUT_DIR / "line_summary_202401.csv"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_mfg_production_variance_data() -> pd.DataFrame:
    if not CLEANED_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["planned_qty", "actual_qty", "achievement_rate", "defect_rate", "variance_qty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_mfg_production_line_summary() -> pd.DataFrame:
    if not LINE_SUMMARY_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(LINE_SUMMARY_CSV, encoding="utf-8-sig")


st.title("🏭 B-75 製造 生産計画差異ダッシュボード")
st.caption("B-75 | 製造 × 生産管理 | 生産計画 vs 実績 差異分析 | 2024年1月")

df_all = load_mfg_production_variance_data()

if df_all.empty:
    st.error(f"データが見つかりません: {CLEANED_CSV}")
    st.info("先にパイプラインを実行してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    all_lines = sorted(df_all["line_name"].dropna().unique().tolist()) if "line_name" in df_all.columns else []
    selected_lines = st.multiselect("製造ラインを選択", all_lines, default=all_lines, key="b75_line_filter")

if not selected_lines:
    st.warning("少なくとも1つのラインを選択してください。")
    st.stop()

df = df_all[df_all["line_name"].isin(selected_lines)].copy()

# KPI
col1, col2, col3, col4 = st.columns(4)
col1.metric("総計画数量", f"{int(df['planned_qty'].sum()):,}" if "planned_qty" in df.columns else "N/A")
col2.metric("総実績数量", f"{int(df['actual_qty'].sum()):,}" if "actual_qty" in df.columns else "N/A")
avg_ach = df["achievement_rate"].mean() if "achievement_rate" in df.columns else None
col3.metric("平均達成率", f"{avg_ach*100:.1f}%" if avg_ach is not None and pd.notna(avg_ach) else "N/A")
avg_def = df["defect_rate"].mean() if "defect_rate" in df.columns else None
col4.metric("平均不良率", f"{avg_def*100:.2f}%" if avg_def is not None and pd.notna(avg_def) else "N/A")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 達成率分析", "⚠️ 不良率分析", "📋 サマリーテーブル"])

with tab1:
    st.subheader("ライン別 平均達成率")
    if "line_name" in df.columns and "achievement_rate" in df.columns:
        grp_ach = df.groupby("line_name")["achievement_rate"].mean().mul(100).sort_values(ascending=True)
        st.bar_chart(grp_ach)

        st.subheader("日別 達成率トレンド")
        if "date" in df.columns:
            daily_ach = df.groupby("date")["achievement_rate"].mean().mul(100)
            st.line_chart(daily_ach)

with tab2:
    st.subheader("カテゴリ別 平均不良率")
    if "category" in df.columns and "defect_rate" in df.columns:
        grp_def = df.groupby("category")["defect_rate"].mean().mul(100).sort_values(ascending=False)
        st.bar_chart(grp_def)

    st.subheader("ライン別 平均不良率")
    if "line_name" in df.columns and "defect_rate" in df.columns:
        line_def = df.groupby("line_name")["defect_rate"].mean().mul(100).sort_values(ascending=False)
        st.bar_chart(line_def)

with tab3:
    st.subheader("ライン別サマリーテーブル")
    line_summary = load_mfg_production_line_summary()
    if not line_summary.empty and "line_name" in line_summary.columns:
        filtered_summary = line_summary[line_summary["line_name"].isin(selected_lines)]
        st.dataframe(filtered_summary, use_container_width=True, hide_index=True)
    else:
        _agg = {}
        if "planned_qty" in df.columns:
            _agg["計画数量合計"] = ("planned_qty", "sum")
        if "actual_qty" in df.columns:
            _agg["実績数量合計"] = ("actual_qty", "sum")
        if "variance_qty" in df.columns:
            _agg["差異数量"] = ("variance_qty", "sum")
        if "achievement_rate" in df.columns:
            _agg["平均達成率"] = ("achievement_rate", "mean")
        if "defect_rate" in df.columns:
            _agg["平均不良率"] = ("defect_rate", "mean")
        if _agg and "line_name" in df.columns:
            grp_table = df.groupby("line_name", as_index=False).agg(**_agg)
            grp_table = grp_table.rename(columns={"line_name": "ライン名"})
            if "平均達成率" in grp_table.columns:
                grp_table["平均達成率"] = (grp_table["平均達成率"] * 100).round(1).astype(str) + "%"
            if "平均不良率" in grp_table.columns:
                grp_table["平均不良率"] = (grp_table["平均不良率"] * 100).round(2).astype(str) + "%"
            st.dataframe(grp_table, use_container_width=True, hide_index=True)

    st.divider()
    if REPORT_MD.exists():
        with st.expander("📄 分析レポートを表示", expanded=False):
            st.markdown(REPORT_MD.read_text(encoding="utf-8"))
    else:
        st.info("analyze.py を実行するとレポートが表示されます。")
