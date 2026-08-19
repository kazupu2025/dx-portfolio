"""
B-49 飲食 シフト・人件費管理ダッシュボード（Streamlit）
"""

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

CSV_PATH = OUTPUT_DIR / "cleaned_labor_202401.csv"
REPORT_PATH = OUTPUT_DIR / "analysis_report.md"


@st.cache_data
def load_restaurant_labor_data() -> pd.DataFrame:
    """B-49専用ローダー（キャッシュキー衝突防止）"""
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    if "work_date" in df.columns:
        df["work_date"] = pd.to_datetime(df["work_date"])
    return df


st.title("🍽️ B-49 飲食 シフト・人件費管理ダッシュボード")
st.caption("B-49 | 2024年1月 | 飲食チェーン3店舗 | 人件費・労働時間・深夜割増分析")

df = load_restaurant_labor_data()

if df.empty:
    st.error("データが見つかりません。パイプラインを実行してください。")
    st.stop()

# サイドバー: 店舗フィルター
with st.sidebar:
    st.header("🔍 フィルター")
    stores = sorted(df["store_id"].unique().tolist()) if "store_id" in df.columns else []
    selected_stores = st.multiselect("店舗", stores, default=stores)

if selected_stores and "store_id" in df.columns:
    df_filtered = df[df["store_id"].isin(selected_stores)].copy()
else:
    df_filtered = df.copy()

# -------------------------------------------------------------------
# メトリクス
# -------------------------------------------------------------------
total_wage  = df_filtered["total_wage"].sum()        if "total_wage"          in df_filtered.columns else 0
total_hours = df_filtered["work_hours"].sum()        if "work_hours"          in df_filtered.columns else 0
ln_premium  = df_filtered["late_night_premium"].sum() if "late_night_premium" in df_filtered.columns else 0
ot_staff    = df_filtered[df_filtered["overtime_hours"] > 0]["staff_id"].nunique() \
              if "overtime_hours" in df_filtered.columns and "staff_id" in df_filtered.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("総人件費", f"{total_wage:,.0f} 円")
col2.metric("総労働時間", f"{total_hours:,.1f} h")
col3.metric("深夜割増額", f"{ln_premium:,.0f} 円")
col4.metric("残業発生スタッフ数", f"{ot_staff} 名")

st.divider()

# -------------------------------------------------------------------
# グラフ表示
# -------------------------------------------------------------------
st.subheader("グラフ")

chart_files = {
    "店舗別人件費（雇用区分別積み上げ）": CHARTS_DIR / "bar_store_labor_cost.png",
    "労働時間上位10名": CHARTS_DIR / "bar_staff_hours_top10.png",
    "雇用区分別人件費構成比": CHARTS_DIR / "pie_employment_cost_share.png",
}

cols = st.columns(len(chart_files))
for col, (title, path) in zip(cols, chart_files.items()):
    with col:
        st.caption(title)
        if path.exists():
            st.image(str(path), use_container_width=True)
        else:
            st.warning(f"グラフファイルが見つかりません: {path.name}")

st.divider()

# -------------------------------------------------------------------
# 店舗別サマリーテーブル
# -------------------------------------------------------------------
st.subheader("店舗別サマリー")
if "store_id" in df_filtered.columns:
    agg_map = {}
    if "total_wage"          in df_filtered.columns: agg_map["人件費合計"]   = ("total_wage",          "sum")
    if "work_hours"          in df_filtered.columns: agg_map["総労働時間"]   = ("work_hours",          "sum")
    if "staff_id"            in df_filtered.columns: agg_map["スタッフ数"]   = ("staff_id",            "nunique")
    if "late_night_premium"  in df_filtered.columns: agg_map["深夜割増"]     = ("late_night_premium",  "sum")
    if agg_map:
        store_summary = (
            df_filtered.groupby("store_id")
            .agg(**agg_map)
            .round(0)
            .reset_index()
            .rename(columns={"store_id": "店舗"})
        )
        st.dataframe(store_summary, use_container_width=True, hide_index=True)

st.divider()

# -------------------------------------------------------------------
# 雇用区分別サマリーテーブル
# -------------------------------------------------------------------
st.subheader("雇用区分別サマリー")
if "employment_type" in df_filtered.columns:
    emp_agg = {}
    if "total_wage"   in df_filtered.columns: emp_agg["人件費合計"] = ("total_wage",   "sum")
    if "hourly_wage"  in df_filtered.columns: emp_agg["平均時給"]   = ("hourly_wage",  "mean")
    if "work_hours"   in df_filtered.columns: emp_agg["総労働時間"] = ("work_hours",   "sum")
    if emp_agg:
        emp_summary = (
            df_filtered.groupby("employment_type")
            .agg(**emp_agg)
            .round(1)
            .reset_index()
            .rename(columns={"employment_type": "雇用区分"})
        )
        st.dataframe(emp_summary, use_container_width=True, hide_index=True)

st.divider()

# -------------------------------------------------------------------
# 分析レポート
# -------------------------------------------------------------------
if REPORT_PATH.exists():
    with st.expander("📄 分析レポートを表示", expanded=False):
        st.markdown(REPORT_PATH.read_text(encoding="utf-8"))
else:
    st.info("分析レポートが見つかりません。analyze.py を実行してください。")
