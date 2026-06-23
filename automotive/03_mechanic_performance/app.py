"""
C-126 整備士別生産性・売上分析 - Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# matplotlib日本語フォント設定
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Hiragino Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# analyze.py をインポート
sys.path.insert(0, str(Path(__file__).parent))
from analyze import (
    load_data,
    calculate_summary,
    analyze_mechanic_performance,
    analyze_service_breakdown,
    analyze_monthly_trend,
    generate_report
)

st.set_page_config(page_title="整備士別生産性・売上分析", layout="wide")

st.title("🔧 整備士別生産性・売上分析ダッシュボード")

# データ読み込み
@st.cache_data
def get_data():
    return load_data("sample_mechanic.csv")

df = get_data()

# 分析実行
summary = calculate_summary(df)
mechanic_results = analyze_mechanic_performance(df)
mechanic_stats = mechanic_results['mechanic_df']
service_stats = analyze_service_breakdown(df)
monthly_stats = analyze_monthly_trend(df)

# ── KPIカード ──────────────────────────────────────────
st.subheader("📊 主要KPI")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "総売上",
        f"¥{summary['total_revenue']:,.0f}",
        delta=f"{summary['job_count']}件"
    )

with col2:
    st.metric(
        "平均顧客評価",
        f"{summary['avg_rating']:.2f}/5",
        delta="⭐" if summary['avg_rating'] >= 4.0 else ""
    )

with col3:
    st.metric(
        "平均時給効率",
        f"¥{summary['avg_hourly_rate']:,.0f}/h",
        delta="👍" if summary['avg_hourly_rate'] >= 6000 else "⚠️"
    )

with col4:
    judgment_color = {
        'good': '🟢 GOOD',
        'warning': '🟡 WARNING',
        'alert': '🔴 ALERT'
    }
    st.metric(
        "全体判定",
        judgment_color.get(summary['overall_judgment'], 'UNKNOWN')
    )

st.divider()

# ── グラフ１: 整備士別売上ランキング ──────────────────────────
st.subheader("💰 整備士別売上ランキング")

fig, ax = plt.subplots(figsize=(10, 5))
mechanic_sorted = mechanic_stats.sort_values('total_revenue', ascending=True)
colors = ['#2ecc71' if j == 'good' else '#f39c12' if j == 'warning' else '#e74c3c'
          for j in mechanic_sorted['judgment']]
ax.barh(mechanic_sorted['mechanic_name'], mechanic_sorted['total_revenue'], color=colors)
ax.set_xlabel('総売上（円）', fontsize=12)
ax.set_title('整備士別売上（色は効率判定）', fontsize=14, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
st.pyplot(fig)

st.divider()

# ── グラフ２: 整備士別平均評価 ──────────────────────────
st.subheader("⭐ 整備士別平均顧客評価")

fig, ax = plt.subplots(figsize=(10, 5))
mechanic_sorted = mechanic_stats.sort_values('avg_rating', ascending=True)
ax.barh(mechanic_sorted['mechanic_name'], mechanic_sorted['avg_rating'], color='#3498db')
ax.set_xlabel('平均評価（5点満点）', fontsize=12)
ax.set_xlim(0, 5)
ax.set_title('整備士別平均顧客評価', fontsize=14, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
st.pyplot(fig)

st.divider()

# ── グラフ３: サービス種別案件数 ──────────────────────────
st.subheader("🛠️ サービス種別案件数")

fig, ax = plt.subplots(figsize=(10, 5))
service_sorted = service_stats.sort_values('job_count', ascending=True)
ax.barh(service_sorted['service_type'], service_sorted['job_count'], color='#9b59b6')
ax.set_xlabel('案件数', fontsize=12)
ax.set_title('サービス種別の案件数分布', fontsize=14, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
st.pyplot(fig)

st.divider()

# ── テーブル: 整備士詳細 ──────────────────────────
st.subheader("📋 整備士詳細情報")

display_df = mechanic_stats[['mechanic_name', 'job_count', 'total_revenue', 'avg_rating', 'total_hours', 'avg_hourly_rate', 'judgment']].copy()
display_df.columns = ['整備士名', '案件数', '総売上', '平均評価', '稼働時間', '時給効率', '判定']

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

st.divider()

# ── 月別トレンド ──────────────────────────
st.subheader("📈 月別トレンド")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 案件数推移
axes[0].plot(monthly_stats['month'], monthly_stats['job_count'], marker='o', linewidth=2, markersize=8, color='#e74c3c')
axes[0].fill_between(range(len(monthly_stats)), monthly_stats['job_count'], alpha=0.3, color='#e74c3c')
axes[0].set_xlabel('月', fontsize=12)
axes[0].set_ylabel('案件数', fontsize=12)
axes[0].set_title('月別案件数推移', fontsize=14, fontweight='bold')
axes[0].grid(alpha=0.3)

# 売上推移
axes[1].plot(monthly_stats['month'], monthly_stats['total_revenue'], marker='s', linewidth=2, markersize=8, color='#2ecc71')
axes[1].fill_between(range(len(monthly_stats)), monthly_stats['total_revenue'], alpha=0.3, color='#2ecc71')
axes[1].set_xlabel('月', fontsize=12)
axes[1].set_ylabel('総売上（円）', fontsize=12)
axes[1].set_title('月別売上推移', fontsize=14, fontweight='bold')
axes[1].grid(alpha=0.3)

st.pyplot(fig)

st.divider()

# ── レポート表示 ──────────────────────────
st.subheader("📄 分析レポート（Markdown）")

report = generate_report(summary, mechanic_stats, service_stats, monthly_stats)
st.markdown(report)

# レポートをダウンロード可能にする
st.download_button(
    label="📥 レポートをダウンロード（Markdown）",
    data=report,
    file_name="mechanic_analysis_report.md",
    mime="text/markdown"
)
