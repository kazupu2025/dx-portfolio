# -*- coding: utf-8 -*-
"""
B-62: 農業 収穫量・品質トレンド分析ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# config.yml（存在しない場合はデフォルト値を使用）
try:
    import yaml
    _cfg_path = BASE_DIR / "config.yml"
    with open(_cfg_path, encoding="utf-8") as _f:
        _config = yaml.safe_load(_f)
except Exception:
    _config = {}

GRADE_A_GOOD = _config.get("grade_a_threshold_good", 75)
GRADE_A_WARNING = _config.get("grade_a_threshold_warning", 60)


@st.cache_data
def load_agri_harvest_sample() -> pd.DataFrame:
    path = BASE_DIR / "sample_harvest_quality.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8")


def analyze_data(df: pd.DataFrame) -> dict:
    df = df.copy()
    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"], errors="coerce")
    if "yield_kg" in df.columns and "field_area_ha" in df.columns:
        df["yield_per_ha"] = df["yield_kg"] / df["field_area_ha"].replace(0, np.nan)
    else:
        df["yield_per_ha"] = np.nan

    agg_spec = {}
    if "yield_kg" in df.columns:
        agg_spec["total_yield"] = ("yield_kg", "sum")
    if "yield_per_ha" in df.columns:
        agg_spec["avg_yield_per_ha"] = ("yield_per_ha", "mean")
    if "grade_a_rate" in df.columns:
        agg_spec["avg_grade_a"] = ("grade_a_rate", "mean")
    if "avg_brix" in df.columns:
        agg_spec["avg_brix"] = ("avg_brix", "mean")
    if "field_area_ha" in df.columns:
        agg_spec["area"] = ("field_area_ha", "mean")

    crop_df = (
        df.groupby("crop").agg(**agg_spec).reset_index().sort_values(
            "avg_yield_per_ha" if "avg_yield_per_ha" in agg_spec else list(agg_spec.keys())[0],
            ascending=False
        )
    ) if "crop" in df.columns and agg_spec else pd.DataFrame()

    m_agg = {}
    if "yield_kg" in df.columns:
        m_agg["total_yield"] = ("yield_kg", "sum")
    if "grade_a_rate" in df.columns:
        m_agg["avg_grade_a"] = ("grade_a_rate", "mean")
    if "avg_brix" in df.columns:
        m_agg["avg_brix"] = ("avg_brix", "mean")
    monthly_df = (
        df.groupby("month").agg(**m_agg).reset_index()
    ) if "month" in df.columns and m_agg else pd.DataFrame()

    total_yield = float(df["yield_kg"].sum()) if "yield_kg" in df.columns else 0
    avg_grade_a = float(df["grade_a_rate"].mean()) if "grade_a_rate" in df.columns else 0
    avg_brix = float(df["avg_brix"].mean()) if "avg_brix" in df.columns else 0
    verdict = "good" if avg_grade_a >= GRADE_A_GOOD else ("warning" if avg_grade_a >= GRADE_A_WARNING else "alert")

    return {
        "df": df, "crop_df": crop_df, "monthly_df": monthly_df,
        "total_yield": total_yield, "avg_grade_a": avg_grade_a,
        "avg_brix": avg_brix, "verdict": verdict,
    }


st.title("🌾 B-62 農業 収穫量・品質トレンド分析ダッシュボード")
st.caption("品目別収穫量・A品率・糖度の分析")

with st.sidebar:
    st.header("📊 データ読み込み")
    data_source = st.radio("データ源の選択", ["サンプルデータ", "CSVアップロード"])
    uploaded_file = None
    if data_source == "CSVアップロード":
        uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if data_source == "サンプルデータ" or uploaded_file is None:
    df_raw = load_agri_harvest_sample()
else:
    try:
        df_raw = pd.read_csv(uploaded_file, encoding="utf-8")
    except Exception:
        df_raw = pd.DataFrame()

if df_raw.empty:
    st.error("データファイルが見つかりません。sample_harvest_quality.csv を確認してください。")
    st.stop()

with st.sidebar:
    if "crop" in df_raw.columns:
        crops = sorted(df_raw["crop"].dropna().unique().tolist())
        selected_crops = st.multiselect("品目フィルター", crops, default=crops)
    else:
        selected_crops = []

if selected_crops and "crop" in df_raw.columns:
    df_filtered = df_raw[df_raw["crop"].isin(selected_crops)]
else:
    df_filtered = df_raw.copy()

result = analyze_data(df_filtered)
crop_df = result["crop_df"]
monthly_df = result["monthly_df"]

# KPI
st.subheader("📈 KPI サマリー")
col1, col2, col3, col4 = st.columns(4)
col1.metric("総収穫量 (kg)", f"{result['total_yield']:,.0f}")
col2.metric("A品率 (%)", f"{result['avg_grade_a']:.1f}%",
            delta=f"状態: {result['verdict'].upper()}")
col3.metric("平均糖度 (Brix)", f"{result['avg_brix']:.1f}")
verdict_emoji = "✓" if result["verdict"] == "good" else "⚠" if result["verdict"] == "warning" else "✗"
col4.metric("品質判定", f"{verdict_emoji} {result['verdict'].upper()}")

# 月次収穫量トレンド
st.subheader("📅 月次収穫量トレンド")
if not monthly_df.empty and "month" in monthly_df.columns and "total_yield" in monthly_df.columns:
    _m = monthly_df.copy()
    _m["month"] = _m["month"].dt.strftime("%Y-%m") if hasattr(_m["month"], "dt") else _m["month"].astype(str)
    st.line_chart(_m.set_index("month")["total_yield"])

# 品目別A品率
st.subheader("📊 品目別 A品率")
if not crop_df.empty and "crop" in crop_df.columns and "avg_grade_a" in crop_df.columns:
    st.bar_chart(crop_df.set_index("crop")["avg_grade_a"])
    st.caption(f"Good判定閾値: {GRADE_A_GOOD}% / Warning判定閾値: {GRADE_A_WARNING}%")

# 等級構成
st.subheader("📦 等級構成 (A/B/C品)")
grade_cols = [c for c in ["grade_a_rate", "grade_b_rate", "grade_c_rate"] if c in result["df"].columns]
if "crop" in result["df"].columns and grade_cols:
    grade_dist = result["df"].groupby("crop")[grade_cols].mean().rename(
        columns={"grade_a_rate": "A品", "grade_b_rate": "B品", "grade_c_rate": "C品"}
    )
    st.bar_chart(grade_dist)

# 詳細データ
st.subheader("📋 品目別詳細データ")
if not crop_df.empty:
    _rename = {
        "crop": "品目", "total_yield": "総収穫量 (kg)",
        "avg_yield_per_ha": "単位面積当たり収穫量 (kg/ha)",
        "avg_grade_a": "A品率 (%)", "avg_brix": "平均糖度 (Brix)", "area": "平均作付面積 (ha)",
    }
    _avail = {k: v for k, v in _rename.items() if k in crop_df.columns}
    st.dataframe(crop_df.rename(columns=_avail), use_container_width=True)
