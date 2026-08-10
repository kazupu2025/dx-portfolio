"""不動産 問い合わせ・成約ダッシュボード — Plotly 動的チャート版"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from pathlib import Path

BASE = Path(__file__).parent
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
CONV_ALERT = config.get("conversion_alert_threshold", 0.10)
STAGES = config.get("stages", ["問い合わせ", "内見", "申し込み", "成約"])


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_inquiry_202401.csv", encoding="utf-8-sig")
    for col in ["is_contracted", "contract_amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data
def load_report():
    p = BASE / "output" / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません"


df_all = load_data()
report_text = load_report()

st.title("🏠 不動産 問い合わせ・成約ダッシュボード")
st.caption("2024年1月 | 5エリア | サンプルデータ")

areas = sorted(df_all["area"].dropna().unique().tolist())
selected = st.multiselect("エリアフィルター", areas, default=areas)
df = df_all[df_all["area"].isin(selected)] if selected else df_all

total = len(df)
total_contracts = int(df["is_contracted"].sum())
overall_conv    = total_contracts / total * 100 if total > 0 else 0
total_revenue   = df["contract_amount"].sum()
avg_revenue     = total_revenue / total_contracts if total_contracts > 0 else 0
area_conv       = df.groupby("area").apply(lambda g: g["is_contracted"].mean())
low_conv_areas  = int((area_conv < CONV_ALERT).sum())
alert_pct       = CONV_ALERT * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総問い合わせ数", f"{total}件")
c2.metric("成約件数", f"{total_contracts}件",
          delta=f"成約率 {overall_conv:.1f}%",
          delta_color="normal" if overall_conv >= alert_pct else "inverse")
c3.metric("総成約金額", f"{total_revenue:,.0f}万円")
c4.metric("平均成約金額", f"{avg_revenue:,.0f}万円")
c5.metric("⚠ 低成約エリア", f"{low_conv_areas}エリア",
          delta="要対応" if low_conv_areas > 0 else "問題なし",
          delta_color="inverse" if low_conv_areas > 0 else "normal")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 ファネル分析", "👤 担当者別", "🗺️ エリア別"])

with tab1:
    # status カラムがある場合はステージ別、なければ 問い合わせ→成約 の2段
    if "status" in df.columns:
        stage_counts = df["status"].value_counts().reset_index()
        stage_counts.columns = ["ステージ", "件数"]
        fig = px.funnel(stage_counts, x="件数", y="ステージ",
                        title="商談ファネル（2024年1月）")
    else:
        funnel_data = pd.DataFrame({
            "ステージ": ["問い合わせ", "成約"],
            "件数": [total, total_contracts],
        })
        fig = px.funnel(funnel_data, x="件数", y="ステージ",
                        title="問い合わせ → 成約 ファネル（2024年1月）")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if "agent" in df.columns:
        agent_df = df.groupby("agent").agg(
            問い合わせ数=("inquiry_id", "count"),
            成約数=("is_contracted", "sum"),
        ).reset_index()
        agent_df["成約率(%)"] = (agent_df["成約数"] / agent_df["問い合わせ数"] * 100).round(1)
        agent_df["状態"] = agent_df["成約率(%)"].apply(
            lambda x: "要改善" if x < alert_pct else "正常"
        )
        fig2 = px.bar(agent_df, x="agent", y="成約率(%)",
                      color="状態", color_discrete_map={"要改善": "#ef4444", "正常": "#3b82f6"},
                      title="担当者別 成約率（2024年1月）", text="成約率(%)")
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig2.add_hline(y=alert_pct, line_dash="dash", line_color="orange",
                       annotation_text=f"アラートライン ({alert_pct:.0f}%)")
        fig2.update_layout(showlegend=False, xaxis_title="担当者")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("担当者データがありません")

with tab3:
    area_summary = df.groupby("area").agg(
        問い合わせ数=("inquiry_id", "count"),
        成約数=("is_contracted", "sum"),
    ).reset_index()
    area_summary["成約率(%)"] = (area_summary["成約数"] / area_summary["問い合わせ数"] * 100).round(1)
    area_summary["状態"] = area_summary["成約率(%)"].apply(
        lambda x: "低成約率" if x < alert_pct else "正常"
    )
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=area_summary["area"], y=area_summary["問い合わせ数"],
        name="問い合わせ数", marker_color="#93c5fd", yaxis="y1",
    ))
    fig3.add_trace(go.Scatter(
        x=area_summary["area"], y=area_summary["成約率(%)"],
        name="成約率(%)", mode="lines+markers",
        marker=dict(color="#ef4444"), yaxis="y2",
    ))
    fig3.update_layout(
        title="エリア別 問い合わせ数 & 成約率（2024年1月）",
        yaxis=dict(title="問い合わせ数"),
        yaxis2=dict(title="成約率（%）", overlaying="y", side="right"),
    )
    fig3.add_hline(y=alert_pct, line_dash="dash", line_color="orange",
                   annotation_text=f"アラートライン ({alert_pct:.0f}%)", yref="y2")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

st.subheader("エリア別 成約サマリー")
area_tbl = df.groupby("area").agg(
    問い合わせ数=("inquiry_id", "count"),
    成約数=("is_contracted", "sum"),
    成約金額合計=("contract_amount", "sum"),
).copy()
area_tbl["成約率(%)"] = (area_tbl["成約数"] / area_tbl["問い合わせ数"] * 100).round(1)
area_tbl["アラート"] = area_tbl["成約率(%)"].apply(
    lambda x: "⚠ 低成約率" if x < alert_pct else "✅ 正常"
)
area_tbl["成約金額合計"] = area_tbl["成約金額合計"].apply(lambda x: f"{x:,.0f}万円")
st.dataframe(area_tbl.sort_values("成約率(%)", ascending=False), use_container_width=True)

st.divider()
with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
