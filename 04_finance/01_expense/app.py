"""経費精算ダッシュボード — Plotly 動的チャート版"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from pathlib import Path

BASE = Path(__file__).parent
with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
BUDGET_ALERT = config.get("budget_alert_threshold", 1.0)


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "output" / "cleaned_expense_202401.csv", encoding="utf-8-sig")
    for col in ["amount", "budget"]:
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

st.title("💴 経費精算ダッシュボード")
st.caption("2024年1月 | 5部門 | サンプルデータ")

depts = sorted(df_all["department"].dropna().unique().tolist())
selected = st.multiselect("部門フィルター", depts, default=depts)
df = df_all[df_all["department"].isin(selected)] if selected else df_all

total_amount = df["amount"].sum()
total_budget = df["budget"].sum()
budget_ratio = total_amount / total_budget * 100 if total_budget > 0 else 0
dept_totals  = df.groupby("department")["amount"].sum()
dept_budgets = df.groupby("department")["budget"].sum()
over_depts   = sum(1 for d in dept_totals.index
                   if dept_totals[d] > dept_budgets.get(d, 0) * BUDGET_ALERT)
alert_pct = BUDGET_ALERT * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総経費", f"¥{total_amount:,.0f}")
c2.metric("予算消化率", f"{budget_ratio:.1f}%",
          delta="⚠ 超過" if budget_ratio > alert_pct else "正常",
          delta_color="inverse" if budget_ratio > alert_pct else "normal")
c3.metric("予算超過部門数", f"{over_depts} 部門",
          delta="要確認" if over_depts > 0 else "正常",
          delta_color="inverse" if over_depts > 0 else "normal")
c4.metric("対象部門数", f"{df['department'].nunique()} 部門")
c5.metric("経費申請件数", f"{len(df):,} 件")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 部門別経費", "💡 費目別経費", "📈 予算 vs 実績"])

with tab1:
    dept_exp = (
        df.groupby("department")["amount"].sum().reset_index()
        .rename(columns={"department": "部門", "amount": "経費(円)"})
        .sort_values("経費(円)", ascending=False)
    )
    fig = px.bar(dept_exp, x="部門", y="経費(円)", title="部門別 経費合計（2024年1月）",
                 text="経費(円)", color_discrete_sequence=["#3b82f6"])
    fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if "expense_type" in df.columns:
        type_exp = (
            df.groupby("expense_type")["amount"].sum().reset_index()
            .rename(columns={"expense_type": "費目", "amount": "経費(円)"})
            .sort_values("経費(円)", ascending=False)
        )
        fig2 = px.bar(type_exp, x="費目", y="経費(円)", title="費目別 経費合計（2024年1月）",
                      text="経費(円)", color_discrete_sequence=["#8b5cf6"])
        fig2.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("費目データがありません")

with tab3:
    bva = df.groupby("department").agg(
        実績=("amount", "sum"), 予算=("budget", "sum")
    ).reset_index()
    bva["消化率(%)"] = (bva["実績"] / bva["予算"] * 100).round(1)
    bva["状態"] = bva["消化率(%)"].apply(lambda x: "超過" if x > alert_pct else "予算内")

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="実績", x=bva["department"], y=bva["実績"],
                          marker_color=["#ef4444" if s == "超過" else "#3b82f6" for s in bva["状態"]]))
    fig3.add_trace(go.Bar(name="予算", x=bva["department"], y=bva["予算"],
                          marker_color="#94a3b8", opacity=0.6))
    fig3.update_layout(barmode="group", title="部門別 予算 vs 実績（2024年1月）",
                       xaxis_title="部門", yaxis_title="金額（円）")
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(f"赤棒 = 予算超過（{alert_pct:.0f}%超）")

st.divider()

st.subheader("部門別経費サマリー")
dept_tbl = df.groupby("department").agg(
    経費合計=("amount", "sum"), 予算合計=("budget", "sum"), 件数=("amount", "count"),
).copy()
dept_tbl["予算消化率(%)"] = (dept_tbl["経費合計"] / dept_tbl["予算合計"].replace(0, 1) * 100).round(1)
dept_tbl["アラート"] = dept_tbl["予算消化率(%)"].apply(
    lambda x: "⚠ 超過" if x > alert_pct else "✅ 正常"
)
dept_tbl["経費合計"] = dept_tbl["経費合計"].apply(lambda x: f"¥{x:,.0f}")
dept_tbl["予算合計"] = dept_tbl["予算合計"].apply(lambda x: f"¥{x:,.0f}")
st.dataframe(dept_tbl.sort_values("予算消化率(%)", ascending=False), use_container_width=True)

st.divider()
with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
