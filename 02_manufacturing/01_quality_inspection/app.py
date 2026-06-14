import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="製造 品質検査ダッシュボード",
    page_icon="🔍",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
DEFECT_ALERT = config.get("defect_rate_alert_threshold", 0.05)
SIGMA = config.get("sigma_threshold", 3.0)


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_inspection_202401.csv", encoding="utf-8-sig")
    for col in ["inspection_value", "lower_limit", "upper_limit"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "is_defect" in df.columns:
        df["is_defect"] = df["is_defect"].astype(bool)
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("🔍 製造 品質検査ダッシュボード")
st.caption("2024年1月 | 5工程")

procs = sorted(df_all["process"].dropna().unique().tolist())
selected = st.multiselect("工程フィルター", procs, default=procs)
df = df_all[df_all["process"].isin(selected)] if selected else df_all

total = len(df)
total_defects = int(df["is_defect"].sum())
overall_rate = total_defects / total * 100 if total > 0 else 0
alert_procs = df.groupby("process")["is_defect"].mean()
alert_count = (alert_procs > DEFECT_ALERT).sum()
total_procs = df["process"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総検査件数", f"{total:,}件")
c2.metric("全体不良率", f"{overall_rate:.2f}%",
          delta="⚠ 要対応" if overall_rate > DEFECT_ALERT * 100 else "正常範囲",
          delta_color="inverse" if overall_rate > DEFECT_ALERT * 100 else "normal")
c3.metric("不良件数", f"{total_defects:,}件")
c4.metric("⚠ アラート工程数", f"{alert_count}工程",
          delta="要対応" if alert_count > 0 else "問題なし",
          delta_color="inverse" if alert_count > 0 else "normal")
c5.metric("対象工程数", f"{total_procs}工程")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 工程別不良率", "📅 日次トレンド", "🗺️ ヒートマップ"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_process_defect_rate.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

with tab2:
    p = charts_dir / "line_daily_defect_trend.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"赤破線 = アラートライン（{DEFECT_ALERT*100:.0f}%）、赤塗り = アラート超過期間")
    else:
        st.warning("グラフなし")

with tab3:
    p = charts_dir / "heatmap_process_product.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption("色が濃いほど不良率が高い。製品コードと工程の組み合わせで問題箇所を特定")
    else:
        st.warning("グラフなし")

st.divider()

st.subheader("工程別不良率サマリー")
proc_tbl = df.groupby("process").agg(
    検査件数=("is_defect", "count"),
    不良件数=("is_defect", "sum"),
).copy()
proc_tbl["不良率(%)"] = (proc_tbl["不良件数"] / proc_tbl["検査件数"] * 100).round(2)
proc_tbl["アラート"] = proc_tbl["不良率(%)"].apply(
    lambda x: "⚠ 要対応" if x > DEFECT_ALERT * 100 else "✅ 正常"
)
proc_tbl = proc_tbl.sort_values("不良率(%)", ascending=False)
st.dataframe(proc_tbl, use_container_width=True)

st.divider()

st.subheader("不良品一覧（最新50件）")
defect_df = df[df["is_defect"]].sort_values("date", ascending=False).head(50)
if len(defect_df) > 0:
    show_cols = [c for c in ["date", "product_code", "product_name", "process",
                              "inspection_value", "lower_limit", "upper_limit", "inspector", "result"]
                 if c in defect_df.columns]
    display = defect_df[show_cols].copy()
    if "date" in display.columns:
        display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display, use_container_width=True)
else:
    st.success("不良品データなし")

st.divider()

with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
