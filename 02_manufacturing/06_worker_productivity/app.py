# -*- coding: utf-8 -*-
"""
B-79: 製造 作業員生産性・稼働率分析ダッシュボード
Streamlit ダッシュボード
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_worker_202401.csv"
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"


@st.cache_data
def load_mfg_worker_productivity_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    for col in ["productivity", "defect_rate", "overtime_hours", "production_qty", "work_hours"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("🔧 B-79 製造 作業員生産性・稼働率分析ダッシュボード")
st.caption("B-79 | 製造 × 人事・生産管理 | 作業員別生産性・不良率・OJT優先候補 | 2024年1月")

df_all = load_mfg_worker_productivity_data()

if df_all.empty:
    st.error(f"データが見つかりません: {CSV_PATH}")
    st.info("先にパイプラインを実行してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    line_col = "line" if "line" in df_all.columns else None
    if line_col:
        lines = sorted(df_all[line_col].dropna().unique().tolist())
        selected_lines = st.multiselect("製造ラインを選択", lines, default=lines, key="b79_line_filter")
    else:
        selected_lines = []

df = df_all[df_all[line_col].isin(selected_lines)].copy() if selected_lines and line_col else df_all.copy()

# KPI
col1, col2, col3, col4 = st.columns(4)
n_workers = df["worker_id"].nunique() if "worker_id" in df.columns else len(df)
avg_prod = df["productivity"].mean() if "productivity" in df.columns else None
avg_defect = df["defect_rate"].mean() if "defect_rate" in df.columns else None
total_ot = df["overtime_hours"].sum() if "overtime_hours" in df.columns else None

col1.metric("総作業員数", f"{n_workers}名")
col2.metric("平均生産性", f"{avg_prod:.2f} 個/時" if avg_prod is not None and pd.notna(avg_prod) else "N/A")
col3.metric("平均不良率", f"{avg_defect*100:.2f}%" if avg_defect is not None and pd.notna(avg_defect) else "N/A")
col4.metric("総残業時間", f"{total_ot:.1f}h" if total_ot is not None and pd.notna(total_ot) else "N/A")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 生産性ランキング", "⚠️ ライン別不良率", "🎯 OJT優先候補"])

with tab1:
    st.subheader("作業員別 平均生産性（上位20名）")
    if "worker_id" in df.columns and "productivity" in df.columns:
        worker_prod = df.groupby("worker_id")["productivity"].mean().sort_values(ascending=False).head(20)
        st.bar_chart(worker_prod)

    st.subheader("作業員別集計テーブル")
    _agg = {}
    if "productivity" in df.columns:
        _agg["平均生産性"] = ("productivity", "mean")
    if "defect_rate" in df.columns:
        _agg["平均不良率"] = ("defect_rate", "mean")
    if "production_qty" in df.columns:
        _agg["総生産数"] = ("production_qty", "sum")
    if "overtime_hours" in df.columns:
        _agg["総残業時間"] = ("overtime_hours", "sum")

    if _agg and "worker_id" in df.columns:
        worker_tbl = df.groupby("worker_id", as_index=False).agg(**_agg).sort_values("平均生産性", ascending=False)
        worker_tbl["平均生産性"] = worker_tbl["平均生産性"].round(2)
        if "平均不良率" in worker_tbl.columns:
            worker_tbl["平均不良率"] = (worker_tbl["平均不良率"] * 100).round(2)
        st.dataframe(worker_tbl, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("ライン別 平均不良率")
    if line_col and "defect_rate" in df.columns:
        line_defect = df.groupby(line_col)["defect_rate"].mean().mul(100).sort_values(ascending=False)
        st.bar_chart(line_defect)

    st.subheader("ライン別 平均生産性")
    if line_col and "productivity" in df.columns:
        line_prod = df.groupby(line_col)["productivity"].mean().sort_values(ascending=True)
        st.bar_chart(line_prod)

with tab3:
    st.subheader("OJT優先候補（低生産性 × 高不良率）")
    if "worker_id" in df.columns and "productivity" in df.columns and "defect_rate" in df.columns:
        _agg2 = {"avg_productivity": ("productivity", "mean"), "avg_defect_rate": ("defect_rate", "mean")}
        if "overtime_hours" in df.columns:
            _agg2["total_overtime"] = ("overtime_hours", "sum")
        worker_agg = df.groupby("worker_id", as_index=False).agg(**_agg2)
        prod_median = worker_agg["avg_productivity"].median()
        defect_median = worker_agg["avg_defect_rate"].median()
        ojt = worker_agg[
            (worker_agg["avg_productivity"] < prod_median) &
            (worker_agg["avg_defect_rate"] > defect_median)
        ].sort_values("avg_defect_rate", ascending=False)
        ojt_display = ojt.rename(columns={
            "worker_id": "作業員ID",
            "avg_productivity": "平均生産性(個/時)",
            "avg_defect_rate": "平均不良率(%)",
            "total_overtime": "総残業時間(h)",
        })
        if "平均生産性(個/時)" in ojt_display.columns:
            ojt_display["平均生産性(個/時)"] = ojt_display["平均生産性(個/時)"].round(2)
        if "平均不良率(%)" in ojt_display.columns:
            ojt_display["平均不良率(%)"] = (ojt_display["平均不良率(%)"] * 100).round(2)
        if len(ojt_display) > 0:
            st.warning(f"OJT優先候補: {len(ojt_display)}名")
            st.dataframe(ojt_display, use_container_width=True, hide_index=True)
        else:
            st.success("OJT優先候補なし")

st.divider()
if REPORT_PATH.exists():
    with st.expander("📄 分析レポートを表示", expanded=False):
        st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
else:
    st.info("analyze.py を実行するとレポートが表示されます。")
