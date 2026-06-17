# -*- coding: utf-8 -*-
"""
C-52: 保険問い合わせ・対応履歴分析ダッシュボード Streamlit アプリ
"""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="保険問い合わせ分析ダッシュボード",
    page_icon="[INS]",
    layout="wide",
)

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"

INQUIRY_TYPE_ORDER = ["契約内容確認", "保険金請求", "解約手続き", "新規加入", "変更手続き"]
CHANNEL_ORDER = ["電話", "メール", "窓口"]


@st.cache_data
def load_data() -> pd.DataFrame:
    path = OUTPUT_DIR / "cleaned_inquiries_202401.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    for col in ["handling_minutes", "is_resolved", "recontact_flag", "satisfaction"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "inquiry_date" in df.columns:
        df["inquiry_date"] = pd.to_datetime(df["inquiry_date"], errors="coerce")
    return df


@st.cache_data
def load_report() -> str:
    p = OUTPUT_DIR / "analysis_report.md"
    return p.read_text(encoding="utf-8") if p.exists() else "レポートが見つかりません。"


# --- データ読み込み ---
try:
    df_all = load_data()
except FileNotFoundError:
    st.error("cleaned_inquiries_202401.csv が見つかりません。cleanse.py を先に実行してください。")
    st.stop()

report_text = load_report()

# --- タイトル ---
st.title("保険問い合わせ・対応履歴分析ダッシュボード")
st.caption("2024年1月 | C-52 保険契約問い合わせ・対応履歴分析パイプライン")

# --- サイドバー: フィルター ---
st.sidebar.header("フィルター")

available_types = [t for t in INQUIRY_TYPE_ORDER if t in df_all["inquiry_type"].unique()] \
    if "inquiry_type" in df_all.columns else []
selected_types = st.sidebar.multiselect(
    "問い合わせ区分",
    options=available_types,
    default=available_types,
)

available_channels = [c for c in CHANNEL_ORDER if c in df_all["channel"].unique()] \
    if "channel" in df_all.columns else []
selected_channels = st.sidebar.multiselect(
    "チャネル",
    options=available_channels,
    default=available_channels,
)

# フィルター適用
df = df_all.copy()
if selected_types and "inquiry_type" in df.columns:
    df = df[df["inquiry_type"].isin(selected_types)]
if selected_channels and "channel" in df.columns:
    df = df[df["channel"].isin(selected_channels)]

# --- タブ ---
tab1, tab2, tab3 = st.tabs(["KPIサマリー", "区分・チャネル分析", "対応履歴明細"])

# ===== タブ1: KPIサマリー =====
with tab1:
    st.subheader("KPIサマリー")

    total_rows = len(df)
    resolution_rate = df["is_resolved"].mean() * 100 if "is_resolved" in df.columns and total_rows > 0 else 0
    avg_minutes = df["handling_minutes"].mean() if "handling_minutes" in df.columns and total_rows > 0 else 0
    avg_satisfaction = df["satisfaction"].mean() if "satisfaction" in df.columns and total_rows > 0 else 0
    recontact_rate = df["recontact_flag"].mean() * 100 if "recontact_flag" in df.columns and total_rows > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総件数", f"{total_rows:,} 件")
    c2.metric("解決率", f"{resolution_rate:.1f}%",
              delta="[OK]" if resolution_rate >= 85 else "[NG]",
              delta_color="normal" if resolution_rate >= 85 else "inverse")
    c3.metric("平均対応時間", f"{avg_minutes:.1f} 分")
    c4.metric("平均満足度", f"{avg_satisfaction:.2f} 点")

    st.divider()
    col_a, col_b = st.columns(2)
    col_a.metric("再問い合わせ率", f"{recontact_rate:.1f}%",
                 delta="[OK]" if recontact_rate <= 15 else "[NG]",
                 delta_color="inverse" if recontact_rate > 15 else "normal")

    # efficiency_flag サマリー
    if "efficiency_flag" in df.columns and total_rows > 0:
        eff_dist = df["efficiency_flag"].value_counts()
        st.subheader("対応効率分布")
        eff_cols = st.columns(len(eff_dist))
        for i, (flag, cnt) in enumerate(eff_dist.items()):
            eff_cols[i].metric(flag, f"{cnt} 件", f"{cnt/total_rows*100:.1f}%")

    with st.expander("分析レポートを見る", expanded=False):
        st.markdown(report_text)

# ===== タブ2: 区分・チャネル分析 =====
with tab2:
    charts_dir = OUTPUT_DIR / "charts"

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("問い合わせ区分別 件数")
        p = charts_dir / "bar_type_count.png"
        if p.exists():
            st.image(str(p), use_container_width=True)
        else:
            st.warning("グラフなし。visualize.py を実行してください。")

        st.subheader("問い合わせ区分別 解決率")
        p2 = charts_dir / "bar_type_resolution.png"
        if p2.exists():
            st.image(str(p2), use_container_width=True)
        else:
            st.warning("グラフなし。visualize.py を実行してください。")

    with col_right:
        st.subheader("チャネル別 平均満足度")
        p3 = charts_dir / "bar_channel_satisfaction.png"
        if p3.exists():
            st.image(str(p3), use_container_width=True)
        else:
            st.warning("グラフなし。visualize.py を実行してください。")

        if "inquiry_type" in df.columns and total_rows > 0:
            st.subheader("区分別サマリーテーブル")
            type_tbl = df.groupby("inquiry_type").agg(
                件数=("inquiry_id", "count"),
                解決率=("is_resolved", "mean"),
                平均対応時間=("handling_minutes", "mean"),
                平均満足度=("satisfaction", "mean"),
            )
            type_tbl["解決率"] = (type_tbl["解決率"] * 100).round(1).astype(str) + "%"
            type_tbl["平均対応時間"] = type_tbl["平均対応時間"].round(1)
            type_tbl["平均満足度"] = type_tbl["平均満足度"].round(2)
            st.dataframe(type_tbl, use_container_width=True)

# ===== タブ3: 対応履歴明細 =====
with tab3:
    st.subheader("対応履歴明細")

    display_cols = [c for c in [
        "inquiry_date", "inquiry_id", "inquiry_type", "channel",
        "operator_id", "handling_minutes", "is_resolved",
        "recontact_flag", "satisfaction", "efficiency_flag", "cs_grade"
    ] if c in df.columns]

    if len(df) > 0:
        st.dataframe(
            df[display_cols].sort_values("inquiry_date") if "inquiry_date" in df.columns else df[display_cols],
            use_container_width=True,
        )
        st.caption(f"表示件数: {len(df):,} 件")
    else:
        st.info("該当データなし。フィルターを確認してください。")
