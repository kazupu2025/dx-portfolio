"""品質検査データ異常値検出レポート — Plotly 動的チャート版"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from pathlib import Path

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
DEFECT_ALERT = config.get("defect_rate_alert_threshold", 0.05)


@st.cache_data
def load_data():
    df = pd.read_csv(
        BASE / "output" / "cleaned_inspection_202401.csv", encoding="utf-8-sig"
    )
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

# ── ヘッダー ─────────────────────────────────────────────────
st.title("🔬 品質検査 異常値検出ダッシュボード")
st.caption("2024年1月 | 製造5工程 | サンプルデータ")

# ── 工程フィルター ────────────────────────────────────────────
procs = sorted(df_all["process"].dropna().unique().tolist())
selected = st.multiselect("工程フィルター", procs, default=procs)
df = df_all[df_all["process"].isin(selected)] if selected else df_all

# ── KPI ──────────────────────────────────────────────────────
total = len(df)
total_defects = int(df["is_defect"].sum())
overall_rate = total_defects / total * 100 if total > 0 else 0
alert_procs = df.groupby("process")["is_defect"].mean()
alert_count = int((alert_procs > DEFECT_ALERT).sum())
total_procs = df["process"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総検査件数", f"{total:,}件")
c2.metric(
    "全体不良率", f"{overall_rate:.2f}%",
    delta="⚠ 要対応" if overall_rate > DEFECT_ALERT * 100 else "正常範囲",
    delta_color="inverse" if overall_rate > DEFECT_ALERT * 100 else "normal",
)
c3.metric("不良件数", f"{total_defects:,}件")
c4.metric(
    "⚠ アラート工程数", f"{alert_count}工程",
    delta="要対応" if alert_count > 0 else "問題なし",
    delta_color="inverse" if alert_count > 0 else "normal",
)
c5.metric("対象工程数", f"{total_procs}工程")

st.divider()

# ── グラフ 3タブ（フィルター連動） ───────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 工程別不良率", "📅 日次トレンド", "🗺️ ヒートマップ"])

alert_pct = DEFECT_ALERT * 100

with tab1:
    proc_rate = (
        df.groupby("process")["is_defect"]
        .mean().mul(100).reset_index()
        .rename(columns={"process": "工程", "is_defect": "不良率(%)"})
        .sort_values("不良率(%)", ascending=False)
    )
    proc_rate["状態"] = proc_rate["不良率(%)"].apply(
        lambda x: "アラート超過" if x > alert_pct else "正常"
    )
    fig = px.bar(
        proc_rate, x="工程", y="不良率(%)",
        color="状態",
        color_discrete_map={"アラート超過": "#ef4444", "正常": "#3b82f6"},
        title="工程別 不良率（2024年1月）",
        text="不良率(%)",
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.add_hline(
        y=alert_pct, line_dash="dash", line_color="orange",
        annotation_text=f"アラートライン ({alert_pct:.0f}%)",
        annotation_position="top right",
    )
    fig.update_layout(showlegend=False, yaxis_title="不良率 (%)")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    daily = (
        df.groupby("date")
        .agg(検査件数=("is_defect", "count"), 不良件数=("is_defect", "sum"))
        .reset_index()
    )
    daily["不良率(%)"] = (daily["不良件数"] / daily["検査件数"] * 100).round(2)

    fig2 = px.line(
        daily, x="date", y="不良率(%)",
        title="日次 不良率トレンド（2024年1月）",
        markers=True, line_shape="linear",
    )
    fig2.add_hline(
        y=alert_pct, line_dash="dash", line_color="orange",
        annotation_text=f"アラートライン ({alert_pct:.0f}%)",
        annotation_position="bottom right",
    )
    alert_days = daily[daily["不良率(%)"] > alert_pct]
    if not alert_days.empty:
        fig2.add_trace(go.Scatter(
            x=alert_days["date"], y=alert_days["不良率(%)"],
            mode="markers", marker=dict(color="red", size=9, symbol="circle"),
            name="アラート超過日",
        ))
    fig2.update_layout(xaxis_title="日付", yaxis_title="不良率 (%)")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    heat = (
        df.groupby(["process", "product_name"])["is_defect"]
        .mean().mul(100).reset_index()
        .rename(columns={"process": "工程", "product_name": "製品", "is_defect": "不良率(%)"})
    )
    heat_pivot = (
        heat.pivot(index="工程", columns="製品", values="不良率(%)")
        .fillna(0)
    )
    fig3 = px.imshow(
        heat_pivot,
        title="工程 × 製品 不良率ヒートマップ（%）",
        color_continuous_scale="RdYlGn_r",
        text_auto=".1f",
        aspect="auto",
    )
    fig3.update_layout(xaxis_title="製品", yaxis_title="工程")
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("色が濃いほど不良率が高い。製品×工程の組み合わせで問題箇所を特定")

st.divider()

# ── 工程別サマリーテーブル ─────────────────────────────────────
st.subheader("工程別不良率サマリー")
proc_tbl = df.groupby("process").agg(
    検査件数=("is_defect", "count"),
    不良件数=("is_defect", "sum"),
).copy()
proc_tbl["不良率(%)"] = (proc_tbl["不良件数"] / proc_tbl["検査件数"] * 100).round(2)
proc_tbl["アラート"] = proc_tbl["不良率(%)"].apply(
    lambda x: "⚠ 要対応" if x > alert_pct else "✅ 正常"
)
st.dataframe(
    proc_tbl.sort_values("不良率(%)", ascending=False),
    use_container_width=True,
)

st.divider()

# ── 不良品一覧 ────────────────────────────────────────────────
st.subheader("不良品一覧（最新50件）")
defect_df = df[df["is_defect"]].sort_values("date", ascending=False).head(50)
if len(defect_df) > 0:
    show_cols = [c for c in [
        "date", "product_code", "product_name", "process",
        "inspection_value", "lower_limit", "upper_limit", "inspector", "result",
    ] if c in defect_df.columns]
    display = defect_df[show_cols].copy()
    if "date" in display.columns:
        display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display, use_container_width=True)
else:
    st.success("不良品データなし")

st.divider()

with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
