# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
Streamlit ダッシュボード: CSチケット分析ダッシュボード
"""

import os
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'
import matplotlib.pyplot as plt
import streamlit as st

BASE_DIR = os.path.dirname(__file__)
CLEANED_PATH = os.path.join(BASE_DIR, "output", "cleaned_tickets_202401.csv")


@st.cache_data
def load_data():
    df = pd.read_csv(CLEANED_PATH, encoding="utf-8-sig")
    df["resolution_hours"] = pd.to_numeric(df["resolution_hours"], errors="coerce")
    df["is_resolved"] = pd.to_numeric(df["is_resolved"], errors="coerce")
    df["is_escalated"] = pd.to_numeric(df["is_escalated"], errors="coerce")
    df["satisfaction"] = pd.to_numeric(df["satisfaction"], errors="coerce")
    return df


def main():
    st.set_page_config(
        page_title="CSチケット分析ダッシュボード",
        page_icon=None,
        layout="wide",
    )
    st.title("CSチケット分析ダッシュボード")
    st.markdown("**2024年1月分 カスタマーサポートチケット集計**")

    if not os.path.exists(CLEANED_PATH):
        st.error(f"データファイルが見つかりません: {CLEANED_PATH}")
        st.info("先に cleanse.py を実行してください。")
        return

    df_all = load_data()

    # --- サイドバー: フィルター ---
    st.sidebar.header("フィルター設定")

    all_categories = sorted(df_all["category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "カテゴリ選択",
        options=all_categories,
        default=all_categories,
    )

    all_priorities = ["高", "中", "低"]
    available_prios = [p for p in all_priorities if p in df_all["priority"].unique()]
    selected_priorities = st.sidebar.multiselect(
        "優先度選択",
        options=available_prios,
        default=available_prios,
    )

    # フィルター適用
    df = df_all[
        df_all["category"].isin(selected_categories) &
        df_all["priority"].isin(selected_priorities)
    ].copy()

    st.sidebar.markdown(f"**表示件数:** {len(df):,} 件")

    if len(df) == 0:
        st.warning("選択条件に一致するデータがありません。")
        return

    # --- タブ ---
    tab1, tab2, tab3 = st.tabs(["KPIサマリー", "カテゴリ・優先度分析", "チケット明細"])

    # ====== Tab1: KPIサマリー ======
    with tab1:
        st.subheader("KPIサマリー")
        total = len(df)
        resolved = int(df["is_resolved"].sum())
        resolve_rate = resolved / total if total > 0 else 0
        avg_rh = df["resolution_hours"].mean()
        avg_sat = df["satisfaction"].mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("総チケット数", f"{total:,}件")
        col2.metric("解決率", f"{resolve_rate:.1%}")
        col3.metric("平均解決時間", f"{avg_rh:.1f}h")
        col4.metric("平均満足度", f"{avg_sat:.2f}点")

        st.markdown("---")
        esc_count = int(df["is_escalated"].sum())
        esc_rate = esc_count / total if total > 0 else 0
        st.markdown(f"**エスカレーション:** {esc_count}件 ({esc_rate:.1%})")

    # ====== Tab2: カテゴリ・優先度分析 ======
    with tab2:
        st.subheader("カテゴリ別チケット件数")
        cat_counts = df.groupby("category")["ticket_id"].count().sort_values()
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.barh(cat_counts.index, cat_counts.values, color="#4C72B0")
        ax1.set_xlabel("チケット件数")
        ax1.set_title("カテゴリ別チケット件数")
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close()

        st.subheader("優先度別エスカレーション率")
        prio_order = [p for p in ["高", "中", "低"] if p in df["priority"].unique()]
        prio_esc = df.groupby("priority")["is_escalated"].mean().reindex(prio_order, fill_value=0)
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        colors = {"高": "#e74c3c", "中": "#f39c12", "低": "#2ecc71"}
        bar_colors = [colors.get(p, "#999") for p in prio_esc.index]
        ax2.bar(prio_esc.index, prio_esc.values * 100, color=bar_colors)
        ax2.set_ylabel("エスカレーション率 (%)")
        ax2.set_title("優先度別エスカレーション率")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    # ====== Tab3: チケット明細 ======
    with tab3:
        st.subheader("チケット明細データ")
        display_cols = [
            "received_date", "ticket_id", "category", "priority",
            "agent_id", "resolution_hours", "is_escalated",
            "satisfaction", "is_resolved", "speed_grade", "cs_level",
        ]
        show_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[show_cols].reset_index(drop=True), use_container_width=True)
        st.markdown(f"**件数:** {len(df):,}件")


if __name__ == "__main__":
    main()
