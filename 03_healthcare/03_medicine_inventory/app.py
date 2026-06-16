# -*- coding: utf-8 -*-
"""
C-29: 薬品在庫管理・発注アラートパイプライン
Streamlit ダッシュボードアプリ
"""

import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_medicine_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"
CHARTS_DIR = OUTPUT_DIR / "charts"

st.set_page_config(
    page_title="薬品在庫管理ダッシュボード",
    page_icon="💊",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        st.error(f"データファイルが見つかりません: {CSV_PATH}")
        st.stop()
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


def main():
    st.title("💊 医療・介護 薬品在庫管理ダッシュボード")
    st.caption("C-29 | 物流・在庫 | 2024年1月 集計")

    df_all = load_data()

    # ============================================================
    # サイドバー: 病棟フィルター
    # ============================================================
    st.sidebar.header("フィルター")
    wards = sorted(df_all["ward"].unique().tolist())
    selected_wards = st.sidebar.multiselect("病棟を選択", wards, default=wards)

    if selected_wards:
        df = df_all[df_all["ward"].isin(selected_wards)].copy()
    else:
        df = df_all.copy()

    # ============================================================
    # KPI
    # ============================================================
    total_meds = df["med_code"].nunique()
    shortage_count = (df["alert_level"] == "欠品").sum()
    warning_count = (df["alert_level"] == "警告").sum()
    total_value = df["stock_value"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("管理品目数", f"{total_meds} 品目")
    col2.metric("欠品品目数", f"{shortage_count} 件",
                delta=f"{shortage_count} 件" if shortage_count > 0 else None,
                delta_color="inverse")
    col3.metric("警告品目数", f"{warning_count} 件",
                delta=f"{warning_count} 件" if warning_count > 0 else None,
                delta_color="inverse")
    col4.metric("総在庫金額", f"{total_value:,.0f} 円")

    st.divider()

    # ============================================================
    # タブ
    # ============================================================
    tab1, tab2, tab3 = st.tabs(["アラート状況", "欠品リスクランキング", "カテゴリ別在庫"])

    # ---------- Tab1: アラート状況 ----------
    with tab1:
        st.subheader("アラートレベル別サマリー")
        alert_summary = (
            df.groupby("alert_level")
            .agg(件数=("med_code", "count"), 総在庫金額=("stock_value", "sum"))
            .reset_index()
        )
        st.dataframe(alert_summary, use_container_width=True)

        st.subheader("欠品・警告 明細テーブル")
        alert_detail = df[df["alert_level"].isin(["欠品", "警告"])].sort_values(
            ["alert_level", "days_until_stockout"]
        )
        display_cols = ["alert_level", "med_code", "med_name", "category", "ward",
                        "stock_qty", "min_stock", "daily_usage", "days_until_stockout", "unit_price"]
        st.dataframe(
            alert_detail[display_cols].reset_index(drop=True),
            use_container_width=True,
            column_config={
                "alert_level": st.column_config.TextColumn("アラート"),
                "med_code": st.column_config.TextColumn("薬品コード"),
                "med_name": st.column_config.TextColumn("薬品名"),
                "category": st.column_config.TextColumn("カテゴリ"),
                "ward": st.column_config.TextColumn("病棟"),
                "stock_qty": st.column_config.NumberColumn("在庫数"),
                "min_stock": st.column_config.NumberColumn("最低在庫"),
                "daily_usage": st.column_config.NumberColumn("日次使用量"),
                "days_until_stockout": st.column_config.NumberColumn("残日数"),
                "unit_price": st.column_config.NumberColumn("単価(円)"),
            },
        )

        # グラフ表示
        chart_path = CHARTS_DIR / "bar_ward_alert.png"
        if chart_path.exists():
            st.subheader("病棟別 欠品・警告品目数")
            st.image(str(chart_path), use_container_width=True)

    # ---------- Tab2: 欠品リスクランキング ----------
    with tab2:
        st.subheader("欠品リスク上位10品目（在庫残日数が少ない順）")
        risk_df = df[df["days_until_stockout"].notna()].copy()
        risk_top10 = (
            risk_df.sort_values("days_until_stockout")
            .drop_duplicates("med_code")
            .head(10)[["med_code", "med_name", "category", "ward",
                       "stock_qty", "min_stock", "daily_usage",
                       "days_until_stockout", "alert_level"]]
            .reset_index(drop=True)
        )
        st.dataframe(risk_top10, use_container_width=True)

        chart_path = CHARTS_DIR / "bar_stockout_risk_top10.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)

    # ---------- Tab3: カテゴリ別在庫 ----------
    with tab3:
        st.subheader("カテゴリ別在庫金額構成")
        cat_val = (
            df.groupby("category")
            .agg(総在庫金額=("stock_value", "sum"), 品目数=("med_code", "nunique"))
            .sort_values("総在庫金額", ascending=False)
            .reset_index()
        )
        total = cat_val["総在庫金額"].sum()
        cat_val["構成比率(%)"] = (cat_val["総在庫金額"] / total * 100).round(1)
        st.dataframe(cat_val, use_container_width=True)

        chart_path = CHARTS_DIR / "pie_category_stock_value.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)

    # ============================================================
    # 分析レポート
    # ============================================================
    if REPORT_PATH.exists():
        with st.expander("分析レポートを表示"):
            report_text = REPORT_PATH.read_text(encoding="utf-8")
            st.markdown(report_text)


if __name__ == "__main__":
    main()
