# -*- coding: utf-8 -*-
"""
B-72: 建設 工事原価・予算実績管理ダッシュボード
Streamlit ダッシュボード
"""
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_costs_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_construction_cost_budget_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    if "record_date" in df.columns:
        df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce")
    for col in ["budget_amount", "actual_amount", "variance_rate"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("🏗️ B-72 建設 工事原価・予算実績管理ダッシュボード")
st.caption("B-72 | 建設 × 経理・財務 | 工事番号別予算差異・工種別実績額")

df_all = load_construction_cost_budget_data()

if df_all.empty:
    st.error(f"データが見つかりません: {CSV_PATH}")
    st.info("先にパイプラインを実行してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    projects = sorted(df_all["project_no"].dropna().unique().tolist()) if "project_no" in df_all.columns else []
    selected_projects = st.multiselect("工事番号", projects, default=projects, key="b72_project_filter")
    work_types = sorted(df_all["work_type"].dropna().unique().tolist()) if "work_type" in df_all.columns else []
    selected_work_types = st.multiselect("工種", work_types, default=work_types, key="b72_worktype_filter")

df = df_all.copy()
if selected_projects and "project_no" in df.columns:
    df = df[df["project_no"].isin(selected_projects)]
if selected_work_types and "work_type" in df.columns:
    df = df[df["work_type"].isin(selected_work_types)]

if df.empty:
    st.warning("フィルター条件に一致するデータがありません。")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📊 KPIサマリー", "📈 工事・工種分析", "📋 原価明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    total_budget = df["budget_amount"].sum() if "budget_amount" in df.columns else 0
    total_actual = df["actual_amount"].sum() if "actual_amount" in df.columns else 0
    avg_variance = df["variance_rate"].mean() if "variance_rate" in df.columns else 0
    over_count = int((df["is_over_budget"] == 1).sum()) if "is_over_budget" in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総予算額", f"¥{total_budget:,.0f}")
    col2.metric("総実績額", f"¥{total_actual:,.0f}")
    col3.metric("平均差異率", f"{avg_variance:.2%}" if pd.notna(avg_variance) else "N/A")
    col4.metric("予算超過件数", f"{over_count:,} 件",
                delta="要対応" if over_count > 0 else "正常",
                delta_color="inverse" if over_count > 0 else "normal")

    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        if "budget_status" in df.columns:
            st.subheader("予算状況の内訳")
            status_count = df["budget_status"].value_counts().reset_index()
            status_count.columns = ["予算状況", "件数"]
            st.dataframe(status_count, use_container_width=True, hide_index=True)
    with col_r:
        if "variance_grade" in df.columns:
            st.subheader("超過グレード別件数")
            grade_count = df["variance_grade"].value_counts().reset_index()
            grade_count.columns = ["超過グレード", "件数"]
            st.dataframe(grade_count, use_container_width=True, hide_index=True)

with tab2:
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.subheader("工事番号別 差異率")
        if "project_no" in df.columns and "variance_rate" in df.columns:
            proj_var = df.groupby("project_no")["variance_rate"].mean().sort_values(ascending=True)
            st.bar_chart(proj_var)
    with col_r2:
        st.subheader("工種別 実績額合計")
        if "work_type" in df.columns and "actual_amount" in df.columns:
            wt_actual = df.groupby("work_type")["actual_amount"].sum().sort_values(ascending=True)
            st.bar_chart(wt_actual)

    st.subheader("費目別 予算 vs 実績")
    if "cost_category" in df.columns:
        _agg = {}
        if "budget_amount" in df.columns:
            _agg["予算額"] = ("budget_amount", "sum")
        if "actual_amount" in df.columns:
            _agg["実績額"] = ("actual_amount", "sum")
        if _agg:
            cat_tbl = df.groupby("cost_category", as_index=False).agg(**_agg)
            st.bar_chart(cat_tbl.set_index("cost_category"))

    st.divider()
    st.subheader("工事番号別サマリー")
    if "project_no" in df.columns:
        _pagg = {}
        if "budget_amount" in df.columns:
            _pagg["予算額合計"] = ("budget_amount", "sum")
        if "actual_amount" in df.columns:
            _pagg["実績額合計"] = ("actual_amount", "sum")
        if "is_over_budget" in df.columns:
            _pagg["超過件数"] = ("is_over_budget", "sum")
        if "record_id" in df.columns:
            _pagg["件数"] = ("record_id", "count")
        proj_summary = df.groupby("project_no", as_index=False).agg(**_pagg)
        proj_summary = proj_summary.rename(columns={"project_no": "工事番号"})
        if "予算額合計" in proj_summary.columns and "実績額合計" in proj_summary.columns:
            proj_summary["差異率"] = (
                (proj_summary["実績額合計"] - proj_summary["予算額合計"])
                / proj_summary["予算額合計"].replace(0, float("nan"))
            ).apply(lambda v: f"{v:.2%}" if pd.notna(v) else "N/A")
        st.dataframe(proj_summary, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("原価明細データ")
    col_search, col_sort = st.columns([2, 1])
    with col_search:
        keyword = st.text_input("工事番号・工種・費目で絞り込み", "", key="b72_keyword")
    _sort_options = [c for c in ["record_date", "project_no", "budget_amount",
                                  "actual_amount", "variance_rate"] if c in df.columns]
    with col_sort:
        sort_col = st.selectbox("ソート列", _sort_options, key="b72_sort")

    df_display = df.copy()
    if keyword:
        _masks = []
        for col in ["project_no", "work_type", "cost_category"]:
            if col in df_display.columns:
                _masks.append(df_display[col].astype(str).str.contains(keyword, na=False))
        if _masks:
            import functools, operator
            df_display = df_display[functools.reduce(operator.or_, _masks)]

    if sort_col in df_display.columns:
        df_display = df_display.sort_values(sort_col, ascending=False)

    st.info(f"表示件数: {len(df_display):,} 件")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.divider()
    if REPORT_PATH.exists():
        with st.expander("📄 分析レポート全文を表示", expanded=False):
            st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
    else:
        st.info("分析レポートが見つかりません。analyze.py を実行してください。")
