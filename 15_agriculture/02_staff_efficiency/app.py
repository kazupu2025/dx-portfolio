# -*- coding: utf-8 -*-
"""
B-74: 農業 農場スタッフ勤怠・作業効率分析ダッシュボード
Streamlit ダッシュボード
"""
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CLEANED_FILE = BASE_DIR / "output" / "cleaned_farm_work_202401.csv"


@st.cache_data
def load_agriculture_staff_efficiency_data() -> pd.DataFrame:
    if not CLEANED_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(str(CLEANED_FILE), encoding="utf-8-sig")
    if "work_date" in df.columns:
        df["work_date"] = pd.to_datetime(
            df["work_date"].astype(str).str.replace("/", "-"),
            format="%Y-%m-%d", errors="coerce",
        )
    for col in ["work_hours", "target_qty", "actual_qty",
                "achievement_rate", "productivity", "is_target_met"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("🌾 B-74 農業 農場スタッフ勤怠・作業効率分析ダッシュボード")
st.caption("B-74 | 2024年1月 | 作物・作業区分別生産性・目標達成率")

df_all = load_agriculture_staff_efficiency_data()

if df_all.empty:
    st.error(f"データファイルが見つかりません: {CLEANED_FILE}")
    st.info("先にパイプラインを実行してください。")
    st.stop()

# サイドバー
with st.sidebar:
    st.header("🔍 フィルター")
    work_types = sorted(df_all["work_type"].dropna().unique().tolist()) if "work_type" in df_all.columns else []
    selected_work_types = st.multiselect("作業区分選択", work_types, default=work_types,
                                         key="b74_worktype_filter")
    crops = sorted(df_all["crop"].dropna().unique().tolist()) if "crop" in df_all.columns else []
    selected_crops = st.multiselect("作物選択", crops, default=crops, key="b74_crop_filter")

mask = pd.Series([True] * len(df_all), index=df_all.index)
if selected_work_types and "work_type" in df_all.columns:
    mask &= df_all["work_type"].isin(selected_work_types)
if selected_crops and "crop" in df_all.columns:
    mask &= df_all["crop"].isin(selected_crops)
df = df_all[mask].copy()

tab1, tab2, tab3 = st.tabs(["📊 KPIサマリー", "🌱 作物・作業区分分析", "📋 作業明細データ"])

with tab1:
    st.subheader("KPIサマリー")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総記録数", len(df))
    met_rate = df["is_target_met"].mean() if "is_target_met" in df.columns and len(df) > 0 else None
    col2.metric("目標達成率", f"{met_rate:.1%}" if met_rate is not None and pd.notna(met_rate) else "N/A")
    avg_prod = df["productivity"].mean() if "productivity" in df.columns and len(df) > 0 else None
    col3.metric("平均生産性(単位/時間)",
                f"{avg_prod:.2f}" if avg_prod is not None and pd.notna(avg_prod) else "N/A")
    avg_hours = df["work_hours"].mean() if "work_hours" in df.columns and len(df) > 0 else None
    col4.metric("平均作業時間(時間)",
                f"{avg_hours:.2f}" if avg_hours is not None and pd.notna(avg_hours) else "N/A")

    if "efficiency_grade" in df.columns:
        st.divider()
        grade_counts = df["efficiency_grade"].value_counts().reindex(
            ["高効率", "中効率", "低効率"], fill_value=0)
        col5, col6, col7 = st.columns(3)
        col5.metric("高効率件数", int(grade_counts.get("高効率", 0)))
        col6.metric("中効率件数", int(grade_counts.get("中効率", 0)))
        col7.metric("低効率件数", int(grade_counts.get("低効率", 0)))

        st.subheader("効率グレード分布")
        grade_ser = df["efficiency_grade"].value_counts().sort_values(ascending=True)
        st.bar_chart(grade_ser)

with tab2:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("作物別 目標達成率")
        if "crop" in df.columns and "achievement_rate" in df.columns:
            crop_ach = df.groupby("crop")["achievement_rate"].mean().sort_values(ascending=True)
            st.bar_chart(crop_ach)
    with col_r:
        st.subheader("作業区分別 平均生産性")
        if "work_type" in df.columns and "productivity" in df.columns:
            wt_prod = df.groupby("work_type")["productivity"].mean().sort_values(ascending=True)
            st.bar_chart(wt_prod)

    st.subheader("作物別 平均作業時間")
    if "crop" in df.columns and "work_hours" in df.columns:
        crop_hours = df.groupby("crop")["work_hours"].mean().sort_values(ascending=True)
        st.bar_chart(crop_hours)

with tab3:
    st.subheader("作業明細データ")
    display_cols = ["work_date", "record_id", "staff_id", "work_type", "crop",
                    "work_hours", "target_qty", "actual_qty", "is_target_met",
                    "achievement_rate", "productivity", "efficiency_grade"]
    show_cols = [c for c in display_cols if c in df.columns]
    disp = df[show_cols].copy()
    if "work_date" in disp.columns:
        disp["work_date"] = disp["work_date"].dt.strftime("%Y-%m-%d")
    st.caption(f"表示件数: {len(disp):,} 件")
    st.dataframe(disp, use_container_width=True, hide_index=True)
