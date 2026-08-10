"""医療 来院ダッシュボード — Plotly 動的チャート版"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from pathlib import Path

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


df_all = load_data()
report_text = load_report()

st.title("🏥 医療 来院ダッシュボード")
st.caption("2024年1月 | 5診療科 | サンプルデータ")

depts = sorted(df_all["department"].dropna().unique().tolist())
selected = st.multiselect("診療科フィルター", depts, default=depts)
df = df_all[df_all["department"].isin(selected)] if selected else df_all

total_visits = len(df)
avg_wait     = df["wait_minutes"].mean() if "wait_minutes" in df.columns else 0
total_long   = int(df["is_long_wait"].sum()) if "is_long_wait" in df.columns else 0
long_rate    = total_long / total_visits * 100 if total_visits > 0 else 0
hour_counts  = df.groupby("hour_slot").size().reindex(range(9, 18), fill_value=0)
avg_hourly   = hour_counts.mean()
peak_hours   = hour_counts[hour_counts > avg_hourly * PEAK_THRESHOLD].index.tolist()

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

with tab1:
    hour_df = df.groupby("hour_slot").size().reset_index(name="来院数")
    hour_df["状態"] = hour_df["来院数"].apply(
        lambda x: "ピーク" if x > hour_df["来院数"].mean() * PEAK_THRESHOLD else "通常"
    )
    fig = px.bar(hour_df, x="hour_slot", y="来院数",
                 color="状態", color_discrete_map={"ピーク": "#ef4444", "通常": "#3b82f6"},
                 title="時間帯別 来院数（2024年1月）", text="来院数")
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_title="時間帯（時）", showlegend=False)
    fig.add_hline(y=hour_df["来院数"].mean() * PEAK_THRESHOLD, line_dash="dash",
                  line_color="orange", annotation_text=f"ピーク閾値（平均×{PEAK_THRESHOLD}倍）")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    dept_summary = df.groupby("department").agg(
        来院数=("patient_id", "count"),
        平均待ち時間=("wait_minutes", "mean"),
    ).reset_index().round(1)
    dept_summary["アラート"] = dept_summary["平均待ち時間"].apply(
        lambda x: "要改善" if x > WAIT_ALERT else "正常"
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=dept_summary["department"], y=dept_summary["来院数"],
        name="来院数", marker_color="#3b82f6", yaxis="y1",
    ))
    fig2.add_trace(go.Scatter(
        x=dept_summary["department"], y=dept_summary["平均待ち時間"],
        name="平均待ち時間(分)", mode="lines+markers",
        marker=dict(color="#ef4444"), yaxis="y2",
    ))
    fig2.update_layout(
        title="診療科別 来院数 & 平均待ち時間（2024年1月）",
        yaxis=dict(title="来院数"),
        yaxis2=dict(title="平均待ち時間（分）", overlaying="y", side="right"),
        legend=dict(x=0.01, y=0.99),
    )
    fig2.add_hline(y=WAIT_ALERT, line_dash="dash", line_color="orange",
                   annotation_text=f"待ちアラートライン（{WAIT_ALERT}分）",
                   yref="y2")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    if "weekday" in df.columns:
        heat = df.groupby(["weekday", "hour_slot"]).size().reset_index(name="来院数")
        weekday_order = ["月", "火", "水", "木", "金", "土", "日"]
        existing = [w for w in weekday_order if w in heat["weekday"].values]
        heat_pivot = heat.pivot(index="weekday", columns="hour_slot", values="来院数").fillna(0)
        heat_pivot = heat_pivot.reindex([w for w in existing])
        fig3 = px.imshow(heat_pivot, title="曜日×時間帯 来院数ヒートマップ",
                         color_continuous_scale="Blues", text_auto=True, aspect="auto")
        fig3.update_layout(xaxis_title="時間帯（時）", yaxis_title="曜日")
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("色が濃いほど来院数が多い。受付体制の最適化に活用")
    else:
        st.info("曜日データがありません")

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
