"""
C-30: Streamlit ダッシュボード
タイトル: 人事・採用 人件費予実ダッシュボード
"""

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

CSV_PATH = OUTPUT_DIR / "cleaned_labor_cost_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def main():
    st.set_page_config(
        page_title="人件費予実ダッシュボード",
        page_icon="👥",
        layout="wide",
    )

    st.title("👥 人事・採用 人件費予実ダッシュボード")
    st.caption("C-30 | 2024年度 | 人件費推移・予実差異レポート")

    df = load_data()

    if df.empty:
        st.error("データが見つかりません。パイプラインを実行してください。")
        return

    # サイドバー: 部門フィルター
    st.sidebar.header("フィルター")
    departments = sorted(df["department"].unique().tolist())
    selected_depts = st.sidebar.multiselect("部門", departments, default=departments)

    if selected_depts:
        df_filtered = df[df["department"].isin(selected_depts)].copy()
    else:
        df_filtered = df.copy()

    # -------------------------------------------------------------------
    # KPI メトリクス
    # -------------------------------------------------------------------
    budget_total = df_filtered["budget_cost"].sum()
    actual_total = df_filtered["actual_cost"].sum()
    variance_total = df_filtered["variance_amount"].sum()
    over_dept_count = df_filtered[df_filtered["variance_flag"] == "超過"]["department"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("予算合計", f"{budget_total:,.0f} 円")
    col2.metric("実績合計", f"{actual_total:,.0f} 円")
    col3.metric("差異合計", f"{variance_total:+,.0f} 円",
                delta=f"{variance_total / budget_total * 100:+.1f}%" if budget_total > 0 else "N/A")
    col4.metric("超過部門数", f"{over_dept_count} 部門")

    st.divider()

    # -------------------------------------------------------------------
    # タブ: 予実差異 / 雇用区分別 / 月別トレンド
    # -------------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["予実差異", "雇用区分別", "月別トレンド"])

    with tab1:
        st.subheader("部門別 予実差異")
        chart_path = CHARTS_DIR / "bar_dept_variance.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        # 部門別サマリーテーブル
        dept_summary = (
            df_filtered.groupby("department")
            .agg(
                予算合計=("budget_cost", "sum"),
                実績合計=("actual_cost", "sum"),
                差異額=("variance_amount", "sum"),
                超過回数=("variance_flag", lambda x: (x == "超過").sum()),
            )
            .round(0)
            .reset_index()
            .rename(columns={"department": "部門"})
            .sort_values("差異額", ascending=False)
        )
        dept_summary["差異率"] = (dept_summary["差異額"] / dept_summary["予算合計"] * 100).round(1).astype(str) + "%"
        st.dataframe(dept_summary, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("雇用区分別 人件費構成")
        chart_path = CHARTS_DIR / "bar_employment_cost.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        emp_summary = (
            df_filtered.groupby("employment_type")
            .agg(
                予算合計=("budget_cost", "sum"),
                実績合計=("actual_cost", "sum"),
                残業代合計=("overtime_cost", "sum"),
                平均人員数=("head_count", "mean"),
            )
            .round(0)
            .reset_index()
            .rename(columns={"employment_type": "雇用区分"})
        )
        st.dataframe(emp_summary, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("月別 人件費推移（予算 vs 実績）")
        chart_path = CHARTS_DIR / "line_monthly_trend.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        trend_summary = (
            df_filtered.groupby("year_month")
            .agg(
                予算合計=("budget_cost", "sum"),
                実績合計=("actual_cost", "sum"),
                残業代=("overtime_cost", "sum"),
            )
            .round(0)
            .reset_index()
            .rename(columns={"year_month": "年月"})
            .sort_values("年月")
        )
        st.dataframe(trend_summary, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------------
    # 超過部門明細テーブル
    # -------------------------------------------------------------------
    st.subheader("超過部門明細")
    over_df = df_filtered[df_filtered["variance_flag"] == "超過"].copy()
    if over_df.empty:
        st.info("超過部門はありません。")
    else:
        over_detail = (
            over_df[["year_month", "department", "employment_type",
                      "budget_cost", "actual_cost", "variance_amount", "variance_rate"]]
            .rename(columns={
                "year_month":       "年月",
                "department":       "部門",
                "employment_type":  "雇用区分",
                "budget_cost":      "予算",
                "actual_cost":      "実績",
                "variance_amount":  "差異額",
                "variance_rate":    "差異率",
            })
            .sort_values("差異率", ascending=False)
        )
        over_detail["差異率"] = (over_detail["差異率"] * 100).round(1).astype(str) + "%"
        st.dataframe(over_detail, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------------
    # 分析レポート expander
    # -------------------------------------------------------------------
    st.subheader("分析レポート")
    if REPORT_PATH.exists():
        report = REPORT_PATH.read_text(encoding="utf-8")
        with st.expander("レポート全文を表示", expanded=False):
            st.markdown(report)
    else:
        st.info("分析レポートが見つかりません。analyze.py を実行してください。")


if __name__ == "__main__":
    main()
