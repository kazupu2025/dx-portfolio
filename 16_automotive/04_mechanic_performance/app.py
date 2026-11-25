# -*- coding: utf-8 -*-
"""
B-68: 自動車 整備士別生産性・売上分析ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

THRESHOLD_GOOD = 6000
THRESHOLD_WARNING = 4000


# ── 分析関数（インライン）────────────────────────────────
def _load_mechanic_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def _analyze_mechanic_performance(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mid in df["mechanic_id"].unique():
        mdf = df[df["mechanic_id"] == mid]
        rev = mdf["labor_revenue"].sum()
        hrs = mdf["labor_hours"].sum()
        rate = rev / hrs if hrs > 0 else 0
        rows.append({
            "mechanic_id": mid,
            "mechanic_name": mdf["mechanic_name"].iloc[0] if "mechanic_name" in mdf.columns else mid,
            "job_count": len(mdf),
            "total_revenue": rev,
            "avg_rating": round(mdf["customer_rating"].mean(), 2) if "customer_rating" in mdf.columns else 0,
            "total_hours": hrs,
            "avg_hourly_rate": round(rate, 2),
            "judgment": "good" if rate >= THRESHOLD_GOOD else ("warning" if rate >= THRESHOLD_WARNING else "alert"),
        })
    return pd.DataFrame(rows).sort_values("total_revenue", ascending=False)


def _analyze_service_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    if "service_type" not in df.columns:
        return pd.DataFrame()
    rows = []
    for svc in df["service_type"].unique():
        sdf = df[df["service_type"] == svc]
        rows.append({
            "service_type": svc,
            "job_count": len(sdf),
            "total_revenue": sdf["labor_revenue"].sum(),
            "avg_rating": round(sdf["customer_rating"].mean(), 2) if "customer_rating" in sdf.columns else 0,
        })
    return pd.DataFrame(rows).sort_values("job_count", ascending=False)


def _analyze_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2["year_month"] = df2["date"].dt.to_period("M")
    rows = []
    for period in sorted(df2["year_month"].dropna().unique()):
        pdf = df2[df2["year_month"] == period]
        rev = pdf["labor_revenue"].sum()
        hrs = pdf["labor_hours"].sum()
        rows.append({
            "month": str(period),
            "job_count": len(pdf),
            "total_revenue": rev,
            "avg_rating": round(pdf["customer_rating"].mean(), 2) if "customer_rating" in pdf.columns else 0,
            "total_hours": hrs,
            "avg_hourly_rate": round(rev / hrs, 2) if hrs > 0 else 0,
        })
    return pd.DataFrame(rows)


def _calculate_summary(df: pd.DataFrame) -> dict:
    rev = df["labor_revenue"].sum()
    hrs = df["labor_hours"].sum()
    rate = rev / hrs if hrs > 0 else 0
    return {
        "total_revenue": rev,
        "avg_rating": round(df["customer_rating"].mean(), 2) if "customer_rating" in df.columns else 0,
        "avg_hourly_rate": round(rate, 2),
        "job_count": len(df),
        "overall_judgment": "good" if rate >= THRESHOLD_GOOD else ("warning" if rate >= THRESHOLD_WARNING else "alert"),
    }


@st.cache_data
def load_automotive_mechanic_data() -> pd.DataFrame:
    csv_path = BASE_DIR / "sample_mechanic.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    return _load_mechanic_csv(str(csv_path))


# ── Streamlit UI ────────────────────────────────────────
st.title("🔧 B-68 自動車 整備士別生産性・売上分析ダッシュボード")
st.caption("B-68 | 整備士別案件数・売上・顧客評価・時給効率を分析")

df_raw = load_automotive_mechanic_data()

if df_raw.empty:
    st.error(f"データファイルが見つかりません: {BASE_DIR / 'sample_mechanic.csv'}")
    st.stop()

with st.sidebar:
    st.header("🔍 フィルター")
    if "service_type" in df_raw.columns:
        svcs = sorted(df_raw["service_type"].dropna().unique().tolist())
        sel_svcs = st.multiselect("サービス種別", svcs, default=svcs, key="b68_service_filter")
        df = df_raw[df_raw["service_type"].isin(sel_svcs)].copy() if sel_svcs else df_raw.copy()
    else:
        df = df_raw.copy()

summary = _calculate_summary(df)
mechanic_stats = _analyze_mechanic_performance(df)
service_stats = _analyze_service_breakdown(df)
monthly_stats = _analyze_monthly_trend(df)

# KPI
col1, col2, col3, col4 = st.columns(4)
col1.metric("総売上", f"¥{summary['total_revenue']:,.0f}", delta=f"{summary['job_count']}件")
col2.metric("平均顧客評価", f"{summary['avg_rating']:.2f}/5")
col3.metric("平均時給効率", f"¥{summary['avg_hourly_rate']:,.0f}/h",
            delta="👍 良好" if summary["avg_hourly_rate"] >= THRESHOLD_GOOD else "⚠️ 要改善")
verdict_text = {"good": "🟢 GOOD", "warning": "🟡 WARNING", "alert": "🔴 ALERT"}
col4.metric("全体判定", verdict_text.get(summary["overall_judgment"], "―"))

st.divider()

tab1, tab2, tab3 = st.tabs(["👤 整備士別分析", "🛠️ サービス種別", "📈 月別トレンド"])

with tab1:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("整備士別 総売上")
        if not mechanic_stats.empty and "mechanic_name" in mechanic_stats.columns:
            rev_ser = mechanic_stats.set_index("mechanic_name")["total_revenue"].sort_values()
            st.bar_chart(rev_ser)
    with col_r:
        st.subheader("整備士別 平均顧客評価")
        if not mechanic_stats.empty and "avg_rating" in mechanic_stats.columns:
            rating_ser = mechanic_stats.set_index("mechanic_name")["avg_rating"].sort_values()
            st.bar_chart(rating_ser)

    st.subheader("📋 整備士詳細")
    if not mechanic_stats.empty:
        disp = mechanic_stats[
            [c for c in ["mechanic_name", "job_count", "total_revenue", "avg_rating",
                         "total_hours", "avg_hourly_rate", "judgment"] if c in mechanic_stats.columns]
        ].copy()
        disp.columns = [{"mechanic_name": "整備士名", "job_count": "案件数",
                         "total_revenue": "総売上", "avg_rating": "平均評価",
                         "total_hours": "稼働時間(h)", "avg_hourly_rate": "時給効率",
                         "judgment": "判定"}.get(c, c) for c in disp.columns]
        st.dataframe(disp, use_container_width=True, hide_index=True)

with tab2:
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.subheader("サービス種別 案件数")
        if not service_stats.empty:
            st.bar_chart(service_stats.set_index("service_type")["job_count"].sort_values())
    with col_r2:
        st.subheader("サービス種別 売上")
        if not service_stats.empty:
            st.bar_chart(service_stats.set_index("service_type")["total_revenue"].sort_values())

with tab3:
    if not monthly_stats.empty:
        col_l3, col_r3 = st.columns(2)
        with col_l3:
            st.subheader("月別 案件数")
            st.line_chart(monthly_stats.set_index("month")["job_count"])
        with col_r3:
            st.subheader("月別 売上")
            st.line_chart(monthly_stats.set_index("month")["total_revenue"])

        st.subheader("月別 詳細テーブル")
        st.dataframe(monthly_stats, use_container_width=True, hide_index=True)

st.divider()

# レポートダウンロード
report_lines = [
    "# 整備士別生産性・売上分析レポート",
    f"総売上: ¥{summary['total_revenue']:,.0f}",
    f"平均時給効率: ¥{summary['avg_hourly_rate']:,.0f}/h",
    f"全体判定: {summary['overall_judgment'].upper()}",
]
st.download_button("📥 サマリーレポートをダウンロード",
                   data="\n".join(report_lines).encode("utf-8"),
                   file_name="mechanic_report.md", mime="text/markdown")
