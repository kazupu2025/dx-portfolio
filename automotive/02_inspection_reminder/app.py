"""
C-125: 顧客車検リマインダー・定期点検管理
Streamlit ダッシュボード
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import io

from analyze import (
    load_customers,
    analyze_inspection_status,
    generate_summary_stats,
    get_alert_dataframe,
    get_urgent_dataframe,
    get_caution_dataframe,
    get_oil_change_dataframe,
    get_contact_status_summary,
    get_vehicle_type_summary
)


def main():
    st.set_page_config(page_title="顧客車検リマインダー", layout="wide")
    st.title("🚗 顧客車検リマインダー・定期点検管理 (C-125)")

    # ==================== サイドバー ====================
    with st.sidebar:
        st.header("設定")

        # CSVアップロード
        uploaded_file = st.file_uploader("📁 顧客データ（CSV）をアップロード", type=['csv'])

        # 基準日選択
        base_date = st.date_input(
            "📅 基準日",
            value=datetime.today(),
            help="このシステムは基準日から計算します"
        )
        base_date = pd.Timestamp(base_date)

        # アップロードファイルが存在するか、デフォルトファイルを使うか
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
        else:
            sample_csv = Path(__file__).parent / 'sample_customers.csv'
            if sample_csv.exists():
                df = load_customers(str(sample_csv))
                st.info("💡 デフォルトサンプルデータを使用しています")
            else:
                st.error("❌ sample_customers.csv が見つかりません")
                return

    # ==================== データ分析 ====================
    df = analyze_inspection_status(df, base_date=base_date)
    stats = generate_summary_stats(df)

    # ==================== KPIカード ====================
    st.subheader("📊 KPI ダッシュボード")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="総顧客数",
            value=stats['total_customers'],
            delta=None
        )

    with col2:
        st.metric(
            label="30日以内期限",
            value=stats['within_30_days'],
            delta=f"{stats['within_30_days']}件",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            label="期限切れ",
            value=stats['overdue_count'],
            delta="緊急" if stats['overdue_count'] > 0 else "OK",
            delta_color="inverse" if stats['overdue_count'] > 0 else "normal"
        )

    with col4:
        judgment_colors = {
            'good': '✅ Good',
            'warning': '⚠️ Warning',
            'alert': '🚨 Alert'
        }
        st.metric(
            label="総合判定",
            value=judgment_colors.get(stats['judgment'], stats['judgment'])
        )

    st.divider()

    # ==================== 🚨 期限切れテーブル ====================
    st.subheader("🚨 緊急アラート（期限切れ）")

    alert_df = get_alert_dataframe(df)
    if len(alert_df) > 0:
        st.warning(f"⚠️ {len(alert_df)}件の顧客が期限切れです！")

        # Streamlit で赤背景を表現するため、HTML を使用
        alert_display = alert_df.copy()
        alert_display.columns = ['顧客ID', '顧客名', '電話番号', '期限切れ日数', '連絡状態']

        # DataFrameスタイリング
        def highlight_overdue(row):
            return ['background-color: #ffcccc'] * len(row)

        styled_alert = alert_display.style.apply(highlight_overdue, axis=1)
        st.dataframe(styled_alert, use_container_width=True)
    else:
        st.success("✅ 期限切れ顧客はいません")

    st.divider()

    # ==================== ⚠️ 30日以内テーブル ====================
    st.subheader("⚠️ 要連絡（30日以内）")

    urgent_df = get_urgent_dataframe(df)
    if len(urgent_df) > 0:
        urgent_display = urgent_df.copy()
        urgent_display.columns = ['顧客ID', '顧客名', '電話番号', '期限までの日数', '連絡状態']

        def highlight_urgent(row):
            return ['background-color: #ffe6cc'] * len(row)

        styled_urgent = urgent_display.style.apply(highlight_urgent, axis=1)
        st.dataframe(styled_urgent, use_container_width=True)
    else:
        st.info("ℹ️ 30日以内の対象顧客はいません")

    st.divider()

    # ==================== 📅 60日以内テーブル ====================
    st.subheader("📅 要注意（60日以内）")

    caution_df = get_caution_dataframe(df)
    if len(caution_df) > 0:
        caution_display = caution_df.copy()
        caution_display.columns = ['顧客ID', '顧客名', '電話番号', '期限までの日数', '連絡状態']

        def highlight_caution(row):
            return ['background-color: #fff9e6'] * len(row)

        styled_caution = caution_display.style.apply(highlight_caution, axis=1)
        st.dataframe(styled_caution, use_container_width=True)
    else:
        st.info("ℹ️ 60日以内の要注意顧客はいません")

    st.divider()

    # ==================== オイル交換推奨顧客 ====================
    st.subheader("🛢️ オイル交換推奨顧客（最終交換から6ヶ月超）")

    oil_df = get_oil_change_dataframe(df)
    if len(oil_df) > 0:
        st.info(f"💡 {len(oil_df)}件のオイル交換推奨顧客")

        oil_display = oil_df.copy()
        oil_display.columns = ['顧客ID', '顧客名', '電話番号', 'オイル交換から経過日数', '走行距離(km)', '連絡状態']

        st.dataframe(oil_display, use_container_width=True)
    else:
        st.success("✅ オイル交換推奨顧客はいません")

    st.divider()

    # ==================== サマリー分析 ====================
    st.subheader("📈 詳細分析")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**連絡ステータス別サマリー**")
        contact_summary = get_contact_status_summary(df)
        st.bar_chart(contact_summary.set_index('contact_status')['count'])

    with col2:
        st.markdown("**車種別アラート集計（期限切れ・30日以内）**")
        vehicle_summary = get_vehicle_type_summary(df)
        st.bar_chart(vehicle_summary.set_index('vehicle_type')['alert_count'])

    st.divider()

    # ==================== CSV出力 ====================
    st.subheader("📥 データエクスポート")

    # 全データをCSVで出力
    output_csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 全データをCSVダウンロード",
        data=output_csv,
        file_name=f"inspection_data_{base_date.strftime('%Y%m%d')}.csv",
        mime='text/csv'
    )

    # 期限切れリストをCSVで出力
    if len(alert_df) > 0:
        alert_csv = alert_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 期限切れリストをCSVダウンロード",
            data=alert_csv,
            file_name=f"alert_overdue_{base_date.strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )

    # 30日以内リストをCSVで出力
    if len(urgent_df) > 0:
        urgent_csv = urgent_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 30日以内リストをCSVダウンロード",
            data=urgent_csv,
            file_name=f"alert_urgent_{base_date.strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )


if __name__ == '__main__':
    main()
