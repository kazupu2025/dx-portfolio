# -*- coding: utf-8 -*-
"""
B-78: 製造 原価差異分析ダッシュボード
Streamlit ダッシュボード
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "output" / "cleaned_production_cost_202401.csv"
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"


@st.cache_data
def load_mfg_cost_variance_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    for col in ["planned_total_cost", "actual_total_cost", "total_variance",
                "planned_material_cost", "actual_material_cost",
                "planned_labor_cost", "actual_labor_cost"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("💴 B-78 製造 原価差異分析ダッシュボード")
st.caption("B-78 | 製造 × 経理・財務 | 製造ライン別計画コスト vs 実績コスト差異分析 | 2024年1月")

df_all = load_mfg_cost_variance_data()

if df_all.empty:
    st.error(f"データが見つかりません: {CSV_PATH}")
    st.info("先にパイプラインを実行してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    id_col = "line_id" if "line_id" in df_all.columns else (df_all.columns[0] if len(df_all.columns) > 0 else None)
    if id_col:
        lines = sorted(df_all[id_col].dropna().unique().tolist())
        selected_lines = st.multiselect("製造ラインを選択", lines, default=lines, key="b78_line_filter")
    else:
        selected_lines = []

df = df_all[df_all[id_col].isin(selected_lines)].copy() if selected_lines and id_col else df_all.copy()

# KPI
col1, col2, col3, col4 = st.columns(4)
planned = df["planned_total_cost"].sum() if "planned_total_cost" in df.columns else 0
actual = df["actual_total_cost"].sum() if "actual_total_cost" in df.columns else 0
var_amt = df["total_variance"].sum() if "total_variance" in df.columns else (actual - planned)
var_pct = (var_amt / planned * 100) if planned != 0 else 0

col1.metric("総計画コスト", f"¥{planned:,.0f}")
col2.metric("総実績コスト", f"¥{actual:,.0f}")
col3.metric("差異額合計", f"¥{var_amt:,.0f}",
            delta=f"{'▲' if var_amt > 0 else '▼'}{abs(var_amt):,.0f}",
            delta_color="inverse" if var_amt > 0 else "normal")
col4.metric("差異率", f"{var_pct:.2f}%",
            delta_color="inverse" if var_pct > 0 else "normal")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 ライン別差異", "📈 費目別分析", "📋 明細データ"])

with tab1:
    st.subheader("ライン別 総差異額")
    if id_col and "total_variance" in df.columns:
        var_by_line = df.groupby(id_col)["total_variance"].sum().sort_values(ascending=True)
        st.bar_chart(var_by_line)

    st.subheader("ライン別 計画 vs 実績コスト")
    if id_col and "planned_total_cost" in df.columns and "actual_total_cost" in df.columns:
        cost_tbl = df.groupby(id_col, as_index=False).agg(
            計画コスト=("planned_total_cost", "sum"),
            実績コスト=("actual_total_cost", "sum"),
        )
        cost_chart = cost_tbl.set_index(id_col)
        st.bar_chart(cost_chart)

with tab2:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("材料費 差異")
        if "planned_material_cost" in df.columns and "actual_material_cost" in df.columns:
            mat_var = (df["actual_material_cost"] - df["planned_material_cost"]).sum()
            st.metric("材料費差異", f"¥{mat_var:,.0f}",
                      delta_color="inverse" if mat_var > 0 else "normal")
            if id_col:
                mat_by_line = (df["actual_material_cost"] - df["planned_material_cost"]).groupby(df[id_col]).sum().sort_values(ascending=True)
                # Pandas groupby with Series
                mat_by_line = df.assign(mat_var=df["actual_material_cost"] - df["planned_material_cost"]).groupby(id_col)["mat_var"].sum().sort_values(ascending=True)
                st.bar_chart(mat_by_line)
    with col_r:
        st.subheader("労務費 差異")
        if "planned_labor_cost" in df.columns and "actual_labor_cost" in df.columns:
            lab_var = (df["actual_labor_cost"] - df["planned_labor_cost"]).sum()
            st.metric("労務費差異", f"¥{lab_var:,.0f}",
                      delta_color="inverse" if lab_var > 0 else "normal")
            if id_col:
                lab_by_line = df.assign(lab_var=df["actual_labor_cost"] - df["planned_labor_cost"]).groupby(id_col)["lab_var"].sum().sort_values(ascending=True)
                st.bar_chart(lab_by_line)

    if "variance_flag" in df.columns:
        st.subheader("差異フラグ別件数")
        flag_counts = df["variance_flag"].value_counts()
        st.bar_chart(flag_counts)

with tab3:
    st.subheader("原価明細データ")
    st.caption(f"表示件数: {len(df):,} 件")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if REPORT_PATH.exists():
        st.divider()
        with st.expander("📄 分析レポートを表示", expanded=False):
            st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
