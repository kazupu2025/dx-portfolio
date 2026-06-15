import streamlit as st
import pandas as pd
import yaml
from pathlib import Path

st.set_page_config(
    page_title="不動産 問い合わせ・成約ダッシュボード",
    page_icon="🏠",
    layout="wide",
)

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
st.caption("2024年1月 | 5エリア")

areas = sorted(df_all["area"].dropna().unique().tolist())
selected = st.multiselect("エリアフィルター", areas, default=areas)
df = df_all[df_all["area"].isin(selected)] if selected else df_all

total = len(df)
total_contracts = int(df["is_contracted"].sum())
overall_conv = total_contracts / total * 100 if total > 0 else 0
total_revenue = df["contract_amount"].sum()
avg_revenue = total_revenue / total_contracts if total_contracts > 0 else 0
low_conv_areas = df.groupby("area").apply(
    lambda g: g["is_contracted"].mean()
).lt(CONV_ALERT).sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総問い合わせ数", f"{total}件")
c2.metric("成約件数",       f"{total_contracts}件",
          delta=f"成約率 {overall_conv:.1f}%",
          delta_color="normal" if overall_conv >= CONV_ALERT * 100 else "inverse")
c3.metric("総成約金額",     f"{total_revenue:,.0f}万円")
c4.metric("平均成約金額",   f"{avg_revenue:,.0f}万円")
c5.metric("⚠ 低成約エリア", f"{low_conv_areas}エリア",
          delta="要対応" if low_conv_areas > 0 else "問題なし",
          delta_color="inverse" if low_conv_areas > 0 else "normal")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 ファネル分析", "👤 担当者別", "🗺️ エリア別"])
charts_dir = BASE / "output" / "charts"

with tab1:
    p = charts_dir / "bar_funnel.png"
    st.image(str(p), use_container_width=True) if p.exists() else st.warning("グラフなし")

with tab2:
    p = charts_dir / "bar_agent_conversion.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption(f"赤棒 = 成約率{CONV_ALERT*100:.0f}%未満（アラート）")
    else:
        st.warning("グラフなし")

with tab3:
    p = charts_dir / "bar_area_inquiry.png"
    if p.exists():
        st.image(str(p), use_container_width=True)
        st.caption("青棒=問い合わせ数、赤線=成約率、橙破線=アラートライン")
    else:
        st.warning("グラフなし")

st.divider()

st.subheader("エリア別 成約サマリー")
area_tbl = df.groupby("area").agg(
    問い合わせ数=("inquiry_id", "count"),
    成約数=("is_contracted", "sum"),
    成約金額合計=("contract_amount", "sum"),
).copy()
area_tbl["成約率(%)"] = (area_tbl["成約数"] / area_tbl["問い合わせ数"] * 100).round(1)
area_tbl["アラート"] = area_tbl["成約率(%)"].apply(
    lambda x: "⚠ 低成約率" if x < CONV_ALERT * 100 else "✅ 正常"
)
area_tbl = area_tbl.sort_values("成約率(%)", ascending=False)
area_tbl["成約金額合計"] = area_tbl["成約金額合計"].apply(lambda x: f"{x:,.0f}万円")
st.dataframe(area_tbl, use_container_width=True)

st.divider()

with st.expander("📋 分析レポートを見る", expanded=False):
    st.markdown(report_text)
