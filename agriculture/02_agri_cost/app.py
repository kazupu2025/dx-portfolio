# -*- coding: utf-8 -*-
"""
B-63: 農業 農薬・肥料コスト分析ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    import yaml
    with open(BASE_DIR / "config.yml", encoding="utf-8") as _f:
        _config = yaml.safe_load(_f)
except Exception:
    _config = {}

COST_GOOD = _config.get("cost_per_ha_good", 50000)
COST_WARNING = _config.get("cost_per_ha_warning", 80000)


@st.cache_data
def load_agri_cost_sample() -> pd.DataFrame:
    path = BASE_DIR / "sample_agri_cost.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8")


def analyze_data(df: pd.DataFrame) -> dict:
    df = df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "total_cost" in df.columns and "field_area_ha" in df.columns:
        df["cost_per_ha"] = df["total_cost"] / df["field_area_ha"].replace(0, np.nan)
    else:
        df["cost_per_ha"] = np.nan

    cat_agg = {}
    if "total_cost" in df.columns:
        cat_agg["total_cost"] = ("total_cost", "sum")
        if "product_name" in df.columns:
            cat_agg["count"] = ("product_name", "count")
    if "unit_price" in df.columns:
        cat_agg["avg_unit_price"] = ("unit_price", "mean")
    category_df = (
        df.groupby("category").agg(**cat_agg).reset_index().sort_values("total_cost", ascending=False)
    ) if "category" in df.columns and cat_agg else pd.DataFrame()

    crop_agg = {}
    if "total_cost" in df.columns:
        crop_agg["total_cost"] = ("total_cost", "sum")
    if "cost_per_ha" in df.columns:
        crop_agg["avg_cost_per_ha"] = ("cost_per_ha", "mean")
    if "category" in df.columns:
        crop_agg["category_count"] = ("category", "nunique")
    if "field_area_ha" in df.columns:
        crop_agg["field_area_ha"] = ("field_area_ha", "mean")
    crop_df = (
        df.groupby("crop").agg(**crop_agg).reset_index().sort_values(
            "avg_cost_per_ha" if "avg_cost_per_ha" in crop_agg else "total_cost", ascending=False
        )
    ) if "crop" in df.columns and crop_agg else pd.DataFrame()

    m_agg = {}
    if "total_cost" in df.columns:
        m_agg["total_cost"] = ("total_cost", "sum")
    if "cost_per_ha" in df.columns:
        m_agg["avg_cost_per_ha"] = ("cost_per_ha", "mean")
    monthly_df = (
        df.groupby("date").agg(**m_agg).reset_index()
    ) if "date" in df.columns and m_agg else pd.DataFrame()

    total_cost = float(df["total_cost"].sum()) if "total_cost" in df.columns else 0
    cost_per_ha = float(df["cost_per_ha"].mean()) if "cost_per_ha" in df.columns else 0
    category_count = int(df["category"].nunique()) if "category" in df.columns else 0
    verdict = "good" if cost_per_ha <= COST_GOOD else ("warning" if cost_per_ha <= COST_WARNING else "alert")

    return {
        "df": df, "category_df": category_df, "crop_df": crop_df, "monthly_df": monthly_df,
        "total_cost": total_cost, "cost_per_ha": cost_per_ha,
        "category_count": category_count, "verdict": verdict,
    }


st.title("🌿 B-63 農業 農薬・肥料コスト分析ダッシュボード")
st.caption("品目別・カテゴリ別コスト集計と月次トレンド分析")

with st.sidebar:
    st.header("📊 データ読み込み")
    data_source = st.radio("データ源の選択", ["サンプルデータ", "CSVアップロード"])
    uploaded_file = None
    if data_source == "CSVアップロード":
        uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if data_source == "サンプルデータ" or uploaded_file is None:
    df_raw = load_agri_cost_sample()
else:
    try:
        df_raw = pd.read_csv(uploaded_file, encoding="utf-8")
    except Exception:
        df_raw = pd.DataFrame()

if df_raw.empty:
    st.error("データファイルが見つかりません。sample_agri_cost.csv を確認してください。")
    st.stop()

with st.sidebar:
    if "crop" in df_raw.columns:
        crops = sorted(df_raw["crop"].dropna().unique().tolist())
        selected_crops = st.multiselect("品目フィルター", crops, default=crops)
    else:
        selected_crops = []

df_filtered = df_raw[df_raw["crop"].isin(selected_crops)] if selected_crops and "crop" in df_raw.columns else df_raw.copy()
result = analyze_data(df_filtered)
category_df = result["category_df"]
crop_df = result["crop_df"]
monthly_df = result["monthly_df"]

# KPI
st.subheader("📈 KPI サマリー")
col1, col2, col3, col4 = st.columns(4)
col1.metric("総コスト (円)", f"{result['total_cost']:,.0f}")
col2.metric("ha当たりコスト (円)", f"{result['cost_per_ha']:,.0f}",
            delta=f"状態: {result['verdict'].upper()}")
col3.metric("利用カテゴリ数", result["category_count"])
verdict_emoji = "✓" if result["verdict"] == "good" else "⚠" if result["verdict"] == "warning" else "✗"
col4.metric("コスト判定", f"{verdict_emoji} {result['verdict'].upper()}")

st.caption(f"Good: ha当たりコスト ≤{COST_GOOD:,.0f}円 / Warning: ≤{COST_WARNING:,.0f}円")

# カテゴリ別コスト
st.subheader("📊 カテゴリ別コスト")
if not category_df.empty and "category" in category_df.columns and "total_cost" in category_df.columns:
    st.bar_chart(category_df.set_index("category")["total_cost"])

# 作物別コスト
col1, col2 = st.columns(2)
with col1:
    st.subheader("🌾 作物別 総コスト")
    if not crop_df.empty and "crop" in crop_df.columns and "total_cost" in crop_df.columns:
        st.bar_chart(crop_df.set_index("crop")["total_cost"])
with col2:
    st.subheader("📌 作物別 ha当たりコスト")
    if not crop_df.empty and "crop" in crop_df.columns and "avg_cost_per_ha" in crop_df.columns:
        st.bar_chart(crop_df.set_index("crop")["avg_cost_per_ha"])

# 月次コスト推移
st.subheader("📅 月次コスト推移")
if not monthly_df.empty and "date" in monthly_df.columns and "total_cost" in monthly_df.columns:
    _m = monthly_df.copy()
    _m["date"] = _m["date"].dt.strftime("%Y-%m") if hasattr(_m["date"], "dt") else _m["date"].astype(str)
    _chart_cols = [c for c in ["total_cost", "avg_cost_per_ha"] if c in _m.columns]
    st.line_chart(_m.set_index("date")[_chart_cols])

# 詳細テーブル
st.subheader("📋 作物別詳細データ")
if not crop_df.empty:
    _rename = {
        "crop": "作物", "total_cost": "総コスト (円)", "avg_cost_per_ha": "ha当たりコスト (円)",
        "category_count": "利用カテゴリ数", "field_area_ha": "平均作付面積 (ha)",
    }
    st.dataframe(crop_df.rename(columns={k: v for k, v in _rename.items() if k in crop_df.columns}),
                 use_container_width=True)

st.subheader("📋 カテゴリ別詳細データ")
if not category_df.empty:
    _rename2 = {
        "category": "カテゴリ", "total_cost": "総コスト (円)",
        "count": "使用回数", "avg_unit_price": "平均単価 (円/kg)",
    }
    st.dataframe(category_df.rename(columns={k: v for k, v in _rename2.items() if k in category_df.columns}),
                 use_container_width=True)
