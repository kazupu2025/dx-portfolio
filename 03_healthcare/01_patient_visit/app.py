import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="医療 来院ダッシュボード",
    page_icon="🏥",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
WAIT_ALERT     = config.get("wait_alert_minutes", 60)
PEAK_THRESHOLD = config.get("peak_hour_threshold", 1.3)


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_visit_202401.csv", encoding="utf-8-sig")
    for col in ["wait_minutes", "hour_slot"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "is_long_wait" in df.columns:
        df["is_long_wait"] = df["is_long_wait"].astype(bool)
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all     = load_data()
report_text = load_report()

st.title("🏥 医療 来院ダッシュボード")
st.caption("2024年1月 | 5診療科")

depts    = sorted(df_all["department"].dropna().unique().tolist())
selected = st.multiselect("診療科フィルター", depts, default=depts)
df       = df_all[df_all["department"].isin(selected)] if selected else df_all

total_visits  = len(df)
avg_wait      = df["wait_minutes"].mean() if "wait_minutes" in df.columns else 0
total_long    = int(df["is_long_wait"].sum()) if "is_long_wait" in df.columns else 0
long_rate     = total_long / total_visits * 100 if total_visits > 0 else 0
hour_counts   = df.groupby("hour_slot").size().reindex(range(9, 18), fill_value=0)
avg_hourly    = hour_counts.mean()
peak_hours    = hour_counts[hour_counts > avg_hourly * PEAK_THRESHOLD].index.tolist()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("月次総来院数",   f"{total_visits:,}件")
c2.metric("平均待ち時間",   f"{avg_wait:.1f}分",
          delta="⚠ 長い" if avg_wait > WAIT_ALERT else "正常範囲",
          delta_color="inverse" if avg_wait > WAIT_ALERT else "normal")
c3.metric("長時間待ち件数", f"{total_long}件",
          delta=f"{long_rate:.1f}%",
          delta_color="inverse" if long_rate > 10 else "normal")
c4.metric("ピーク時間帯数", f"{len(peak_hours)}時間帯")
c5.metric("対象診療科数",   f"{df['department'].nunique()}科")

st.divider()

tab1, tab2, tab3 = st.tabs(["⏰ 時間帯別来院", "🏢 診療科別", "🗺️ 曜日×時間ヒートマップ"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_hourly_visits.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"赤棒 = ピーク時間帯（平均×{PEAK_THRESHOLD}倍超）")
    else:
        st.warning("グラフなし")

with tab2:
    p = charts_dir / "bar_dept_visits.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"青棒=来院数、赤線=平均待ち時間、橙破線=アラートライン（{WAIT_ALERT}分）")
    else:
        st.warning("グラフなし")

with tab3:
    p = charts_dir / "heatmap_weekday_hour.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption("色が濃いほど来院数が多い。受付体制を最適化するための配置計画に活用")
    else:
        st.warning("グラフなし")

st.divider()

st.subheader("診療科別 来院サマリー")
dept_tbl = df.groupby("department").agg(
    来院数=("patient_id", "count"),
    平均待ち時間=("wait_minutes", "mean"),
    長時間待ち件数=("is_long_wait", "sum"),
).round(1).sort_values("来院数", ascending=False)
dept_tbl["アラート"] = dept_tbl["平均待ち時間"].apply(
    lambda x: "⚠ 要改善" if x > WAIT_ALERT else "✅ 正常"
)
dept_tbl["平均待ち時間"] = dept_tbl["平均待ち時間"].apply(lambda x: f"{x:.1f}分")
st.dataframe(dept_tbl, use_container_width=True)

st.divider()

with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
