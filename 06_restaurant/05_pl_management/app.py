# -*- coding: utf-8 -*-
"""
C-54: 店舗別損益・原価率管理パイプライン
Streamlit ダッシュボード
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import streamlit as st
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
INPUT_FILE = OUTPUT_DIR / "cleaned_pl_202401.csv"


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["food_cost"] = pd.to_numeric(df["food_cost"], errors="coerce")
    df["labor_cost"] = pd.to_numeric(df["labor_cost"], errors="coerce")
    df["other_cost"] = pd.to_numeric(df["other_cost"], errors="coerce")
    df["total_cost"] = pd.to_numeric(df["total_cost"], errors="coerce")
    df["gross_profit"] = pd.to_numeric(df["gross_profit"], errors="coerce")
    df["food_cost_rate"] = pd.to_numeric(df["food_cost_rate"], errors="coerce")
    df["labor_cost_rate"] = pd.to_numeric(df["labor_cost_rate"], errors="coerce")
    df["profit_margin"] = pd.to_numeric(df["profit_margin"], errors="coerce")
    df["record_date"] = pd.to_datetime(df["record_date"], format="%Y-%m-%d", errors="coerce")
    return df


def make_kpi_section(df: pd.DataFrame):
    """KPIカードを表示"""
    total_rev = df["revenue"].sum()
    total_gp = df["gross_profit"].sum()
    avg_fcr = df["food_cost_rate"].mean() * 100
    avg_margin = df["profit_margin"].mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総売上", f"{total_rev:,.0f} 円")
    col2.metric("総粗利", f"{total_gp:,.0f} 円")
    col3.metric("平均食材費率", f"{avg_fcr:.1f}%")
    col4.metric("平均利益率", f"{avg_margin:.1f}%")


def make_store_chart(df: pd.DataFrame):
    """店舗別売上・利益率チャート"""
    store_rev = df.groupby("store_name")["revenue"].sum().sort_values(ascending=False)
    store_margin = df.groupby("store_name").apply(
        lambda g: g["gross_profit"].sum() / g["revenue"].sum() * 100
        if g["revenue"].sum() > 0 else 0
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 売上棒グラフ
    colors_rev = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6"]
    bars = ax1.bar(store_rev.index, store_rev.values, color=colors_rev[: len(store_rev)])
    ax1.set_title("店舗別 総売上", fontsize=13, fontweight="bold")
    ax1.set_xlabel("店舗名")
    ax1.set_ylabel("売上（円）")
    ax1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, h * 1.01, f"{int(h):,}",
                 ha="center", va="bottom", fontsize=8)

    # 利益率横棒
    store_margin_sorted = store_margin.sort_values(ascending=True)
    colors_margin = ["#E74C3C" if v < 0 else "#3498DB" for v in store_margin_sorted.values]
    ax2.barh(store_margin_sorted.index, store_margin_sorted.values, color=colors_margin)
    ax2.set_title("店舗別 利益率（赤=赤字）", fontsize=13, fontweight="bold")
    ax2.set_xlabel("利益率（%）")
    ax2.axvline(x=0, color="black", linewidth=0.8, linestyle="--")

    plt.tight_layout()
    return fig


def make_cost_breakdown_chart(df: pd.DataFrame):
    """コスト内訳積み上げグラフ"""
    store_food = df.groupby("store_name")["food_cost"].sum()
    store_labor = df.groupby("store_name")["labor_cost"].sum()
    store_other = df.groupby("store_name")["other_cost"].sum()
    stores = store_food.index.tolist()

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(stores))
    w = 0.6
    ax.bar(x, store_food.values, w, label="食材費", color="#E74C3C")
    ax.bar(x, store_labor.values, w, bottom=store_food.values, label="人件費", color="#3498DB")
    ax.bar(x, store_other.values, w, bottom=store_food.values + store_labor.values,
           label="その他経費", color="#2ECC71")

    ax.set_title("店舗別 コスト内訳（積み上げ）", fontsize=13, fontweight="bold")
    ax.set_xlabel("店舗名")
    ax.set_ylabel("コスト（円）")
    ax.set_xticks(list(x))
    ax.set_xticklabels(stores)
    ax.legend()
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    plt.tight_layout()
    return fig


def main():
    st.set_page_config(
        page_title="店舗別損益・原価率管理ダッシュボード",
        page_icon=None,
        layout="wide",
    )
    st.title("店舗別損益・原価率管理ダッシュボード")
    st.caption("C-54: 飲食×経理・財務 — P/L管理パイプライン")

    if not INPUT_FILE.exists():
        st.error(f"データファイルが見つかりません: {INPUT_FILE}")
        st.info("先に cleanse.py を実行してください。")
        return

    df_all = load_data()

    # ---- サイドバー: 店舗選択 ----
    stores = sorted(df_all["store_name"].dropna().unique().tolist())
    selected_stores = st.sidebar.multiselect(
        "店舗を選択",
        options=stores,
        default=stores,
    )

    if not selected_stores:
        st.warning("店舗を1つ以上選択してください。")
        return

    df = df_all[df_all["store_name"].isin(selected_stores)].copy()

    # ---- タブ ----
    tab1, tab2, tab3 = st.tabs(["損益サマリー", "店舗別損益分析", "日次P/L明細"])

    # ---- タブ1: 損益サマリー ----
    with tab1:
        st.subheader("損益サマリー（KPIカード）")
        make_kpi_section(df)

        st.subheader("店舗別 損益フラグ集計")
        flag_counts = df["pl_flag"].value_counts().reset_index()
        flag_counts.columns = ["損益フラグ", "件数"]
        st.dataframe(flag_counts, use_container_width=True)

        st.subheader("店舗別 損益サマリーテーブル")
        summary = df.groupby("store_name", as_index=False).agg(
            総売上=("revenue", "sum"),
            総粗利=("gross_profit", "sum"),
            平均食材費率=("food_cost_rate", "mean"),
            平均人件費率=("labor_cost_rate", "mean"),
            平均利益率=("profit_margin", "mean"),
        )
        summary["平均食材費率"] = (summary["平均食材費率"] * 100).round(2).astype(str) + "%"
        summary["平均人件費率"] = (summary["平均人件費率"] * 100).round(2).astype(str) + "%"
        summary["平均利益率"] = (summary["平均利益率"] * 100).round(2).astype(str) + "%"
        st.dataframe(summary, use_container_width=True)

    # ---- タブ2: 店舗別損益分析 ----
    with tab2:
        st.subheader("店舗別 売上・利益率チャート")
        fig_store = make_store_chart(df)
        st.pyplot(fig_store)
        plt.close()

        st.subheader("店舗別 コスト内訳（積み上げ棒グラフ）")
        fig_cost = make_cost_breakdown_chart(df)
        st.pyplot(fig_cost)
        plt.close()

    # ---- タブ3: 日次P/L明細 ----
    with tab3:
        st.subheader("日次P/L明細データ")
        display_df = df[[
            "record_date", "record_id", "store_name",
            "revenue", "food_cost", "labor_cost", "other_cost",
            "total_cost", "gross_profit", "profit_margin", "pl_flag"
        ]].copy()
        display_df["record_date"] = display_df["record_date"].dt.strftime("%Y-%m-%d")
        display_df = display_df.sort_values(["record_date", "store_name"]).reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True)

        st.download_button(
            label="CSVダウンロード",
            data=display_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name="pl_detail.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
