# -*- coding: utf-8 -*-
"""
B-66: 自動車 車検リマインダー・定期点検管理ダッシュボード
Streamlit ダッシュボード
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_customers(csv_path):
    df = pd.read_csv(csv_path)
    for col in ['last_inspection_date', 'next_inspection_due', 'last_oil_change']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def analyze_inspection_status(df, base_date=None):
    if base_date is None:
        base_date = pd.Timestamp.today()
    df = df.copy()
    df['days_until_inspection'] = (df['next_inspection_due'] - base_date).dt.days
    df['is_overdue'] = df['days_until_inspection'] < 0

    def get_status(days):
        if days < 0:
            return '期限切れ'
        elif days <= 30:
            return '30日以内'
        elif days <= 60:
            return '60日以内'
        return 'OK'

    df['inspection_status'] = df['days_until_inspection'].apply(get_status)
    df['days_since_oil_change'] = (base_date - df['last_oil_change']).dt.days
    df['oil_change_needed'] = df['days_since_oil_change'] > 180
    return df


def generate_summary_stats(df):
    total = len(df)
    overdue = int(df['is_overdue'].sum())
    within_30 = int(((df['days_until_inspection'] >= 0) & (df['days_until_inspection'] <= 30)).sum())
    within_60 = int(((df['days_until_inspection'] > 30) & (df['days_until_inspection'] <= 60)).sum())
    oil_needed = int(df['oil_change_needed'].sum())
    judgment = 'good' if (overdue == 0 and within_30 <= 3) else ('warning' if within_30 <= 10 else 'alert')
    return {
        'total_customers': total, 'overdue_count': overdue,
        'within_30_days': within_30, 'within_60_days': within_60,
        'oil_change_needed': oil_needed, 'judgment': judgment
    }


@st.cache_data
def load_automotive_inspection_data() -> pd.DataFrame:
    sample_csv = BASE_DIR / 'sample_customers.csv'
    if not sample_csv.exists():
        return pd.DataFrame()
    return load_customers(str(sample_csv))


st.title("🚗 B-66 自動車 車検リマインダー・定期点検管理ダッシュボード")

with st.sidebar:
    st.header("設定")
    uploaded_file = st.file_uploader("📁 顧客データ（CSV）をアップロード", type=['csv'])
    base_date_input = st.date_input("📅 基準日", value=datetime.today(),
                                    help="このシステムは基準日から計算します")
    base_date = pd.Timestamp(base_date_input)

if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
    for col in ['last_inspection_date', 'next_inspection_due', 'last_oil_change']:
        if col in df_raw.columns:
            df_raw[col] = pd.to_datetime(df_raw[col], errors="coerce")
else:
    df_raw = load_automotive_inspection_data()
    if not df_raw.empty:
        with st.sidebar:
            st.info("💡 デフォルトサンプルデータを使用しています")

if df_raw.empty:
    st.error("❌ sample_customers.csv が見つかりません")
    st.stop()

df = analyze_inspection_status(df_raw, base_date=base_date)
stats = generate_summary_stats(df)

# KPI
st.subheader("📊 KPI ダッシュボード")
col1, col2, col3, col4 = st.columns(4)
col1.metric("総顧客数", stats['total_customers'])
col2.metric("30日以内期限", stats['within_30_days'],
            delta=f"{stats['within_30_days']}件", delta_color="inverse")
col3.metric("期限切れ", stats['overdue_count'],
            delta="緊急" if stats['overdue_count'] > 0 else "OK",
            delta_color="inverse" if stats['overdue_count'] > 0 else "normal")
judgment_labels = {'good': '✅ Good', 'warning': '⚠️ Warning', 'alert': '🚨 Alert'}
col4.metric("総合判定", judgment_labels.get(stats['judgment'], stats['judgment']))

st.divider()

# 期限切れ
st.subheader("🚨 緊急アラート（期限切れ）")
alert_df = df[df['is_overdue']].copy()
_alert_cols = [c for c in ['customer_id', 'name', 'phone', 'days_until_inspection', 'contact_status'] if c in alert_df.columns]
alert_df = alert_df[_alert_cols].sort_values('days_until_inspection') if _alert_cols else alert_df
if len(alert_df) > 0:
    st.warning(f"⚠️ {len(alert_df)}件の顧客が期限切れです！")
    _col_rename = {'customer_id': '顧客ID', 'name': '顧客名', 'phone': '電話番号',
                   'days_until_inspection': '期限切れ日数', 'contact_status': '連絡状態'}
    st.dataframe(alert_df.rename(columns={k: v for k, v in _col_rename.items() if k in alert_df.columns}),
                 use_container_width=True, hide_index=True)
else:
    st.success("✅ 期限切れ顧客はいません")

st.divider()

# 30日以内
st.subheader("⚠️ 要連絡（30日以内）")
urgent_df = df[(df['days_until_inspection'] >= 0) & (df['days_until_inspection'] <= 30)].copy()
_u_cols = [c for c in ['customer_id', 'name', 'phone', 'days_until_inspection', 'contact_status'] if c in urgent_df.columns]
urgent_df = urgent_df[_u_cols].sort_values('days_until_inspection') if _u_cols else urgent_df
if len(urgent_df) > 0:
    _col_rename2 = {'customer_id': '顧客ID', 'name': '顧客名', 'phone': '電話番号',
                    'days_until_inspection': '期限までの日数', 'contact_status': '連絡状態'}
    st.dataframe(urgent_df.rename(columns={k: v for k, v in _col_rename2.items() if k in urgent_df.columns}),
                 use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ 30日以内の対象顧客はいません")

st.divider()

# 60日以内
st.subheader("📅 要注意（60日以内）")
caution_df = df[(df['days_until_inspection'] > 30) & (df['days_until_inspection'] <= 60)].copy()
_c_cols = [c for c in ['customer_id', 'name', 'phone', 'days_until_inspection', 'contact_status'] if c in caution_df.columns]
caution_df = caution_df[_c_cols].sort_values('days_until_inspection') if _c_cols else caution_df
if len(caution_df) > 0:
    st.dataframe(caution_df.rename(columns={k: v for k, v in _col_rename2.items() if k in caution_df.columns}),
                 use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ 60日以内の要注意顧客はいません")

st.divider()

# オイル交換推奨
st.subheader("🛢️ オイル交換推奨顧客（最終交換から6ヶ月超）")
oil_df = df[df['oil_change_needed']].copy()
_o_cols = [c for c in ['customer_id', 'name', 'phone', 'days_since_oil_change', 'mileage', 'contact_status'] if c in oil_df.columns]
oil_df = oil_df[_o_cols].sort_values('days_since_oil_change', ascending=False) if _o_cols else oil_df
if len(oil_df) > 0:
    st.info(f"💡 {len(oil_df)}件のオイル交換推奨顧客")
    _o_rename = {'customer_id': '顧客ID', 'name': '顧客名', 'phone': '電話番号',
                 'days_since_oil_change': 'オイル交換から経過日数', 'mileage': '走行距離(km)', 'contact_status': '連絡状態'}
    st.dataframe(oil_df.rename(columns={k: v for k, v in _o_rename.items() if k in oil_df.columns}),
                 use_container_width=True, hide_index=True)
else:
    st.success("✅ オイル交換推奨顧客はいません")

st.divider()

# サマリー分析
st.subheader("📈 詳細分析")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**連絡ステータス別サマリー**")
    if 'contact_status' in df.columns:
        contact_summary = df.groupby('contact_status').size().sort_values(ascending=False)
        st.bar_chart(contact_summary)
with col2:
    st.markdown("**車種別アラート集計（期限切れ・30日以内）**")
    if 'vehicle_type' in df.columns:
        vehicle_summary = df[df['days_until_inspection'] <= 30].groupby('vehicle_type').size().sort_values(ascending=False)
        if not vehicle_summary.empty:
            st.bar_chart(vehicle_summary)
        else:
            st.info("アラート対象の車種データがありません")

st.divider()

# CSV出力
st.subheader("📥 データエクスポート")
output_csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 全データをCSVダウンロード", data=output_csv,
                   file_name=f"inspection_data_{base_date.strftime('%Y%m%d')}.csv", mime='text/csv')
if len(alert_df) > 0:
    st.download_button("📥 期限切れリストをCSVダウンロード",
                       data=alert_df.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f"alert_overdue_{base_date.strftime('%Y%m%d')}.csv", mime='text/csv')
if len(urgent_df) > 0:
    st.download_button("📥 30日以内リストをCSVダウンロード",
                       data=urgent_df.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f"alert_urgent_{base_date.strftime('%Y%m%d')}.csv", mime='text/csv')
