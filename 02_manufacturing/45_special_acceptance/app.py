import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from analyze import analyze, REQUIRED_COLUMNS
from pathlib import Path

st.set_page_config(page_title="特採件数・理由別集計・月次推移", layout="wide")
st.title("特採件数・理由別集計・月次推移")

with st.sidebar:
    st.header("データ入力")
    uploaded_file = st.file_uploader("CSVをアップロード", type="csv")

    if st.button("サンプルデータを読み込む"):
        sample_path = Path(__file__).parent / "sample_special_acceptance.csv"
        if sample_path.exists():
            st.session_state.df = pd.read_csv(sample_path)
            st.success("サンプルデータを読み込みました")

    if uploaded_file:
        st.session_state.df = pd.read_csv(uploaded_file)
        st.success("ファイルをアップロードしました")

if "df" not in st.session_state:
    st.info("サイドバーからCSVをアップロードするか、サンプルデータを読み込んでください")
    st.stop()

df = st.session_state.df

# 必須列のチェック
missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing_cols:
    st.error(f"必須列が不足しています: {', '.join(missing_cols)}")
    st.stop()

# 分析実行
result = analyze(df)

# KPIカード
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("月平均件数", f"{result['avg_monthly']:.1f}")

with col2:
    st.metric("最多理由", result["top_reason"])

with col3:
    st.metric("総数", result["total_count"])

# ステータス表示
st.divider()
if result["verdict"] == "good":
    st.success(f"✓ 良好：月平均 {result['avg_monthly']:.1f}件 (≤3件の基準範囲内)")
elif result["verdict"] == "warning":
    st.warning(f"⚠ 注意：月平均 {result['avg_monthly']:.1f}件 (3-10件の警告範囲)")
else:
    st.error(f"⚠ 注意：月平均 {result['avg_monthly']:.1f}件 (>10件の警報範囲)")

# グラフセクション
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("月次棒グラフ（件数）")
    fig, ax = plt.subplots(figsize=(10, 5))
    monthly_data = result["monthly_df"].sort_values("month")
    ax.bar(monthly_data["month"], monthly_data["count"], color="steelblue")
    ax.set_xlabel("月")
    ax.set_ylabel("特採件数")
    ax.grid(axis="y", alpha=0.3)
    st.pyplot(fig)

with col2:
    st.subheader("理由別棒グラフ")
    fig, ax = plt.subplots(figsize=(10, 5))
    reason_data = result["reason_df"]
    colors = ["#d62728" if x == result["top_reason"] else "steelblue" for x in reason_data["reason_category"]]
    ax.bar(reason_data["reason_category"], reason_data["count"], color=colors)
    ax.set_xlabel("理由")
    ax.set_ylabel("件数")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.3)
    st.pyplot(fig)

# データテーブル
st.divider()
st.subheader("詳細データ")

tab1, tab2, tab3 = st.tabs(["元データ", "月次集計", "理由別集計"])

with tab1:
    st.dataframe(df, use_container_width=True)

with tab2:
    st.dataframe(result["monthly_df"], use_container_width=True)

with tab3:
    st.dataframe(result["reason_df"], use_container_width=True)
