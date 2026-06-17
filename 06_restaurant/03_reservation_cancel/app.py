# -*- coding: utf-8 -*-
"""
C-38: 予約キャンセル集計・傾向分析パイプライン
Streamlit ダッシュボードアプリ
"""

import json
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

st.set_page_config(
    page_title="飲食 予約・キャンセル管理ダッシュボード",
    page_icon="🍽️",
    layout="wide",
)

st.title("🍽️ 飲食 予約・キャンセル管理ダッシュボード")
st.caption("C-38 | 予約キャンセル集計・傾向分析パイプライン")


@st.cache_data
def load_data():
    csv_path = OUTPUT_DIR / "cleaned_reservations_202401.csv"
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str)
    df["guest_count"] = pd.to_numeric(df["guest_count"], errors="coerce").fillna(0).astype(int)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0).astype(int)
    df["is_cancel"] = pd.to_numeric(df["is_cancel"], errors="coerce").fillna(0).astype(int)
    df["loss_amount"] = pd.to_numeric(df["loss_amount"], errors="coerce").fillna(0).astype(int)
    df["reserv_date"] = pd.to_datetime(df["reserv_date"], format="%Y-%m-%d", errors="coerce")
    return df


@st.cache_data
def load_json():
    json_path = OUTPUT_DIR / "result_analysis.json"
    if not json_path.exists():
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


df_all = load_data()

if df_all is None:
    st.error(
        "データが見つかりません。先に以下のコマンドを実行してください。\n\n"
        "```\n"
        "python _gen_sample_data.py\n"
        "python cleanse.py\n"
        "python analyze.py\n"
        "```"
    )
    st.stop()

# ---- サイドバー: 店舗フィルター ----
st.sidebar.header("フィルター")
all_stores = sorted(df_all["store_name"].dropna().unique().tolist())
selected_stores = st.sidebar.multiselect(
    "店舗を選択",
    options=all_stores,
    default=all_stores,
)

df = df_all[df_all["store_name"].isin(selected_stores)].copy() if selected_stores else df_all.copy()

# ---- KPI ----
total_reserv = len(df)
cancel_count = int(df["is_cancel"].sum())
cancel_rate = cancel_count / total_reserv * 100 if total_reserv > 0 else 0
loss_total = int(df["loss_amount"].sum())
visit_count = int((df["status"] == "来店済み").sum())
visit_rate = visit_count / total_reserv * 100 if total_reserv > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("総予約数", f"{total_reserv:,} 件")
col2.metric("キャンセル率", f"{cancel_rate:.1f} %")
col3.metric("ロス金額合計", f"{loss_total:,} 円")
col4.metric("来店率", f"{visit_rate:.1f} %")

st.divider()

# ---- タブ ----
tab1, tab2, tab3 = st.tabs(["店舗別状況", "キャンセル理由", "曜日別傾向"])

with tab1:
    st.subheader("店舗別キャンセル状況")
    store_grp = df.groupby("store_name").agg(
        総予約数=("reserv_no", "count"),
        キャンセル数=("is_cancel", "sum"),
        損失金額合計=("loss_amount", "sum"),
    ).reset_index()
    store_grp["キャンセル率(%)"] = (store_grp["キャンセル数"] / store_grp["総予約数"] * 100).round(1)
    store_grp = store_grp.rename(columns={"store_name": "店舗名"})
    st.dataframe(store_grp.set_index("店舗名"), use_container_width=True)

    chart_path = CHARTS_DIR / "bar_store_cancel_rate.png"
    if chart_path.exists():
        st.image(str(chart_path), caption="店舗別キャンセル率")
    else:
        st.info("グラフは visualize.py を実行後に表示されます")

with tab2:
    st.subheader("キャンセル理由別集計")
    cancel_df = df[df["is_cancel"] == 1].copy()
    if len(cancel_df) > 0:
        reason_counts = cancel_df["cancel_reason"].value_counts().reset_index()
        reason_counts.columns = ["キャンセル理由", "件数"]
        reason_counts["割合(%)"] = (reason_counts["件数"] / reason_counts["件数"].sum() * 100).round(1)
        st.dataframe(reason_counts.set_index("キャンセル理由"), use_container_width=True)
    else:
        st.info("選択した店舗にキャンセルデータがありません")

    chart_path = CHARTS_DIR / "bar_cancel_reason.png"
    if chart_path.exists():
        st.image(str(chart_path), caption="キャンセル理由別件数")
    else:
        st.info("グラフは visualize.py を実行後に表示されます")

with tab3:
    st.subheader("曜日別キャンセル件数")
    weekday_order = ["月", "火", "水", "木", "金", "土", "日"]
    if "day_of_week" in df.columns:
        weekday_grp = df.groupby("day_of_week").agg(
            総予約=("reserv_no", "count"),
            キャンセル=("is_cancel", "sum"),
        ).reset_index()
        weekday_grp["キャンセル率(%)"] = (weekday_grp["キャンセル"] / weekday_grp["総予約"] * 100).round(1)
        weekday_grp["day_of_week"] = pd.Categorical(
            weekday_grp["day_of_week"], categories=weekday_order, ordered=True
        )
        weekday_grp = weekday_grp.sort_values("day_of_week").rename(columns={"day_of_week": "曜日"})
        st.dataframe(weekday_grp.set_index("曜日"), use_container_width=True)
    else:
        st.info("曜日列が存在しません")

    chart_path = CHARTS_DIR / "bar_weekday_cancel.png"
    if chart_path.exists():
        st.image(str(chart_path), caption="曜日別キャンセル件数")
    else:
        st.info("グラフは visualize.py を実行後に表示されます")

st.divider()

# ---- 最近のキャンセルテーブル ----
st.subheader("最近のキャンセル")
recent_cancel = (
    df[df["is_cancel"] == 1]
    .sort_values("reserv_date", ascending=False)
    .head(20)[["reserv_date", "reserv_no", "store_name", "course", "guest_count", "loss_amount", "cancel_reason"]]
    .rename(columns={
        "reserv_date": "予約日",
        "reserv_no": "予約番号",
        "store_name": "店舗",
        "course": "コース",
        "guest_count": "人数",
        "loss_amount": "損失金額",
        "cancel_reason": "キャンセル理由",
    })
)
if len(recent_cancel) > 0:
    st.dataframe(recent_cancel.reset_index(drop=True), use_container_width=True)
else:
    st.info("選択した店舗にキャンセルデータがありません")

# ---- 分析レポート expander ----
report_path = OUTPUT_DIR / "analysis_report.md"
if report_path.exists():
    with st.expander("分析レポート全文", expanded=False):
        report_content = report_path.read_text(encoding="utf-8")
        st.markdown(report_content)
else:
    with st.expander("分析レポート", expanded=False):
        st.info("レポートは analyze.py を実行後に表示されます")
