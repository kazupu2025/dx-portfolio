import streamlit as st
import pandas as pd
from pathlib import Path
from analyze import analyze, REQUIRED_COLUMNS

st.set_page_config(page_title="C-100 4M変更台帳", layout="wide")
st.title("C-100 4M変更台帳 集計・変更種別推移レポート")

# サイドバー
st.sidebar.header("データアップロード")

# サンプルデータボタン
if st.sidebar.button("サンプルデータを読み込む"):
    sample_path = Path(__file__).parent / "sample_4m_change.csv"
    df = pd.read_csv(sample_path)
    st.session_state.df = df
    st.sidebar.success("サンプルデータを読み込みました")

# CSVアップロード
uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.session_state.df = df
    st.sidebar.success("ファイルをアップロードしました")

# データがない場合
if "df" not in st.session_state:
    st.info("サンプルデータを読み込むか、CSVファイルをアップロードしてください")
    st.stop()

df = st.session_state.df

# データの検証
missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing_cols:
    st.error(f"必要な列が不足しています: {', '.join(missing_cols)}")
    st.stop()

# 分析実行
result = analyze(df)

# KPIカード
st.subheader("重要指標（KPI）")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("月平均件数", f"{result['avg_monthly']:.1f}")

with col2:
    st.metric("高リスク件数", result["high_risk_count"])

with col3:
    st.metric("総変更件数", result["total_count"])

with col4:
    verdict_color = {"good": "green", "warning": "orange", "alert": "red"}
    verdict_text = {"good": "良好", "warning": "要注意", "alert": "警告"}
    st.metric("判定", verdict_text.get(result["verdict"], "不明"))

# グラフ表示
st.subheader("変更種別推移（4M別月次変更件数）")
monthly_pivot = result["monthly_df"].pivot(index="month", columns="change_type", values="count").fillna(0)
st.bar_chart(monthly_pivot)

col1, col2 = st.columns(2)

with col1:
    st.subheader("4M別変更件数")
    st.bar_chart(result["type_df"].set_index("change_type")["count"])

with col2:
    st.subheader("工程別変更件数")
    st.bar_chart(result["process_df"].set_index("process")["count"])

# 詳細データ表示
st.subheader("詳細データ")
if st.checkbox("元データを表示"):
    st.dataframe(df)

if st.checkbox("月別・変更種別集計を表示"):
    st.dataframe(result["monthly_df"])
