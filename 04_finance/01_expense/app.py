import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="金融 経費精算ダッシュボード",
    page_icon="💴",
    layout="wide",
)

BASE = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
BUDGET_ALERT_THRESHOLD = config.get("budget_alert_threshold", 1.0)


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

st.title("💴 金融 経費精算ダッシュボード")
st.caption("2024年1月 | 5部門")

depts = sorted(df_all["department"].dropna().unique().tolist())
selected = st.multiselect("部門フィルター", depts, default=depts)
df = df_all[df_all["department"].isin(selected)] if selected else df_all

total_amount = df["amount"].sum()
total_budget = df["budget"].sum()
budget_ratio = total_amount / total_budget * 100 if total_budget > 0 else 0
dept_totals = df.groupby("department")["amount"].sum()
dept_budgets = df.groupby("department")["budget"].sum()
over_depts = sum(1 for d in dept_totals.index
                 if dept_totals[d] > dept_budgets.get(d, 0) * BUDGET_ALERT_THRESHOLD)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総経費", f"¥{total_amount:,.0f}")
c2.metric("予算消化率", f"{budget_ratio:.1f}%",
          delta="⚠ 超過" if budget_ratio > BUDGET_ALERT_THRESHOLD * 100 else "正常",
          delta_color="inverse" if budget_ratio > BUDGET_ALERT_THRESHOLD * 100 else "normal")
c3.metric("予算超過部門数", f"{over_depts} 部門",
          delta="要確認" if over_depts > 0 else "正常",
          delta_color="inverse" if over_depts > 0 else "normal")
c4.metric("対象部門数", f"{df['department'].nunique()} 部門")
c5.metric("経費申請件数", f"{len(df):,} 件")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 部門別経費", "💡 費目別経費", "📈 予算 vs 実績"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_dept_expense.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

with tab2:
    p = charts_dir / "bar_expense_type.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

with tab3:
    p = charts_dir / "bar_budget_vs_actual.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"赤棒 = 予算超過（閾値: {BUDGET_ALERT_THRESHOLD*100:.0f}%）、緑棒 = 予算内")
    else:
        st.warning("グラフなし")

st.divider()

st.subheader("部門別経費サマリー")
dept_tbl = df.groupby("department").agg(
    経費合計=("amount", "sum"),
    予算合計=("budget", "sum"),
    件数=("amount", "count"),
).copy()
dept_tbl["予算消化率(%)"] = (dept_tbl["経費合計"] / dept_tbl["予算合計"].replace(0, 1) * 100).round(1)
dept_tbl["アラート"] = dept_tbl["予算消化率(%)"].apply(
    lambda x: "⚠ 超過" if x > BUDGET_ALERT_THRESHOLD * 100 else "✅ 正常"
)
dept_tbl["経費合計"] = dept_tbl["経費合計"].apply(lambda x: f"¥{x:,.0f}")
dept_tbl["予算合計"] = dept_tbl["予算合計"].apply(lambda x: f"¥{x:,.0f}")
dept_tbl = dept_tbl.sort_values("予算消化率(%)", ascending=False)
st.dataframe(dept_tbl, use_container_width=True)

st.divider()

with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
