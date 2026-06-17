"""
C-39: 入居者対応履歴・クレーム集計パイプライン
Streamlit ダッシュボード
タイトル: 不動産 入居者クレーム管理ダッシュボード
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_CSV = OUTPUT_DIR / "cleaned_claims_202401.csv"
PROPERTY_CSV = OUTPUT_DIR / "property_summary_202401.csv"
REPORT_MD = OUTPUT_DIR / "analysis_report.md"
JSON_PATH = OUTPUT_DIR / "result_analysis.json"
CHARTS_DIR = OUTPUT_DIR / "charts"

st.set_page_config(
    page_title="不動産 入居者クレーム管理ダッシュボード",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 不動産 入居者クレーム管理ダッシュボード")
st.caption("C-39 | 受付・CS部門向け | 入居者対応履歴・クレーム集計パイプライン")


@st.cache_data
def load_data():
    if not CLEANED_CSV.exists():
        return None
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
    df["receipt_date"] = pd.to_datetime(df["receipt_date"], errors="coerce")
    df["response_days"] = pd.to_numeric(df["response_days"], errors="coerce")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    df["cost_estimate"] = pd.to_numeric(df["cost_estimate"], errors="coerce")
    df["is_resolved"] = pd.to_numeric(df["is_resolved"], errors="coerce")
    return df


@st.cache_data
def load_property_summary():
    if not PROPERTY_CSV.exists():
        return None
    return pd.read_csv(PROPERTY_CSV, encoding="utf-8-sig")


df = load_data()
prop_summary = load_property_summary()

if df is None:
    st.error("クレンジング済みデータが見つかりません。cleanse.py を先に実行してください。")
    st.stop()

# ----- 物件フィルター -----
st.sidebar.header("フィルター")
properties = sorted(df["property_name"].dropna().unique().tolist())
selected_props = st.sidebar.multiselect(
    "物件を選択",
    options=properties,
    default=properties,
)

if selected_props:
    filtered = df[df["property_name"].isin(selected_props)]
else:
    filtered = df.copy()

# ----- KPI 4つ -----
total_claims = len(filtered)
resolved_count = int((filtered["status"] == "解決済").sum())
resolution_rate = resolved_count / total_claims * 100 if total_claims > 0 else 0
avg_days = filtered["response_days"].mean()
unresolved_count = int((filtered["status"] == "未対応").sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("総クレーム数", f"{total_claims:,} 件")
col2.metric("解決率", f"{resolution_rate:.1f} %")
col3.metric("平均対応日数", f"{avg_days:.1f} 日")
col4.metric("未対応件数", f"{unresolved_count:,} 件")

st.divider()

# ----- 3タブ -----
tab1, tab2, tab3 = st.tabs(["物件別状況", "クレーム区分", "対応状況"])

with tab1:
    st.subheader("物件別クレーム状況")
    chart_path = CHARTS_DIR / "bar_property_claims.png"
    if chart_path.exists():
        st.image(str(chart_path))
    if prop_summary is not None:
        show_df = prop_summary[prop_summary["property_name"].isin(selected_props)] if selected_props else prop_summary
        st.dataframe(
            show_df[[
                "property_name", "claim_count", "resolved_count",
                "resolution_rate_pct", "avg_response_days",
                "total_work_hours", "total_cost_estimate"
            ]].rename(columns={
                "property_name": "物件名",
                "claim_count": "件数",
                "resolved_count": "解決件数",
                "resolution_rate_pct": "解決率(%)",
                "avg_response_days": "平均対応日数",
                "total_work_hours": "工数合計(h)",
                "total_cost_estimate": "概算コスト(円)",
            }),
            use_container_width=True,
            hide_index=True,
        )

with tab2:
    st.subheader("クレーム区分別発生件数")
    chart_path = CHARTS_DIR / "bar_claim_type.png"
    if chart_path.exists():
        st.image(str(chart_path))
    ct_counts = (
        filtered.groupby("claim_type")["case_no"]
        .count()
        .reset_index()
        .rename(columns={"case_no": "件数", "claim_type": "クレーム区分"})
        .sort_values("件数", ascending=False)
    )
    st.dataframe(ct_counts, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("対応状況別件数")
    chart_path = CHARTS_DIR / "bar_status_dist.png"
    if chart_path.exists():
        st.image(str(chart_path))
    status_counts = (
        filtered["status"]
        .value_counts()
        .reindex(["解決済", "対応中", "未対応"], fill_value=0)
        .reset_index()
        .rename(columns={"status": "対応状況", "count": "件数"})
    )
    st.dataframe(status_counts, use_container_width=True, hide_index=True)

st.divider()

# ----- 緊急・未対応案件テーブル -----
st.subheader("緊急・未対応案件リスト")
urgent_df = filtered[
    (filtered["urgency"] == "緊急") | (filtered["status"] == "未対応")
].sort_values("response_days", ascending=False)

if urgent_df.empty:
    st.info("対象案件はありません。")
else:
    st.dataframe(
        urgent_df[[
            "case_no", "property_name", "room_no",
            "claim_type", "status", "urgency", "response_days", "receipt_date"
        ]].rename(columns={
            "case_no": "案件番号",
            "property_name": "物件名",
            "room_no": "部屋番号",
            "claim_type": "クレーム区分",
            "status": "対応状況",
            "urgency": "緊急度",
            "response_days": "対応日数",
            "receipt_date": "受付日",
        }).head(50),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ----- 分析レポートExpander -----
with st.expander("分析レポートを表示する"):
    if REPORT_MD.exists():
        st.markdown(REPORT_MD.read_text(encoding="utf-8"))
    else:
        st.warning("analysis_report.md が見つかりません。analyze.py を先に実行してください。")

st.caption("C-39 入居者クレーム管理ダッシュボード | DXポートフォリオ")
