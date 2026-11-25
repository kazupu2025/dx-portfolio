# -*- coding: utf-8 -*-
"""
B-65: 自動車 整備案件・部品在庫管理ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ── analyze.py インライン（Streamlit Cloud 互換）──
REQUIRED_SERVICE_COLUMNS = ["date","job_id","customer","vehicle_type","service_type","labor_hours","parts_cost","labor_rate","status"]
REQUIRED_PARTS_COLUMNS = ["part_id","part_name","category","current_stock","min_stock","unit_cost","supplier"]


def analyze(service_df: pd.DataFrame, parts_df: pd.DataFrame) -> dict:
    service_df = service_df.copy()
    parts_df = parts_df.copy()

    service_df["date"] = pd.to_datetime(service_df["date"])
    service_df["labor_cost"] = service_df["labor_hours"] * service_df["labor_rate"]
    service_df["total_revenue"] = service_df["labor_cost"] + service_df["parts_cost"]

    service_type_df = service_df.groupby("service_type").agg(
        count=("job_id","count"),
        avg_hours=("labor_hours","mean"),
        avg_revenue=("total_revenue","mean"),
        total_revenue=("total_revenue","sum"),
    ).reset_index().sort_values("total_revenue", ascending=False)

    vehicle_df = service_df.groupby("vehicle_type").agg(
        count=("job_id","count"),
        avg_revenue=("total_revenue","mean"),
    ).reset_index()

    monthly_df = service_df.groupby(service_df["date"].dt.to_period("M")).agg(
        total_revenue=("total_revenue","sum"),
        job_count=("job_id","count"),
    ).reset_index()
    monthly_df["date"] = monthly_df["date"].astype(str)

    parts_df["stock_ratio"] = parts_df["current_stock"] / parts_df["min_stock"].replace(0, np.nan)
    parts_df["alert"] = parts_df["current_stock"] < parts_df["min_stock"]
    alert_parts = parts_df[parts_df["alert"]].sort_values("stock_ratio")

    total_revenue = float(service_df["total_revenue"].sum())
    completed_jobs = int((service_df["status"] == "完了").sum())
    completion_rate = completed_jobs / len(service_df) * 100
    stock_alert_count = int(parts_df["alert"].sum())

    verdict = "good" if (completion_rate >= 80 and stock_alert_count <= 2) else \
              "warning" if completion_rate >= 60 else "alert"

    return {
        "service_df": service_df, "service_type_df": service_type_df,
        "vehicle_df": vehicle_df, "monthly_df": monthly_df,
        "parts_df": parts_df, "alert_parts": alert_parts,
        "total_revenue": total_revenue, "completion_rate": float(completion_rate),
        "stock_alert_count": stock_alert_count, "verdict": verdict,
    }


@st.cache_data
def load_automotive_service_inventory_data():
    service_path = BASE_DIR / "sample_service.csv"
    parts_path = BASE_DIR / "sample_parts.csv"
    if not service_path.exists() or not parts_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    service_df = pd.read_csv(service_path)
    parts_df = pd.read_csv(parts_path)
    return service_df, parts_df


st.title("🔧 B-65 自動車 整備案件・部品在庫管理ダッシュボード")
st.caption("C-118 自動車整備業向けDXシステム")

service_df, parts_df = load_automotive_service_inventory_data()

if service_df.empty or parts_df.empty:
    st.error("データファイルが見つかりません（sample_service.csv / sample_parts.csv）")
    st.stop()

result = analyze(service_df, parts_df)

tab1, tab2 = st.tabs(["🔧 整備案件", "📦 部品在庫"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総売上", f"¥{result['total_revenue']:,.0f}", delta="期間合計")
    col2.metric("案件完了率", f"{result['completion_rate']:.1f}%")
    verdict_text = {"good": "✅ 良好", "warning": "⚠️ 要注意", "alert": "🔴 要改善"}
    col3.metric("総合判定", verdict_text.get(result["verdict"], result["verdict"]))
    col4.metric("処理件数", len(result['service_df']),
                delta=f"{int((result['service_df']['status'] == '完了').sum())}件完了")

    st.divider()

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("整備タイプ別売上")
        _stype = result['service_type_df'].sort_values('total_revenue', ascending=True)
        st.bar_chart(_stype.set_index('service_type')['total_revenue'])
    with col_g2:
        st.subheader("月次売上トレンド")
        st.line_chart(result['monthly_df'].set_index('date')['total_revenue'])

    st.divider()
    st.subheader("案件一覧")

    status_filter = st.multiselect(
        "ステータスでフィルタ",
        options=result['service_df']['status'].unique(),
        default=result['service_df']['status'].unique(),
        key="b65_service_status_filter"
    )
    filtered_service = result['service_df'][result['service_df']['status'].isin(status_filter)].copy()
    _want = ['date', 'job_id', 'customer', 'vehicle_type', 'service_type',
             'labor_hours', 'parts_cost', 'labor_cost', 'total_revenue', 'status']
    _avail = [c for c in _want if c in filtered_service.columns]
    display_service = filtered_service[_avail].copy()
    if 'date' in display_service.columns:
        display_service['date'] = pd.to_datetime(display_service['date']).dt.strftime('%Y-%m-%d')
    display_service = display_service.rename(columns={
        'job_id': '案件ID', 'customer': '顧客', 'vehicle_type': '車種',
        'service_type': 'サービス', 'labor_hours': '作業時間(h)',
        'parts_cost': '部品代(¥)', 'labor_cost': '工賃(¥)',
        'total_revenue': '売上(¥)', 'status': 'ステータス', 'date': '日付'
    })
    for col in ['部品代(¥)', '工賃(¥)', '売上(¥)']:
        if col in display_service.columns:
            display_service[col] = display_service[col].apply(lambda x: f"¥{x:,.0f}")
    if '作業時間(h)' in display_service.columns:
        display_service['作業時間(h)'] = display_service['作業時間(h)'].apply(lambda x: f"{x:.1f}")
    st.dataframe(display_service, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("統計情報")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("平均作業時間", f"{result['service_df']['labor_hours'].mean():.2f}h")
    s2.metric("平均部品代", f"¥{result['service_df']['parts_cost'].mean():,.0f}")
    s3.metric("平均売上", f"¥{result['service_df']['total_revenue'].mean():,.0f}")
    s4.metric("作業中件数", int((result['service_df']['status'] == '作業中').sum()))

with tab2:
    a1, a2, a3 = st.columns(3)
    alert_count = result['stock_alert_count']
    a1.metric("在庫アラート件数", alert_count,
              delta="最小在庫未満" if alert_count > 0 else "正常",
              delta_color="inverse" if alert_count > 0 else "normal")
    a2.metric("管理部品数", len(result['parts_df']))
    avg_stock_ratio = result['parts_df']['stock_ratio'].mean() * 100
    a3.metric("平均在庫充足率", f"{avg_stock_ratio:.1f}%")

    st.divider()
    st.subheader("カテゴリ別在庫量")
    if 'category' in result['parts_df'].columns and 'current_stock' in result['parts_df'].columns:
        cat_stock = result['parts_df'].groupby('category')['current_stock'].sum().sort_values(ascending=True)
        st.bar_chart(cat_stock)

    st.divider()
    if len(result['alert_parts']) > 0:
        st.subheader("⚠️ 在庫アラート部品")
        _ap = result['alert_parts'].copy()
        _ap_want = ['part_id', 'part_name', 'category', 'current_stock', 'min_stock', 'stock_ratio', 'unit_cost', 'supplier']
        _ap_avail = [c for c in _ap_want if c in _ap.columns]
        _ap = _ap[_ap_avail].rename(columns={
            'part_id': '部品ID', 'part_name': '部品名', 'category': 'カテゴリ',
            'current_stock': '現在在庫', 'min_stock': '最小在庫',
            'stock_ratio': '充足率', 'unit_cost': '単価(¥)', 'supplier': '仕入先'
        })
        if '単価(¥)' in _ap.columns:
            _ap['単価(¥)'] = _ap['単価(¥)'].apply(lambda x: f"¥{x:,.0f}")
        if '充足率' in _ap.columns:
            _ap['充足率'] = _ap['充足率'].apply(lambda x: f"{x*100:.1f}%")
        st.dataframe(_ap, use_container_width=True, hide_index=True)
    else:
        st.success("✅ 在庫アラートはありません")

    st.divider()
    st.subheader("全在庫一覧")
    category_filter = st.multiselect(
        "カテゴリでフィルタ",
        options=result['parts_df']['category'].unique(),
        default=result['parts_df']['category'].unique(),
        key="b65_parts_category_filter"
    )
    filtered_parts = result['parts_df'][result['parts_df']['category'].isin(category_filter)].copy()
    filtered_parts = filtered_parts.sort_values('stock_ratio')
    _p_want = ['part_id', 'part_name', 'category', 'current_stock', 'min_stock', 'stock_ratio', 'unit_cost', 'supplier']
    _p_avail = [c for c in _p_want if c in filtered_parts.columns]
    parts_display = filtered_parts[_p_avail].rename(columns={
        'part_id': '部品ID', 'part_name': '部品名', 'category': 'カテゴリ',
        'current_stock': '現在在庫', 'min_stock': '最小在庫',
        'stock_ratio': '充足率', 'unit_cost': '単価(¥)', 'supplier': '仕入先'
    })
    if '単価(¥)' in parts_display.columns:
        parts_display['単価(¥)'] = parts_display['単価(¥)'].apply(lambda x: f"¥{x:,.0f}")
    if '充足率' in parts_display.columns:
        parts_display['充足率'] = parts_display['充足率'].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(parts_display, use_container_width=True, hide_index=True)
