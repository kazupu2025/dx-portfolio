# -*- coding: utf-8 -*-
"""
B-80: 製造 品質管理ポータル 総合品質KPIダッシュボード
Streamlit ダッシュボード（portal.py の統合版）
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


@st.cache_data
def load_mfg_quality_portal_defect_rate() -> pd.DataFrame:
    p = BASE_DIR / "sample_defect_rate.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["defect_rate", "total_inspected", "defect_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_mfg_quality_portal_claim() -> pd.DataFrame:
    p = BASE_DIR / "sample_claim.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["claim_count", "severity_score", "loss_amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_mfg_quality_portal_yield() -> pd.DataFrame:
    p = BASE_DIR / "sample_yield.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["yield_rate", "total_input", "good_output"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_mfg_quality_portal_inspector() -> pd.DataFrame:
    p = BASE_DIR / "sample_inspector.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["inspection_count", "defect_found", "detection_rate"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_mfg_quality_portal_lot() -> pd.DataFrame:
    p = BASE_DIR / "sample_lot.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, encoding="utf-8-sig")
    for col in ["lot_size", "defect_count", "pass_rate"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("🏭 B-80 製造 品質管理ポータル 総合品質KPIダッシュボード")
st.caption("B-80 | 製造 × 品質保証 | 月次不良率・クレーム・歩留まり・検査員・ロット合否 | 統合品質ポータル")

df_defect = load_mfg_quality_portal_defect_rate()
df_claim = load_mfg_quality_portal_claim()
df_yield = load_mfg_quality_portal_yield()
df_inspector = load_mfg_quality_portal_inspector()
df_lot = load_mfg_quality_portal_lot()

# 総合 KPI サマリー
st.subheader("📊 総合品質KPIサマリー")
c1, c2, c3, c4, c5 = st.columns(5)

avg_defect = df_defect["defect_rate"].mean() if not df_defect.empty and "defect_rate" in df_defect.columns else None
c1.metric("平均不良率", f"{avg_defect*100:.2f}%" if avg_defect is not None and pd.notna(avg_defect) else "N/A")

total_claims = int(df_claim["claim_count"].sum()) if not df_claim.empty and "claim_count" in df_claim.columns else "N/A"
c2.metric("クレーム件数合計", f"{total_claims:,}" if isinstance(total_claims, int) else total_claims)

avg_yield = df_yield["yield_rate"].mean() if not df_yield.empty and "yield_rate" in df_yield.columns else None
c3.metric("平均歩留まり率", f"{avg_yield*100:.1f}%" if avg_yield is not None and pd.notna(avg_yield) else "N/A")

n_inspectors = df_inspector["inspector_id"].nunique() if not df_inspector.empty and "inspector_id" in df_inspector.columns else (len(df_inspector) if not df_inspector.empty else 0)
c4.metric("検査員数", f"{n_inspectors}名")

pass_rate = df_lot["pass_rate"].mean() if not df_lot.empty and "pass_rate" in df_lot.columns else None
c5.metric("ロット合格率", f"{pass_rate*100:.1f}%" if pass_rate is not None and pd.notna(pass_rate) else "N/A")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📉 月次不良率",
    "📋 クレーム集計",
    "📈 歩留まりトレンド",
    "👤 検査員別実績",
    "🗂️ ロット合否判定",
])

with tab1:
    st.subheader("月次不良率推移")
    if not df_defect.empty:
        date_col = next((c for c in ["month", "date", "ym", "period"] if c in df_defect.columns), None)
        rate_col = "defect_rate" if "defect_rate" in df_defect.columns else None
        if date_col and rate_col:
            trend = df_defect.groupby(date_col)[rate_col].mean().mul(100)
            st.line_chart(trend)
        grp_col = next((c for c in ["process", "product", "line", "category"] if c in df_defect.columns), None)
        if grp_col and rate_col:
            st.subheader(f"{grp_col}別 平均不良率")
            grp_defect = df_defect.groupby(grp_col)[rate_col].mean().mul(100).sort_values(ascending=False)
            st.bar_chart(grp_defect)
        st.dataframe(df_defect, use_container_width=True, hide_index=True)
    else:
        st.info("sample_defect_rate.csv が見つかりません。")

with tab2:
    st.subheader("クレーム集計")
    if not df_claim.empty:
        grp_col = next((c for c in ["customer", "product", "category", "claim_type"] if c in df_claim.columns), None)
        if grp_col and "claim_count" in df_claim.columns:
            grp_claim = df_claim.groupby(grp_col)["claim_count"].sum().sort_values(ascending=False)
            st.bar_chart(grp_claim)
        st.dataframe(df_claim, use_container_width=True, hide_index=True)
    else:
        st.info("sample_claim.csv が見つかりません。")

with tab3:
    st.subheader("歩留まりトレンド")
    if not df_yield.empty:
        date_col = next((c for c in ["month", "date", "ym", "period"] if c in df_yield.columns), None)
        rate_col = "yield_rate" if "yield_rate" in df_yield.columns else None
        if date_col and rate_col:
            yield_trend = df_yield.groupby(date_col)[rate_col].mean().mul(100)
            st.line_chart(yield_trend)
        grp_col = next((c for c in ["process", "product", "line"] if c in df_yield.columns), None)
        if grp_col and rate_col:
            st.subheader(f"{grp_col}別 平均歩留まり率")
            grp_yield = df_yield.groupby(grp_col)[rate_col].mean().mul(100).sort_values(ascending=True)
            st.bar_chart(grp_yield)
        st.dataframe(df_yield, use_container_width=True, hide_index=True)
    else:
        st.info("sample_yield.csv が見つかりません。")

with tab4:
    st.subheader("検査員別実績")
    if not df_inspector.empty:
        id_col = next((c for c in ["inspector_id", "inspector", "name"] if c in df_inspector.columns), None)
        if id_col and "inspection_count" in df_inspector.columns:
            insp_count = df_inspector.set_index(id_col)["inspection_count"].sort_values(ascending=True)
            st.bar_chart(insp_count)
        if id_col and "detection_rate" in df_inspector.columns:
            st.subheader("検査員別 不良検出率")
            det_rate = df_inspector.set_index(id_col)["detection_rate"].mul(100).sort_values(ascending=False)
            st.bar_chart(det_rate)
        st.dataframe(df_inspector, use_container_width=True, hide_index=True)
    else:
        st.info("sample_inspector.csv が見つかりません。")

with tab5:
    st.subheader("ロット別合否判定")
    if not df_lot.empty:
        verdict_col = next((c for c in ["verdict", "result", "pass_fail", "judgment"] if c in df_lot.columns), None)
        if verdict_col:
            verdict_counts = df_lot[verdict_col].value_counts()
            st.bar_chart(verdict_counts)
        if "pass_rate" in df_lot.columns:
            product_col = next((c for c in ["product", "product_name", "item"] if c in df_lot.columns), None)
            if product_col:
                prod_pass = df_lot.groupby(product_col)["pass_rate"].mean().mul(100).sort_values(ascending=True)
                st.subheader("製品別 平均ロット合格率")
                st.bar_chart(prod_pass)
        st.dataframe(df_lot, use_container_width=True, hide_index=True)
    else:
        st.info("sample_lot.csv が見つかりません。")
