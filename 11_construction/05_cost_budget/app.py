# -*- coding: utf-8 -*-
"""
C-58: Streamlit ダッシュボード
タイトル: 工事原価・予算実績管理ダッシュボード
"""

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

CSV_PATH = OUTPUT_DIR / "cleaned_costs_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["record_date"] = pd.to_datetime(df["record_date"])
    return df


def main():
    st.set_page_config(
        page_title="工事原価・予算実績管理ダッシュボード",
        layout="wide",
    )

    st.title("工事原価・予算実績管理ダッシュボード")
    st.caption("C-58 | 建設 x 経理・財務 | 2024年1月")

    df_all = load_data()

    if df_all.empty:
        st.error("データが見つかりません。パイプラインを実行してください。")
        return

    # -------------------------------------------------------------------
    # サイドバー: フィルター
    # -------------------------------------------------------------------
    st.sidebar.header("フィルター")

    projects = sorted(df_all["project_no"].unique().tolist())
    selected_projects = st.sidebar.multiselect("工事番号", projects, default=projects)

    work_types = sorted(df_all["work_type"].unique().tolist())
    selected_work_types = st.sidebar.multiselect("工種", work_types, default=work_types)

    # フィルター適用
    df = df_all.copy()
    if selected_projects:
        df = df[df["project_no"].isin(selected_projects)]
    if selected_work_types:
        df = df[df["work_type"].isin(selected_work_types)]

    if df.empty:
        st.warning("フィルター条件に一致するデータがありません。")
        return

    # -------------------------------------------------------------------
    # タブ定義
    # -------------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["KPIサマリー", "工事・工種分析", "原価明細データ"])

    # -------------------------------------------------------------------
    # タブ1: KPIサマリー
    # -------------------------------------------------------------------
    with tab1:
        st.subheader("KPIサマリー")

        total_budget = df["budget_amount"].sum()
        total_actual = df["actual_amount"].sum()
        avg_variance_rate = df["variance_rate"].mean()
        over_count = (df["is_over_budget"] == 1).sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("総予算額", f"{total_budget:,.0f} 円")
        col2.metric("総実績額", f"{total_actual:,.0f} 円")
        col3.metric("平均差異率", f"{avg_variance_rate:.2%}")
        col4.metric("予算超過件数", f"{over_count:,} 件")

        st.divider()

        # 予算状況の内訳
        st.subheader("予算状況の内訳")
        status_count = df["budget_status"].value_counts().reset_index()
        status_count.columns = ["予算状況", "件数"]
        st.dataframe(status_count, use_container_width=False, hide_index=True)

        st.divider()

        # 超過グレード別件数
        st.subheader("超過グレード別件数")
        grade_count = df["variance_grade"].value_counts().reset_index()
        grade_count.columns = ["超過グレード", "件数"]
        st.dataframe(grade_count, use_container_width=False, hide_index=True)

    # -------------------------------------------------------------------
    # タブ2: 工事・工種分析（グラフ）
    # -------------------------------------------------------------------
    with tab2:
        st.subheader("工事・工種分析")

        chart_files = {
            "工事番号別 差異率": CHARTS_DIR / "bar_project_variance.png",
            "工種別 実績額合計": CHARTS_DIR / "bar_worktype_actual.png",
            "費目別 予算vs実績": CHARTS_DIR / "bar_category_budget_actual.png",
        }

        for title, path in chart_files.items():
            st.subheader(title)
            if path.exists():
                st.image(str(path), use_container_width=True)
            else:
                st.warning(f"グラフファイルが見つかりません: {path.name}")
            st.divider()

        # 工事番号別サマリーテーブル
        st.subheader("工事番号別サマリー")
        proj_summary = (
            df.groupby("project_no")
            .agg(
                予算額合計=("budget_amount", "sum"),
                実績額合計=("actual_amount", "sum"),
                超過件数=("is_over_budget", "sum"),
                件数=("record_id", "count"),
            )
            .reset_index()
            .rename(columns={"project_no": "工事番号"})
        )
        proj_summary["差異率"] = (
            (proj_summary["実績額合計"] - proj_summary["予算額合計"]) / proj_summary["予算額合計"]
        ).apply(lambda v: f"{v:.2%}")
        st.dataframe(proj_summary, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------
    # タブ3: 原価明細データ
    # -------------------------------------------------------------------
    with tab3:
        st.subheader("原価明細データ")

        # 検索・ソート
        col_search, col_sort = st.columns([2, 1])
        with col_search:
            keyword = st.text_input("工事番号・工種・費目で絞り込み", "")
        with col_sort:
            sort_col = st.selectbox(
                "ソート列",
                ["record_date", "project_no", "budget_amount", "actual_amount", "variance_rate"],
            )

        df_display = df.copy()
        if keyword:
            mask = (
                df_display["project_no"].str.contains(keyword, na=False)
                | df_display["work_type"].str.contains(keyword, na=False)
                | df_display["cost_category"].str.contains(keyword, na=False)
            )
            df_display = df_display[mask]

        df_display = df_display.sort_values(sort_col, ascending=False)

        st.info(f"表示件数: {len(df_display):,} 件")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # 分析レポート
        st.divider()
        st.subheader("分析レポート")
        if REPORT_PATH.exists():
            report = REPORT_PATH.read_text(encoding="utf-8")
            with st.expander("レポート全文を表示", expanded=False):
                st.markdown(report)
        else:
            st.info("分析レポートが見つかりません。analyze.py を実行してください。")


if __name__ == "__main__":
    main()
