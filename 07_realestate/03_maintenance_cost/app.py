"""
C-23: Streamlit ダッシュボード
タイトル: 不動産 管理費・修繕費ダッシュボード
"""

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

CSV_PATH = OUTPUT_DIR / "cleaned_maintenance_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["occurrence_date"] = pd.to_datetime(df["occurrence_date"])
    return df


def main():
    st.set_page_config(
        page_title="不動産 管理費・修繕費ダッシュボード",
        page_icon="",
        layout="wide",
    )

    st.title("不動産 管理費・修繕費ダッシュボード")
    st.caption("C-23 | 2024年1月 | 物件50棟")

    df = load_data()

    if df.empty:
        st.error("データが見つかりません。パイプラインを実行してください。")
        return

    # サイドバー: エリアフィルター
    st.sidebar.header("フィルター")
    areas = sorted(df["area"].unique().tolist())
    selected_areas = st.sidebar.multiselect("エリア", areas, default=areas)

    if selected_areas:
        df_filtered = df[df["area"].isin(selected_areas)].copy()
    else:
        df_filtered = df.copy()

    # -------------------------------------------------------------------
    # メトリクス
    # -------------------------------------------------------------------
    total_cost = df_filtered["cost_amount"].sum()
    repair_cost = df_filtered[df_filtered["is_repair"] == True]["cost_amount"].sum()
    urgent_cost = df_filtered[df_filtered["is_urgent"] == True]["cost_amount"].sum()
    high_count = (df_filtered["cost_per_unit_flag"] == "高額").sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総コスト", f"{total_cost:,.0f} 円")
    col2.metric("修繕費合計", f"{repair_cost:,.0f} 円")
    col3.metric("緊急対応コスト", f"{urgent_cost:,.0f} 円")
    col4.metric("高額案件数", f"{high_count} 件")

    st.divider()

    # -------------------------------------------------------------------
    # グラフ表示
    # -------------------------------------------------------------------
    st.subheader("グラフ")

    chart_files = {
        "エリア別コスト（費用区分別積み上げ）": CHARTS_DIR / "bar_area_cost.png",
        "コスト上位10物件": CHARTS_DIR / "bar_property_cost_top10.png",
        "費用区分別コスト構成比": CHARTS_DIR / "pie_cost_category.png",
    }

    cols = st.columns(len(chart_files))
    for col, (title, path) in zip(cols, chart_files.items()):
        with col:
            st.caption(title)
            if path.exists():
                st.image(str(path), use_container_width=True)
            else:
                st.warning(f"グラフファイルが見つかりません: {path.name}")

    st.divider()

    # -------------------------------------------------------------------
    # エリア別サマリーテーブル
    # -------------------------------------------------------------------
    st.subheader("エリア別サマリー")
    area_summary = (
        df_filtered.groupby("area")
        .agg(
            コスト合計=("cost_amount", "sum"),
            件数=("cost_amount", "count"),
            平均コスト=("cost_amount", "mean"),
            物件数=("property_id", "nunique"),
        )
        .round(0)
        .reset_index()
        .rename(columns={"area": "エリア"})
        .sort_values("コスト合計", ascending=False)
    )
    st.dataframe(area_summary, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------------
    # 費用区分別サマリーテーブル
    # -------------------------------------------------------------------
    st.subheader("費用区分別サマリー")
    cat_summary = (
        df_filtered.groupby("cost_category")
        .agg(
            コスト合計=("cost_amount", "sum"),
            件数=("cost_amount", "count"),
            平均コスト=("cost_amount", "mean"),
        )
        .round(0)
        .reset_index()
        .rename(columns={"cost_category": "費用区分"})
        .sort_values("コスト合計", ascending=False)
    )
    st.dataframe(cat_summary, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------------
    # 分析レポート
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
