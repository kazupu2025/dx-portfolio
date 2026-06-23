#!/usr/bin/env python3
"""
C-112 Attendance & Grade Report - Streamlit Dashboard
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from analyze import analyze

# Set Japanese font
plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Hiragino Sans']
plt.rcParams['axes.unicode_minus'] = False

# Streamlit page config
st.set_page_config(
    page_title="出席率・成績推移レポート",
    page_icon="📊",
    layout="wide",
)

st.title("📊 出席率・成績推移レポート")
st.markdown("各クラス・科目の出席率と成績の推移を追跡分析します。")

# ────────────────────────────────────────────────────────
# Sidebar: Data Input
# ────────────────────────────────────────────────────────
st.sidebar.header("📥 データ入力")

# Sample data generator
@st.cache_resource
def get_sample_data():
    """Load or generate sample data"""
    sample_path = Path(__file__).parent / "sample_attendance_grade.csv"
    if sample_path.exists():
        return pd.read_csv(sample_path)
    else:
        # Generate if not found
        st.warning("Sample data not found. Generating...")
        from _gen_sample_data import generate_sample_data
        return generate_sample_data()

# Data input options
data_source = st.sidebar.radio("データソース:", ["📊 サンプルデータ", "📁 CSVアップロード"])

if data_source == "📊 サンプルデータ":
    df = get_sample_data()
    st.sidebar.success("✓ サンプルデータを読み込みました")
else:
    uploaded_file = st.sidebar.file_uploader("CSVファイルを選択:", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("✓ ファイルをアップロードしました")
    else:
        df = None

if df is None:
    st.warning("データを読み込んでください")
    st.stop()

# Display data shape
st.sidebar.info(f"📈 レコード数: {len(df)}")

# ────────────────────────────────────────────────────────
# Sidebar: Filters
# ────────────────────────────────────────────────────────
st.sidebar.header("🔍 フィルタ")

all_classes = sorted(df["class_name"].unique())
selected_classes = st.sidebar.multiselect(
    "クラスを選択:",
    all_classes,
    default=all_classes,
)

all_subjects = sorted(df["subject"].unique())
selected_subjects = st.sidebar.multiselect(
    "科目を選択:",
    all_subjects,
    default=all_subjects,
)

# Filter data
df_filtered = df[
    (df["class_name"].isin(selected_classes)) &
    (df["subject"].isin(selected_subjects))
].copy()

st.sidebar.info(f"表示レコード数: {len(df_filtered)}")

# Run analysis
if len(df_filtered) > 0:
    result = analyze(df_filtered)
else:
    st.warning("フィルタ条件に合致するデータがありません")
    st.stop()

# ────────────────────────────────────────────────────────
# KPI Cards
# ────────────────────────────────────────────────────────
st.header("📊 KPI指標")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "平均出席率",
        f"{result['overall_attendance']:.1f}%",
        delta=None,
    )

with col2:
    st.metric(
        "平均成績",
        f"{result['overall_score']:.1f}点",
        delta=None,
    )

with col3:
    st.metric(
        "成績不振率",
        f"{result['overall_failing_rate']:.1f}%",
        delta=None,
    )

with col4:
    verdict_color = {
        "good": "🟢 良好",
        "warning": "🟡 要注意",
        "alert": "🔴 警報",
    }
    verdict_text = verdict_color.get(result["verdict"], "不明")
    st.metric("総合判定", verdict_text)

# ────────────────────────────────────────────────────────
# Monthly Trend (Dual Axis)
# ────────────────────────────────────────────────────────
st.header("📈 月次トレンド")

if len(result["trend_df"]) > 0:
    fig, ax1 = plt.subplots(figsize=(12, 5))

    trend = result["trend_df"].sort_values("month")

    # Left axis: Attendance
    ax1.plot(trend["month"], trend["avg_attendance"], marker="o", color="blue", linewidth=2, label="出席率")
    ax1.set_xlabel("月", fontsize=11)
    ax1.set_ylabel("出席率 (%)", color="blue", fontsize=11)
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.grid(alpha=0.3)

    # Right axis: Score
    ax2 = ax1.twinx()
    ax2.plot(trend["month"], trend["avg_score"], marker="s", color="red", linewidth=2, label="平均点")
    ax2.set_ylabel("平均点", color="red", fontsize=11)
    ax2.tick_params(axis="y", labelcolor="red")

    # Rotate x-axis labels
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    st.pyplot(fig)
    plt.close()

# ────────────────────────────────────────────────────────
# Class Ranking (Bar Chart)
# ────────────────────────────────────────────────────────
st.header("🏆 クラス別成績ランキング")

if len(result["class_df"]) > 0:
    fig, ax = plt.subplots(figsize=(10, 5))
    class_rank = result["class_df"].sort_values("avg_score", ascending=True)

    ax.barh(class_rank["class_name"], class_rank["avg_score"], color="steelblue")
    ax.set_xlabel("平均点", fontsize=11)
    ax.set_ylabel("クラス", fontsize=11)
    ax.set_title("クラス別平均成績", fontsize=12, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    for i, v in enumerate(class_rank["avg_score"]):
        ax.text(v + 1, i, f"{v:.1f}", va="center", fontsize=10)

    st.pyplot(fig)
    plt.close()

# ────────────────────────────────────────────────────────
# Subject Scatter: Attendance vs Score
# ────────────────────────────────────────────────────────
st.header("📊 科目別分析（出席率 × 成績）")

if len(result["subject_df"]) > 0:
    fig, ax = plt.subplots(figsize=(10, 6))
    subject_data = result["subject_df"]

    ax.scatter(subject_data["avg_attendance"], subject_data["avg_score"],
               s=200, alpha=0.6, color="purple")

    for idx, row in subject_data.iterrows():
        ax.annotate(row["subject"],
                    (row["avg_attendance"], row["avg_score"]),
                    xytext=(5, 5), textcoords="offset points", fontsize=10)

    ax.set_xlabel("平均出席率 (%)", fontsize=11)
    ax.set_ylabel("平均成績 (点)", fontsize=11)
    ax.set_title("科目別：出席率と成績の関係", fontsize=12, fontweight="bold")
    ax.grid(alpha=0.3)

    st.pyplot(fig)
    plt.close()

    # Correlation info
    corr = result["correlation"]
    st.info(f"📌 出席率と成績の相関係数: {corr:.3f}")

# ────────────────────────────────────────────────────────
# Alert Classes / Subjects
# ────────────────────────────────────────────────────────
st.header("⚠️ 要注意クラス・科目")

alert_classes = result.get("alert_classes", [])
if alert_classes:
    st.warning(f"🚨 対応が必要なクラス: {', '.join(alert_classes)}")
else:
    st.success("✓ 要注意クラスはありません")

# ────────────────────────────────────────────────────────
# Detailed Tables
# ────────────────────────────────────────────────────────
st.header("📋 詳細データ")

tab1, tab2, tab3 = st.tabs(["クラス別集計", "科目別集計", "全データ"])

with tab1:
    st.dataframe(result["class_df"].round(2), use_container_width=True)

with tab2:
    st.dataframe(result["subject_df"].round(2), use_container_width=True)

with tab3:
    st.dataframe(result["df"].round(2), use_container_width=True)

# ────────────────────────────────────────────────────────
# Download Results
# ────────────────────────────────────────────────────────
st.header("💾 ダウンロード")

csv_buffer = StringIO()
result["df"].to_csv(csv_buffer, index=False, encoding="utf-8-sig")
csv_data = csv_buffer.getvalue()

st.download_button(
    label="📥 分析済みデータ (CSV)",
    data=csv_data,
    file_name="attendance_grade_analysis.csv",
    mime="text/csv",
)
