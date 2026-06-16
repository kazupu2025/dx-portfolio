"""Streamlit ダッシュボード"""
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_production_cost_202401.csv"
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"

st.set_page_config(page_title="製造 原価差異分析", layout="wide")
st.title("[MFG] 製造 原価差異分析ダッシュボード")

if not CSV_PATH.exists():
    st.error("データが見つかりません。パイプラインを実行してください。")
    st.stop()

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# フィルター
lines = sorted(df["line_id"].unique())
selected_lines = st.multiselect("製造ラインを選択", lines, default=lines)
df_filtered = df[df["line_id"].isin(selected_lines)] if selected_lines else df

# メトリクス
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("総計画コスト", f"¥{df_filtered['planned_total_cost'].sum():,.0f}")
with col2:
    st.metric("総実績コスト", f"¥{df_filtered['actual_total_cost'].sum():,.0f}")
with col3:
    var_amt = df_filtered["total_variance"].sum()
    st.metric("差異額", f"¥{var_amt:,.0f}", delta=f"{var_amt:,.0f}")
with col4:
    planned = df_filtered["planned_total_cost"].sum()
    var_pct = (var_amt / planned * 100) if planned != 0 else 0
    st.metric("差異率", f"{var_pct:.2f}%")

st.divider()

# 差異フラグ別件数
st.subheader("差異フラグ別件数")
flag_counts = df_filtered["variance_flag"].value_counts().reset_index()
flag_counts.columns = ["フラグ","件数"]
st.dataframe(flag_counts, use_container_width=True)

st.divider()

# レポート表示
if REPORT_PATH.exists():
    st.subheader("分析レポート")
    st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
