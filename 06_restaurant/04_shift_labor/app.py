# -*- coding: utf-8 -*-
"""
C-40: アルバイトシフト管理・人件費集計パイプライン
Streamlit ダッシュボード
"""

import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CLEANED_FILE = OUTPUT_DIR / "cleaned_shift_202401.csv"
REPORT_FILE = OUTPUT_DIR / "analysis_report.md"

st.set_page_config(
    page_title="飲食 シフト・人件費ダッシュボード",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 飲食 シフト・人件費ダッシュボード")
st.caption("C-40 | 2024年1月 アルバイトシフト管理・人件費集計")


# ---- データ読み込み ----
@st.cache_data
def load_data() -> pd.DataFrame:
    if not CLEANED_FILE.exists():
        st.error(f"データファイルが見つかりません: {CLEANED_FILE}")
        st.stop()
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    df["hourly_rate"] = pd.to_numeric(df["hourly_rate"], errors="coerce")
    df["daily_wage"] = pd.to_numeric(df["daily_wage"], errors="coerce")
    df["is_overtime"] = pd.to_numeric(df["is_overtime"], errors="coerce")
    df["work_date"] = pd.to_datetime(df["work_date"], format="%Y-%m-%d", errors="coerce")
    return df


df_all = load_data()

# ---- 店舗フィルター ----
stores = ["全店舗"] + sorted(df_all["store_name"].dropna().unique().tolist())
selected_store = st.sidebar.selectbox("店舗フィルター", stores)

if selected_store == "全店舗":
    df = df_all.copy()
else:
    df = df_all[df_all["store_name"] == selected_store].copy()

# ---- KPI ----
total_labor_cost = df["daily_wage"].sum()
avg_hourly_rate = df["hourly_rate"].mean()
overtime_rate = df["is_overtime"].mean() * 100
total_work_hours = df["work_hours"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("総人件費", f"{total_labor_cost:,.0f} 円")
col2.metric("平均時給", f"{avg_hourly_rate:,.0f} 円")
col3.metric("残業率", f"{overtime_rate:.1f} %")
col4.metric("総労働時間", f"{total_work_hours:,.1f} h")

st.divider()

# ---- タブ ----
tab1, tab2, tab3 = st.tabs(["店舗別人件費", "役職別分析", "スタッフ別労働時間"])

with tab1:
    st.subheader("店舗別 総人件費・残業率")
    store_summary = (
        df.groupby("store_name", as_index=False)
        .agg(
            総人件費=("daily_wage", "sum"),
            平均時給=("hourly_rate", "mean"),
            総シフト数=("daily_wage", "count"),
            残業件数=("is_overtime", "sum"),
            総労働時間=("work_hours", "sum"),
        )
        .sort_values("総人件費", ascending=False)
    )
    store_summary["残業率(%)"] = (
        store_summary["残業件数"] / store_summary["総シフト数"] * 100
    ).round(1)
    store_summary["総人件費"] = store_summary["総人件費"].round(0).astype(int)
    store_summary["平均時給"] = store_summary["平均時給"].round(0).astype(int)
    store_summary["総労働時間"] = store_summary["総労働時間"].round(1)
    st.dataframe(store_summary, use_container_width=True)

    chart_file = CHARTS_DIR / "bar_store_labor_cost.png"
    if chart_file.exists():
        st.image(str(chart_file), caption="店舗別 総人件費（棒グラフ）")
    else:
        st.info("グラフ画像が見つかりません。visualize.py を先に実行してください。")

with tab2:
    st.subheader("役職別 平均日次賃金・労働時間")
    role_summary = (
        df.groupby("role", as_index=False)
        .agg(
            平均日次賃金=("daily_wage", "mean"),
            平均労働時間=("work_hours", "mean"),
            シフト数=("daily_wage", "count"),
        )
        .sort_values("平均日次賃金", ascending=False)
    )
    role_summary["平均日次賃金"] = role_summary["平均日次賃金"].round(0).astype(int)
    role_summary["平均労働時間"] = role_summary["平均労働時間"].round(2)
    st.dataframe(role_summary, use_container_width=True)

    chart_file = CHARTS_DIR / "bar_role_avg_wage.png"
    if chart_file.exists():
        st.image(str(chart_file), caption="役職別 平均日次賃金（棒グラフ）")
    else:
        st.info("グラフ画像が見つかりません。visualize.py を先に実行してください。")

with tab3:
    st.subheader("スタッフ別 月間労働時間 上位10名")
    staff_ranking = (
        df.groupby("staff_id", as_index=False)
        .agg(
            総労働時間=("work_hours", "sum"),
            シフト数=("work_hours", "count"),
            平均日次賃金=("daily_wage", "mean"),
        )
        .sort_values("総労働時間", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    staff_ranking.index = staff_ranking.index + 1
    staff_ranking["総労働時間"] = staff_ranking["総労働時間"].round(1)
    staff_ranking["平均日次賃金"] = staff_ranking["平均日次賃金"].round(0).astype(int)
    st.dataframe(staff_ranking, use_container_width=True)

    chart_file = CHARTS_DIR / "bar_staff_hours_top10.png"
    if chart_file.exists():
        st.image(str(chart_file), caption="スタッフ別労働時間 上位10名（横棒グラフ）")
    else:
        st.info("グラフ画像が見つかりません。visualize.py を先に実行してください。")

st.divider()

# ---- 高コストシフトテーブル ----
st.subheader("高コストシフト一覧")
high_cost = df[df["labor_cost_flag"] == "高コスト"].copy()
high_cost_display = high_cost[
    ["work_date", "staff_id", "store_name", "role", "work_hours", "hourly_rate", "daily_wage"]
].sort_values("daily_wage", ascending=False).head(20)
high_cost_display = high_cost_display.rename(columns={
    "work_date": "勤務日",
    "staff_id": "スタッフID",
    "store_name": "店舗名",
    "role": "役職",
    "work_hours": "労働時間(h)",
    "hourly_rate": "時給(円)",
    "daily_wage": "日次賃金(円)",
})
st.dataframe(high_cost_display, use_container_width=True)

# ---- 分析レポートexpander ----
with st.expander("分析レポート（Markdown）"):
    if REPORT_FILE.exists():
        report_text = REPORT_FILE.read_text(encoding="utf-8")
        st.markdown(report_text)
    else:
        st.warning("レポートファイルが見つかりません。analyze.py を先に実行してください。")
