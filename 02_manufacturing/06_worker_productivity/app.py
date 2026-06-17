"""Streamlit ダッシュボード - 製造 作業員生産性"""
import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_worker_202401.csv"
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"
CHARTS_DIR = BASE_DIR / "output" / "charts"

st.set_page_config(page_title="製造 作業員生産性ダッシュボード", layout="wide")
st.title("🔧 製造 作業員生産性ダッシュボード")

if not CSV_PATH.exists():
    st.error("データが見つかりません。パイプラインを実行してください。")
    st.stop()

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# ── フィルター ──
lines = sorted(df["line"].unique())
selected_lines = st.multiselect("製造ラインを選択", lines, default=lines)
df_filtered = df[df["line"].isin(selected_lines)] if selected_lines else df.copy()

# ── KPI 4つ ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("総作業員数", f"{df_filtered['worker_id'].nunique()}名")
with col2:
    avg_prod = df_filtered["productivity"].mean()
    st.metric("平均生産性", f"{avg_prod:.2f} 個/時")
with col3:
    avg_defect = df_filtered["defect_rate"].mean()
    st.metric("平均不良率", f"{avg_defect*100:.2f}%")
with col4:
    total_overtime = df_filtered["overtime_hours"].sum()
    st.metric("総残業時間", f"{total_overtime:.1f}h")

st.divider()

# ── 3タブ ──
tab1, tab2, tab3 = st.tabs(["生産性ランキング", "ライン別不良率", "生産性-不良率散布図"])

with tab1:
    st.subheader("作業員別生産性ランキング（上位10名）")
    chart_path = CHARTS_DIR / "bar_worker_productivity_top10.png"
    if chart_path.exists():
        st.image(str(chart_path))
    else:
        st.info("グラフを生成するには visualize.py を実行してください。")
    st.subheader("作業員別集計テーブル")
    worker_tbl = df_filtered.groupby("worker_id").agg(
        平均生産性=("productivity", "mean"),
        平均不良率=("defect_rate", "mean"),
        総生産数=("production_qty", "sum"),
        総残業時間=("overtime_hours", "sum"),
    ).reset_index().sort_values("平均生産性", ascending=False)
    worker_tbl["平均生産性"] = worker_tbl["平均生産性"].round(2)
    worker_tbl["平均不良率"] = (worker_tbl["平均不良率"] * 100).round(2)
    st.dataframe(worker_tbl, use_container_width=True)

with tab2:
    st.subheader("ライン別不良率")
    chart_path = CHARTS_DIR / "bar_line_defect_rate.png"
    if chart_path.exists():
        st.image(str(chart_path))
    else:
        st.info("グラフを生成するには visualize.py を実行してください。")
    st.subheader("ライン別集計テーブル")
    line_tbl = df_filtered.groupby("line").agg(
        平均生産性=("productivity", "mean"),
        平均不良率=("defect_rate", "mean"),
        総生産数=("production_qty", "sum"),
        レコード数=("work_date", "count"),
    ).reset_index()
    line_tbl["平均不良率"] = (line_tbl["平均不良率"] * 100).round(2)
    st.dataframe(line_tbl, use_container_width=True)

with tab3:
    st.subheader("生産性 vs 不良率 散布図（工程別）")
    chart_path = CHARTS_DIR / "scatter_productivity_defect.png"
    if chart_path.exists():
        st.image(str(chart_path))
    else:
        st.info("グラフを生成するには visualize.py を実行してください。")

st.divider()

# ── OJT候補テーブル ──
st.subheader("OJT優先候補（低生産性×高不良率）")
worker_agg = df_filtered.groupby("worker_id").agg(
    avg_productivity=("productivity", "mean"),
    avg_defect_rate=("defect_rate", "mean"),
    total_overtime=("overtime_hours", "sum"),
).reset_index()
prod_median = worker_agg["avg_productivity"].median()
defect_median = worker_agg["avg_defect_rate"].median()
ojt = worker_agg[
    (worker_agg["avg_productivity"] < prod_median) &
    (worker_agg["avg_defect_rate"] > defect_median)
].sort_values("avg_defect_rate", ascending=False)
ojt_display = ojt.rename(columns={
    "worker_id": "作業員ID",
    "avg_productivity": "平均生産性(個/時)",
    "avg_defect_rate": "平均不良率",
    "total_overtime": "総残業時間(h)",
})
ojt_display["平均生産性(個/時)"] = ojt_display["平均生産性(個/時)"].round(2)
ojt_display["平均不良率"] = (ojt_display["平均不良率"] * 100).round(2)
if len(ojt_display) > 0:
    st.dataframe(ojt_display, use_container_width=True)
else:
    st.success("OJT優先候補なし")

st.divider()

# ── 分析レポート expander ──
with st.expander("分析レポートを表示"):
    if REPORT_PATH.exists():
        st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
    else:
        st.info("レポートを生成するには analyze.py を実行してください。")
