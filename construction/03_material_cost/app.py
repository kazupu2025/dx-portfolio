"""
C-122 資材コスト・発注管理 Streamlit ダッシュボード

KPIカード4つ、カテゴリ別円グラフ、月次折れ線グラフ、
仕入先別棒グラフ、資材一覧テーブルを表示。
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import japanize_matplotlib

from analyze import run_analysis

# 日本語フォント設定
plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
sns.set_style("whitegrid")

# ページ設定
st.set_page_config(
    page_title="C-122 資材コスト・発注管理",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 C-122 資材コスト・発注管理")
st.markdown("---")

# データ読み込みとキャッシング
@st.cache_data
def load_and_analyze():
    """データを読み込み分析を実行"""
    analyzer = run_analysis(
        csv_file="sample_material.csv",
        config_file="config.yml"
    )
    return analyzer

# データを読み込み
try:
    analyzer = load_and_analyze()
    df = analyzer.df
    stats = analyzer.get_summary_stats()
except FileNotFoundError:
    st.error("⚠️ データファイルが見つかりません。")
    st.stop()

# ============ KPI カード ============
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💰 総発注額",
        value=f"¥{stats['total_cost']:,.0f}",
        delta=None
    )

with col2:
    st.metric(
        label="📦 品目数",
        value=f"{stats['item_count']} 件",
        delta=None
    )

with col3:
    st.metric(
        label="🏆 最多カテゴリ",
        value=stats['category_with_max_cost'],
        delta=f"¥{stats['max_cost']:,.0f}"
    )

with col4:
    verdict_emoji = {"good": "✅", "warning": "⚠️", "alert": "🔴"}
    verdict_color = {
        "good": "background-color: #d4edda; color: #155724;",
        "warning": "background-color: #fff3cd; color: #856404;",
        "alert": "background-color: #f8d7da; color: #721c24;"
    }
    st.markdown(
        f"<div style='padding: 15px; border-radius: 8px; {verdict_color[stats['verdict']]}'>"
        f"<strong>{verdict_emoji[stats['verdict']]} 判定: {stats['verdict'].upper()}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ============ 分析タブ ============
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 カテゴリ分析", "📅 月次推移", "🏢 プロジェクト別", "🏭 仕入先別", "📋 資材一覧"]
)

# ── Tab 1: カテゴリ別コスト構成 ──
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("カテゴリ別コスト（円グラフ）")
        df_cat = analyzer.df_by_category.reset_index()
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = plt.cm.Set3(range(len(df_cat)))
        ax.pie(
            df_cat["total_cost"],
            labels=df_cat["category"],
            autopct="%1.1f%%",
            colors=colors,
            startangle=90
        )
        ax.set_title("カテゴリ別コスト構成", fontsize=14, fontweight="bold")
        st.pyplot(fig)
        plt.close()

    with col2:
        st.subheader("カテゴリ別統計")
        display_df = df_cat[["category", "total_cost", "item_count", "total_quantity"]].copy()
        display_df.columns = ["カテゴリ", "総コスト(円)", "品目数", "総数量"]
        display_df["総コスト(円)"] = display_df["総コスト(円)"].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── Tab 2: 月次コスト推移 ──
with tab2:
    st.subheader("月次コスト推移（折れ線グラフ）")
    df_monthly = analyzer.df_by_month.copy()
    df_monthly["year_month"] = df_monthly["year_month"].astype(str)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(
        df_monthly["year_month"],
        df_monthly["monthly_cost"],
        marker="o",
        linewidth=2,
        markersize=8,
        color="#1f77b4"
    )
    ax.fill_between(
        range(len(df_monthly)),
        df_monthly["monthly_cost"],
        alpha=0.3,
        color="#1f77b4"
    )
    ax.set_xlabel("年月", fontsize=12)
    ax.set_ylabel("コスト（円）", fontsize=12)
    ax.set_title("月次コスト推移", fontsize=14, fontweight="bold")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"¥{x/1e6:.0f}M"))
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    st.pyplot(fig)
    plt.close()

    st.subheader("月次変動率")
    display_monthly = df_monthly[["year_month", "monthly_cost", "cost_variance_rate"]].copy()
    display_monthly.columns = ["年月", "月次コスト(円)", "変動率(%)"]
    display_monthly["月次コスト(円)"] = display_monthly["月次コスト(円)"].apply(lambda x: f"¥{x:,.0f}")
    st.dataframe(display_monthly, use_container_width=True, hide_index=True)

# ── Tab 3: プロジェクト別コスト ──
with tab3:
    st.subheader("プロジェクト別発注額（棒グラフ）")
    df_proj = analyzer.df_by_project.reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(df_proj["project_id"], df_proj["total_cost"], color="#2ca02c", alpha=0.7)
    ax.set_xlabel("プロジェクトID", fontsize=12)
    ax.set_ylabel("総コスト（円）", fontsize=12)
    ax.set_title("プロジェクト別発注額", fontsize=14, fontweight="bold")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"¥{x/1e6:.0f}M"))
    ax.grid(True, alpha=0.3, axis="y")

    # 値をバーの上に表示
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height,
            f"¥{height/1e6:.1f}M",
            ha="center",
            va="bottom",
            fontsize=10
        )

    st.pyplot(fig)
    plt.close()

    st.subheader("プロジェクト別統計")
    display_proj = df_proj[["project_id", "total_cost", "item_count", "total_quantity"]].copy()
    display_proj.columns = ["プロジェクトID", "総コスト(円)", "品目数", "総数量"]
    display_proj["総コスト(円)"] = display_proj["総コスト(円)"].apply(lambda x: f"¥{x:,.0f}")
    st.dataframe(display_proj, use_container_width=True, hide_index=True)

# ── Tab 4: 仕入先別発注額 ──
with tab4:
    st.subheader("仕入先別発注額（棒グラフ）")
    df_supp = analyzer.df_by_supplier.reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(df_supp["supplier"], df_supp["total_cost"], color="#ff7f0e", alpha=0.7)
    ax.set_xlabel("総発注額（円）", fontsize=12)
    ax.set_ylabel("仕入先", fontsize=12)
    ax.set_title("仕入先別発注額", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"¥{x/1e6:.0f}M"))
    ax.grid(True, alpha=0.3, axis="x")

    # 値をバーの右に表示
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width,
            bar.get_y() + bar.get_height() / 2.,
            f"¥{width/1e6:.1f}M",
            ha="left",
            va="center",
            fontsize=10
        )

    st.pyplot(fig)
    plt.close()

    st.subheader("仕入先別統計")
    display_supp = df_supp[["supplier", "total_cost", "order_count", "total_quantity"]].copy()
    display_supp.columns = ["仕入先", "総発注額(円)", "発注件数", "総数量"]
    display_supp["総発注額(円)"] = display_supp["総発注額(円)"].apply(lambda x: f"¥{x:,.0f}")
    st.dataframe(display_supp, use_container_width=True, hide_index=True)

# ── Tab 5: 資材一覧テーブル ──
with tab5:
    st.subheader("資材発注一覧")

    # フィルター
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_category = st.multiselect(
            "カテゴリで絞り込む",
            options=df["category"].unique(),
            default=df["category"].unique()
        )
    with col2:
        selected_project = st.multiselect(
            "プロジェクトで絞り込む",
            options=df["project_id"].unique(),
            default=df["project_id"].unique()
        )
    with col3:
        selected_supplier = st.multiselect(
            "仕入先で絞り込む",
            options=df["supplier"].unique(),
            default=df["supplier"].unique()
        )

    # フィルタリング
    filtered_df = df[
        (df["category"].isin(selected_category)) &
        (df["project_id"].isin(selected_project)) &
        (df["supplier"].isin(selected_supplier))
    ].copy()

    # 表示用にフォーマット
    display_table = filtered_df[[
        "date", "material_name", "category", "project_id",
        "quantity", "unit", "unit_price", "total_cost", "supplier"
    ]].copy()
    display_table.columns = [
        "日付", "資材名", "カテゴリ", "プロジェクトID",
        "数量", "単位", "単価(円)", "総コスト(円)", "仕入先"
    ]
    display_table["日付"] = pd.to_datetime(display_table["日付"]).dt.strftime("%Y-%m-%d")
    display_table["単価(円)"] = display_table["単価(円)"].apply(lambda x: f"¥{x:,.0f}")
    display_table["総コスト(円)"] = display_table["総コスト(円)"].apply(lambda x: f"¥{x:,.0f}")
    display_table = display_table.sort_values("日付", ascending=False)

    st.dataframe(display_table, use_container_width=True, hide_index=True)

    st.markdown(f"**表示件数:** {len(display_table)} / {len(df)} 件")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 12px;'>"
    "C-122 資材コスト・発注管理 | 作成日: 2026-06-24"
    "</div>",
    unsafe_allow_html=True
)
