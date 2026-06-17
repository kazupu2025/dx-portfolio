"""
C-41: Streamlit ダッシュボード
タイトル: 人事採用 採用コスト分析ダッシュボード
"""

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

CSV_PATH = OUTPUT_DIR / "cleaned_recruitment_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"

PHASES = ["書類選考", "一次面接", "二次面接", "最終面接", "内定"]


@st.cache_data
def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    return df


def main():
    st.set_page_config(
        page_title="採用コスト分析ダッシュボード",
        page_icon="👥",
        layout="wide",
    )

    st.title("👥 人事採用 採用コスト分析ダッシュボード")
    st.caption("C-41 | 2024年1月-3月 | 採用チャネル別コスト・採用レポート")

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
    hire_rate = hired_count / total_applicants * 100 if total_applicants > 0 else 0
    avg_cost = df_filtered["cost"].mean() if total_applicants > 0 else 0

    # 内定承諾率
    if "offer_acceptance" in df_filtered.columns and hired_count > 0:
        accepted = (df_filtered["offer_acceptance"] == "承諾").sum()
        offer_acceptance_rate = accepted / hired_count * 100
    else:
        offer_acceptance_rate = 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総応募数", f"{total_applicants:,} 名")
    col2.metric("採用率", f"{hire_rate:.1f}%")
    col3.metric("平均採用コスト", f"{avg_cost:,.0f} 円")
    col4.metric("内定承諾率", f"{offer_acceptance_rate:.1f}%")

    st.divider()

    # -------------------------------------------------------------------
    # タブ: チャネル別コスト / 採用ファネル / 職種別採用
    # -------------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["チャネル別コスト", "採用ファネル", "職種別採用"])

    with tab1:
        st.subheader("チャネル別 平均採用コスト")
        chart_path = CHARTS_DIR / "bar_channel_cost.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        st.subheader("チャネル別 採用率")
        chart_path2 = CHARTS_DIR / "bar_channel_hire_rate.png"
        if chart_path2.exists():
            st.image(str(chart_path2), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        # チャネル別サマリーテーブル
        channel_summary = (
            df_filtered.groupby("channel")
            .agg(
                応募数=("apply_no", "count"),
                採用数=("is_hired", "sum"),
                平均コスト=("cost", "mean"),
                最小コスト=("cost", "min"),
                最大コスト=("cost", "max"),
            )
            .reset_index()
            .rename(columns={"channel": "チャネル"})
        )
        channel_summary["採用率"] = (
            channel_summary["採用数"] / channel_summary["応募数"] * 100
        ).round(1).astype(str) + "%"
        channel_summary["平均コスト"] = channel_summary["平均コスト"].round(0).astype(int)
        channel_summary["最小コスト"] = channel_summary["最小コスト"].astype(int)
        channel_summary["最大コスト"] = channel_summary["最大コスト"].astype(int)
        st.dataframe(channel_summary, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("選考フェーズ別 応募者数（ファネル）")
        chart_path = CHARTS_DIR / "bar_phase_funnel.png"
        if chart_path.exists():
            st.image(str(chart_path), use_container_width=True)
        else:
            st.warning("グラフファイルが見つかりません。visualize.py を実行してください。")

        # ファネルテーブル
        funnel_rows = []
        for phase in PHASES:
            count = (df_filtered["phase"] == phase).sum()
            rate = count / total_applicants * 100 if total_applicants > 0 else 0
            funnel_rows.append({
                "フェーズ": phase,
                "応募者数": f"{count:,} 名",
                "全体比": f"{rate:.1f}%",
            })
        st.dataframe(pd.DataFrame(funnel_rows), use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("職種別 採用状況")
        jobtype_summary = (
            df_filtered.groupby("job_type")
            .agg(
                応募数=("apply_no", "count"),
                採用数=("is_hired", "sum"),
                平均コスト=("cost", "mean"),
            )
            .reset_index()
            .rename(columns={"job_type": "職種"})
        )
        jobtype_summary["採用率"] = (
            jobtype_summary["採用数"] / jobtype_summary["応募数"] * 100
        ).round(1).astype(str) + "%"
        jobtype_summary["平均コスト"] = jobtype_summary["平均コスト"].round(0).astype(int)
        st.dataframe(jobtype_summary, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------------
    # 高コスト採用テーブル
    # -------------------------------------------------------------------
    st.subheader("高コスト採用テーブル（上位20件）")
    if "cost" in df_filtered.columns:
        high_cost_df = (
            df_filtered[df_filtered["is_hired"] == 1]
            .nlargest(20, "cost")[
                ["apply_date", "apply_no", "channel", "job_type", "cost", "phase", "offer_acceptance"]
            ]
            .rename(columns={
                "apply_date":       "応募日",
                "apply_no":         "応募番号",
                "channel":          "チャネル",
                "job_type":         "職種",
                "cost":             "採用コスト(円)",
                "phase":            "到達フェーズ",
                "offer_acceptance": "内定承諾",
            })
        )
        if high_cost_df.empty:
            st.info("採用者がいません。")
        else:
            st.dataframe(high_cost_df, use_container_width=True, hide_index=True)
    else:
        st.info("コストデータが見つかりません。")

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
