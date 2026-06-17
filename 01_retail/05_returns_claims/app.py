# -*- coding: utf-8 -*-
"""
C-34 返品・クレームデータ集計レポートパイプライン
Streamlit ダッシュボード

起動: streamlit run app.py
"""

from pathlib import Path
import pandas as pd
import streamlit as st

# ---- ページ設定 -----------------------------------------------------------
st.set_page_config(
    page_title="小売 返品・クレーム管理ダッシュボード",
    page_icon="🏪",
    layout="wide",
)

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_claims_202401.csv"
REPORT_PATH = BASE_DIR / "output" / "analysis_report.md"
CHARTS_DIR = BASE_DIR / "output" / "charts"


@st.cache_data
def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CSV_PATH, encoding="utf-8-sig")


# ---- ヘッダー ------------------------------------------------------------
st.title("🏪 小売 返品・クレーム管理ダッシュボード")
st.caption("2024年1月 | C-34 返品・クレームデータ集計レポートパイプライン")

df_all = load_data()

if df_all.empty:
    st.error(
        "データが見つかりません。"
        "先に `_gen_sample_data.py` → `cleanse.py` → `analyze.py` を実行してください。"
    )
    st.stop()

# ---- サイドバー: 店舗フィルター ------------------------------------------
st.sidebar.header("フィルター")
all_stores = sorted(df_all["store_name"].unique().tolist())
selected_stores = st.sidebar.multiselect(
    "店舗を選択",
    options=all_stores,
    default=all_stores,
    help="複数選択可。すべて選択すると全店舗を表示します。",
)

if selected_stores:
    df = df_all[df_all["store_name"].isin(selected_stores)].copy()
else:
    df = df_all.copy()

# ---- KPI カード ----------------------------------------------------------
total_claims = len(df)
resolve_rate = df["is_resolved"].mean() * 100 if total_claims > 0 else 0
avg_response = df["response_days"].mean() if total_claims > 0 else 0
total_amount = int(df["return_amount"].sum()) if total_claims > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("総クレーム数", f"{total_claims:,} 件")
col2.metric("解決率", f"{resolve_rate:.1f}%")
col3.metric("平均対応日数", f"{avg_response:.1f} 日")
col4.metric("総返品金額", f"{total_amount:,} 円")

st.divider()

# ---- タブ ----------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["店舗別状況", "クレーム区分", "対応スピード"])

# --- TAB 1: 店舗別状況 ---
with tab1:
    st.subheader("店舗別クレーム状況")

    store_summary = (
        df.groupby("store_name")
        .agg(
            クレーム件数=("case_no", "count"),
            解決件数=("is_resolved", "sum"),
            解決率=("is_resolved", "mean"),
            平均返品金額=("return_amount", "mean"),
            合計返品金額=("return_amount", "sum"),
            平均対応日数=("response_days", "mean"),
        )
        .reset_index()
        .rename(columns={"store_name": "店舗名"})
    )
    store_summary["解決率"] = (store_summary["解決率"] * 100).round(1).astype(str) + "%"
    store_summary["平均返品金額"] = store_summary["平均返品金額"].round(0).astype(int)
    store_summary["合計返品金額"] = store_summary["合計返品金額"].astype(int)
    store_summary["平均対応日数"] = store_summary["平均対応日数"].round(1)

    st.dataframe(store_summary, use_container_width=True, hide_index=True)

    chart_path = CHARTS_DIR / "bar_store_claim_count.png"
    if chart_path.exists():
        st.image(str(chart_path), caption="店舗別クレーム件数")
    else:
        st.info("グラフが未生成です。visualize.py を実行してください。")

# --- TAB 2: クレーム区分 ---
with tab2:
    st.subheader("クレーム区分別件数")

    claim_summary = (
        df.groupby("claim_type")["case_no"]
        .count()
        .reset_index()
        .rename(columns={"claim_type": "クレーム区分", "case_no": "件数"})
        .sort_values("件数", ascending=False)
        .reset_index(drop=True)
    )
    claim_summary.index = claim_summary.index + 1

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.dataframe(claim_summary, use_container_width=True)
    with col_b:
        chart_path = CHARTS_DIR / "bar_claim_type.png"
        if chart_path.exists():
            st.image(str(chart_path), caption="クレーム区分別件数")
        else:
            st.info("グラフが未生成です。visualize.py を実行してください。")

# --- TAB 3: 対応スピード ---
with tab3:
    st.subheader("対応スピード分布")

    response_summary = (
        df.groupby("response_level")["case_no"]
        .count()
        .reset_index()
        .rename(columns={"response_level": "対応スピード", "case_no": "件数"})
    )
    order_map = {"迅速": 0, "標準": 1, "遅延": 2}
    response_summary["_order"] = response_summary["対応スピード"].map(order_map)
    response_summary = response_summary.sort_values("_order").drop(columns="_order").reset_index(drop=True)
    total_resp = response_summary["件数"].sum()
    response_summary["割合"] = (response_summary["件数"] / total_resp * 100).round(1).astype(str) + "%"

    col_c, col_d = st.columns([1, 1])
    with col_c:
        st.dataframe(response_summary, use_container_width=True, hide_index=True)
    with col_d:
        chart_path = CHARTS_DIR / "pie_response_level.png"
        if chart_path.exists():
            st.image(str(chart_path), caption="対応スピード別件数")
        else:
            st.info("グラフが未生成です。visualize.py を実行してください。")

st.divider()

# ---- 未解決案件テーブル --------------------------------------------------
st.subheader("未解決案件一覧")
unresolved = df[df["is_resolved"] == 0][
    ["case_no", "receipt_date", "store_name", "category", "claim_type", "return_amount", "response_days"]
].rename(columns={
    "case_no": "案件番号",
    "receipt_date": "受付日",
    "store_name": "店舗名",
    "category": "カテゴリ",
    "claim_type": "クレーム区分",
    "return_amount": "返品金額",
    "response_days": "対応日数",
}).sort_values("対応日数", ascending=False).reset_index(drop=True)

if unresolved.empty:
    st.success("未解決案件はありません。")
else:
    st.dataframe(unresolved, use_container_width=True, hide_index=True)
    st.caption(f"未解決件数: {len(unresolved)} 件")

# ---- 分析レポート expander -----------------------------------------------
st.divider()
with st.expander("分析レポートを表示", expanded=False):
    if REPORT_PATH.exists():
        report_text = REPORT_PATH.read_text(encoding="utf-8")
        st.markdown(report_text)
    else:
        st.warning("レポートが未生成です。analyze.py を実行してください。")
