# -*- coding: utf-8 -*-
"""
B-70: 建設 資材コスト・発注管理ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "sample_material.csv"

# config.yml の安全な読み込み
try:
    import yaml
    _cfg_path = BASE_DIR / "config.yml"
    if _cfg_path.exists():
        with open(_cfg_path, encoding="utf-8") as _f:
            _CONFIG = yaml.safe_load(_f) or {}
    else:
        _CONFIG = {}
except Exception:
    _CONFIG = {}

THRESHOLD_GOOD = _CONFIG.get("cost_variance_threshold_good", 0.10) * 100
THRESHOLD_WARNING = _CONFIG.get("cost_variance_threshold_warning", 0.20) * 100


@st.cache_data
def load_construction_material_cost_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(str(CSV_PATH))
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    for col in ["total_cost", "unit_price", "quantity"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("📊 B-70 建設 資材コスト・発注管理ダッシュボード")
st.caption("B-70 | カテゴリ別・プロジェクト別・仕入先別コスト分析")

df = load_construction_material_cost_data()

if df.empty:
    st.error(f"データファイルが見つかりません: {CSV_PATH}")
    st.stop()

# ── サマリー統計 ────────────────────────────────
total_cost = df["total_cost"].sum() if "total_cost" in df.columns else 0
item_count = len(df)

# 月次変動率で判定
_monthly_cost = df.groupby("year_month")["total_cost"].sum().sort_index()
_variance = _monthly_cost.pct_change().abs().dropna() * 100
max_var = _variance.max() if len(_variance) > 0 else 0
verdict = "good" if max_var <= THRESHOLD_GOOD else ("warning" if max_var <= THRESHOLD_WARNING else "alert")
verdict_emoji = {"good": "✅ GOOD", "warning": "⚠️ WARNING", "alert": "🔴 ALERT"}

if "category" in df.columns and "total_cost" in df.columns:
    cat_totals = df.groupby("category")["total_cost"].sum()
    top_cat = cat_totals.idxmax() if not cat_totals.empty else "—"
    top_cat_cost = cat_totals.max() if not cat_totals.empty else 0
else:
    top_cat, top_cat_cost = "—", 0

# KPI
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 総発注額", f"¥{total_cost:,.0f}")
col2.metric("📦 品目数", f"{item_count}件")
col3.metric("🏆 最多カテゴリ", top_cat, delta=f"¥{top_cat_cost:,.0f}")
col4.metric("📈 変動判定", verdict_emoji.get(verdict, verdict))

st.divider()

# サイドバー: フィルター
with st.sidebar:
    st.header("🔍 フィルター")
    if "category" in df.columns:
        cats = sorted(df["category"].dropna().unique().tolist())
        sel_cats = st.multiselect("カテゴリ", cats, default=cats, key="b70_category_filter")
    else:
        sel_cats = []
    if "project_id" in df.columns:
        projs = sorted(df["project_id"].dropna().unique().tolist())
        sel_projs = st.multiselect("プロジェクト", projs, default=projs, key="b70_project_filter")
    else:
        sel_projs = []
    if "supplier" in df.columns:
        supps = sorted(df["supplier"].dropna().unique().tolist())
        sel_supps = st.multiselect("仕入先", supps, default=supps, key="b70_supplier_filter")
    else:
        sel_supps = []

# フィルタリング
mask = pd.Series([True] * len(df), index=df.index)
if sel_cats and "category" in df.columns:
    mask &= df["category"].isin(sel_cats)
if sel_projs and "project_id" in df.columns:
    mask &= df["project_id"].isin(sel_projs)
if sel_supps and "supplier" in df.columns:
    mask &= df["supplier"].isin(sel_supps)
df_f = df[mask].copy()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 カテゴリ分析", "📅 月次推移", "🏢 プロジェクト別", "🏭 仕入先別", "📋 資材一覧"])

with tab1:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("カテゴリ別 コスト")
        if "category" in df_f.columns and "total_cost" in df_f.columns:
            cat_cost = df_f.groupby("category")["total_cost"].sum().sort_values(ascending=True)
            st.bar_chart(cat_cost)
    with col_r:
        st.subheader("カテゴリ別 統計")
        if "category" in df_f.columns:
            cat_tbl = df_f.groupby("category", as_index=False).agg(
                総コスト=("total_cost", "sum"),
                品目数=("total_cost", "count"),
            )
            cat_tbl["総コスト"] = cat_tbl["総コスト"].apply(lambda x: f"¥{x:,.0f}")
            st.dataframe(cat_tbl, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("月次コスト推移")
    if "year_month" in df_f.columns and "total_cost" in df_f.columns:
        monthly = df_f.groupby("year_month")["total_cost"].sum().sort_index()
        st.line_chart(monthly)

    st.subheader("月次変動率テーブル")
    if not monthly.empty:
        m_df = monthly.reset_index()
        m_df.columns = ["年月", "月次コスト(円)"]
        m_df["変動率(%)"] = (m_df["月次コスト(円)"].pct_change() * 100).round(1)
        m_df["月次コスト(円)"] = m_df["月次コスト(円)"].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(m_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("プロジェクト別 発注額")
    if "project_id" in df_f.columns and "total_cost" in df_f.columns:
        proj_cost = df_f.groupby("project_id")["total_cost"].sum().sort_values(ascending=True)
        st.bar_chart(proj_cost)
        proj_tbl = proj_cost.reset_index()
        proj_tbl.columns = ["プロジェクトID", "総コスト(円)"]
        proj_tbl["総コスト(円)"] = proj_tbl["総コスト(円)"].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(proj_tbl, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("仕入先別 発注額")
    if "supplier" in df_f.columns and "total_cost" in df_f.columns:
        supp_cost = df_f.groupby("supplier")["total_cost"].sum().sort_values(ascending=True)
        st.bar_chart(supp_cost)
        supp_tbl = supp_cost.reset_index()
        supp_tbl.columns = ["仕入先", "総発注額(円)"]
        supp_tbl["総発注額(円)"] = supp_tbl["総発注額(円)"].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(supp_tbl, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("資材発注一覧")
    _want = ["date", "material_name", "category", "project_id",
             "quantity", "unit", "unit_price", "total_cost", "supplier"]
    _avail = [c for c in _want if c in df_f.columns]
    disp = df_f[_avail].copy()
    if "date" in disp.columns:
        disp["date"] = disp["date"].dt.strftime("%Y-%m-%d")
    for col in ["unit_price", "total_cost"]:
        if col in disp.columns:
            disp[col] = disp[col].apply(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "N/A")
    disp = disp.sort_values("date", ascending=False) if "date" in disp.columns else disp
    st.dataframe(disp, use_container_width=True, hide_index=True)
    st.caption(f"表示件数: {len(disp)} / {len(df)} 件")

st.divider()
st.caption("B-70 建設 資材コスト・発注管理 | DX ポートフォリオ")
