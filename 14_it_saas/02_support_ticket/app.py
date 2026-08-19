# -*- coding: utf-8 -*-
"""
B-51 IT/SaaS - カスタマーサポートチケット分析
Streamlit ダッシュボード: CSチケット分析ダッシュボード
"""

import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CLEANED_PATH = BASE_DIR / "output" / "cleaned_tickets_202401.csv"


@st.cache_data
def load_support_ticket_data() -> pd.DataFrame:
    if not CLEANED_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CLEANED_PATH, encoding="utf-8-sig")
    for col in ["resolution_hours", "is_resolved", "is_escalated", "satisfaction"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("💻 B-51 CSチケット分析ダッシュボード")
st.markdown("**2024年1月分 カスタマーサポートチケット集計**")

df_all = load_support_ticket_data()

if df_all.empty:
    st.error("データファイルが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# --- サイドバー: フィルター ---
with st.sidebar:
    st.header("フィルター設定")

    all_categories = sorted(df_all["category"].dropna().unique().tolist()) if "category" in df_all.columns else []
    selected_categories = st.multiselect(
        "カテゴリ選択",
        options=all_categories,
        default=all_categories,
    )

    priority_col_exists = "priority" in df_all.columns
    all_priorities = ["高", "中", "低"]
    available_prios = [p for p in all_priorities if priority_col_exists and p in df_all["priority"].unique()]
    selected_priorities = st.multiselect(
        "優先度選択",
        options=available_prios,
        default=available_prios,
    )

# フィルター適用
mask = pd.Series([True] * len(df_all), index=df_all.index)
if "category" in df_all.columns and selected_categories:
    mask &= df_all["category"].isin(selected_categories)
if priority_col_exists and selected_priorities:
    mask &= df_all["priority"].isin(selected_priorities)
df = df_all[mask].copy()

with st.sidebar:
    st.markdown(f"**表示件数:** {len(df):,} 件")

if df.empty:
    st.warning("選択条件に一致するデータがありません。")
    st.stop()

# --- タブ ---
tab1, tab2, tab3 = st.tabs(["KPIサマリー", "カテゴリ・優先度分析", "チケット明細"])

# ====== Tab1: KPIサマリー ======
with tab1:
    st.subheader("KPIサマリー")
    total = len(df)
    resolved = int(df["is_resolved"].sum()) if "is_resolved" in df.columns else 0
    resolve_rate = resolved / total if total > 0 else 0
    avg_rh = df["resolution_hours"].mean() if "resolution_hours" in df.columns else 0.0
    avg_sat = df["satisfaction"].mean() if "satisfaction" in df.columns else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総チケット数", f"{total:,}件")
    col2.metric("解決率", f"{resolve_rate:.1%}")
    col3.metric("平均解決時間", f"{avg_rh:.1f}h")
    col4.metric("平均満足度", f"{avg_sat:.2f}点")

    st.markdown("---")
    if "is_escalated" in df.columns:
        esc_count = int(df["is_escalated"].sum())
        esc_rate = esc_count / total if total > 0 else 0
        st.markdown(f"**エスカレーション:** {esc_count}件 ({esc_rate:.1%})")

# ====== Tab2: カテゴリ・優先度分析 ======
with tab2:
    st.subheader("カテゴリ別チケット件数")
    if "category" in df.columns:
        id_col = "ticket_id" if "ticket_id" in df.columns else df.columns[0]
        cat_counts = df.groupby("category")[id_col].count().sort_values(ascending=False)
        st.bar_chart(cat_counts)

    st.subheader("優先度別エスカレーション率")
    if priority_col_exists and "is_escalated" in df.columns:
        prio_order = [p for p in ["高", "中", "低"] if p in df["priority"].unique()]
        prio_esc = df.groupby("priority")["is_escalated"].mean().reindex(prio_order, fill_value=0) * 100
        st.bar_chart(prio_esc)

# ====== Tab3: チケット明細 ======
with tab3:
    st.subheader("チケット明細データ")
    display_cols = [
        "received_date", "ticket_id", "category", "priority",
        "agent_id", "resolution_hours", "is_escalated",
        "satisfaction", "is_resolved", "speed_grade", "cs_level",
    ]
    show_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[show_cols].reset_index(drop=True) if show_cols else df, use_container_width=True)
    st.markdown(f"**件数:** {len(df):,}件")
