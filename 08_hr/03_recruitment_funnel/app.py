"""
C-33: Streamlit ダッシュボード
タイトル: 人事・採用 採用ファネル分析ダッシュボード
"""

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

CSV_PATH = OUTPUT_DIR / "cleaned_recruitment_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"

PHASE_ORDER = {
    "書類選考": 1,
    "一次面接": 2,
    "二次面接": 3,
    "最終面接": 4,
    "内定": 5,
}
PHASES = ["書類選考", "一次面接", "二次面接", "最終面接", "内定"]


@st.cache_data
def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def main():
    st.set_page_config(
        page_title="採用ファネル分析ダッシュボード",
        page_icon="👔",
        layout="wide",
    )

    st.title("👔 人事・採用 採用ファネル分析ダッシュボード")
    st.caption("C-33 | 2024年1月-3月 | 採用歩留まり率分析レポート")

    df = load_data()

    if df.empty:
        st.error("データが見つかりません。パイプラインを実行してください。")
        return

    # サイドバー: チャネルフィルター
    st.sidebar.header("フィルター")
    channels = sorted(df["channel"].unique().tolist())
    selected_channels = st.sidebar.multiselect("採用チャネル", channels, default=channels)

    if selected_channels:
        df_filtered = df[df["channel"].isin(selected_channels)].copy()
    else:
        df_filtered = df.copy()

    # -------------------------------------------------------------------
    # KPI メトリクス (4つ)
    # -------------------------------------------------------------------
    total_applicants = len(df_filtered)
    hired_count = int(df_filtered["is_hired"].sum())
    overall_rate = hired_count / total_applicants * 100 if total_applicants > 0 else 0
    avg_screening_days = df_filtered["screening_days"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総応募数", f"{total_applicants:,} 名")
    col2.metric("採用人数", f"{hired_count:,} 名")
    col3.metric("総採用率", f"{overall_rate:.1f}%")
    col4.metric("平均選考日数", f"{avg_screening_days:.1f} 日")

    st.divider()

    # -------------------------------------------------------------------
    # タブ: ファネル分析 / チャネル別採用率 / 職種別選考日数
    # -------------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["ファネル分析", "チャネル別採用率", "職種別選考日数"])

    with tab1:
        st.subheader("フェーズ別 到達率（採用ファネル）")
        chart_path = CHARTS_DIR / "bar_funnel_passrate.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        # フェーズ別サマリーテーブル
        funnel_rows = []
        for phase in PHASES:
            phase_num = PHASE_ORDER[phase]
            count = (df_filtered["phase_order"] >= phase_num).sum()
            rate = count / total_applicants * 100 if total_applicants > 0 else 0
            funnel_rows.append({
                "フェーズ": phase,
                "到達者数": f"{count:,} 名",
                "到達率(全体比)": f"{rate:.1f}%",
            })
        st.dataframe(pd.DataFrame(funnel_rows), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("チャネル別 採用率")
        chart_path = CHARTS_DIR / "bar_channel_hire_rate.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        channel_summary = (
            df_filtered.groupby("channel")
            .agg(
                応募数=("applicant_id", "count"),
                採用数=("is_hired", "sum"),
                平均選考日数=("screening_days", "mean"),
            )
            .reset_index()
            .rename(columns={"channel": "チャネル"})
        )
        channel_summary["採用率"] = (
            channel_summary["採用数"] / channel_summary["応募数"] * 100
        ).round(1).astype(str) + "%"
        channel_summary["平均選考日数"] = channel_summary["平均選考日数"].round(1)
        st.dataframe(channel_summary, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("職種別 平均選考日数")
        chart_path = CHARTS_DIR / "bar_jobtype_screening_days.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        jobtype_summary = (
            df_filtered.groupby("job_type")
            .agg(
                応募数=("applicant_id", "count"),
                採用数=("is_hired", "sum"),
                平均選考日数=("screening_days", "mean"),
            )
            .reset_index()
            .rename(columns={"job_type": "職種"})
        )
        jobtype_summary["採用率"] = (
            jobtype_summary["採用数"] / jobtype_summary["応募数"] * 100
        ).round(1).astype(str) + "%"
        jobtype_summary["平均選考日数"] = jobtype_summary["平均選考日数"].round(1)
        st.dataframe(jobtype_summary, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------------
    # 採用者リストテーブル
    # -------------------------------------------------------------------
    st.subheader("採用者リスト")
    hired_df = df_filtered[df_filtered["is_hired"] == 1].copy()
    if hired_df.empty:
        st.info("採用者はいません。")
    else:
        hired_detail = (
            hired_df[["apply_date", "applicant_id", "job_type", "channel",
                       "reached_phase", "screening_days"]]
            .rename(columns={
                "apply_date":    "応募日",
                "applicant_id":  "応募者ID",
                "job_type":      "職種",
                "channel":       "採用チャネル",
                "reached_phase": "到達フェーズ",
                "screening_days": "選考日数",
            })
            .sort_values("応募日")
        )
        st.dataframe(hired_detail, use_container_width=True, hide_index=True)

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
