import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from analyze import analyze

# ページ設定
st.set_page_config(
    page_title="C-118 整備案件・部品在庫管理ダッシュボード",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# スタイル設定
st.markdown("""
<style>
    .metric-card {
        background: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background: #ffe6e6;
        border-left: 4px solid #d62728;
    }
    .alert-medium {
        background: #fff4e6;
        border-left: 4px solid #ff7f0e;
    }
    .status-完了 {
        background-color: #d4edda;
        color: #155724;
    }
    .status-作業中 {
        background-color: #cfe2ff;
        color: #084298;
    }
    .status-待機中 {
        background-color: #fff3cd;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# タイトル
st.title("🔧 整備案件・部品在庫管理ダッシュボード")
st.caption("C-118 自動車整備業向けDXシステム")

# データ読み込み
@st.cache_data
def load_data():
    base_path = Path(__file__).parent
    service_path = base_path / "sample_service.csv"
    parts_path = base_path / "sample_parts.csv"

    service_df = pd.read_csv(service_path)
    parts_df = pd.read_csv(parts_path)

    return service_df, parts_df

service_df, parts_df = load_data()
result = analyze(service_df, parts_df)

# タブの作成
tab1, tab2 = st.tabs(["🔧 整備案件", "📦 部品在庫"])

# ==================== タブ1: 整備案件 ====================
with tab1:
    # KPIカード
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="総売上",
            value=f"¥{result['total_revenue']:,.0f}",
            delta="期間合計"
        )

    with col2:
        st.metric(
            label="案件完了率",
            value=f"{result['completion_rate']:.1f}%",
            delta=f"{int(result['completion_rate'])}%"
        )

    with col3:
        # 判定をアイコンで表現
        verdict_text = {
            "good": "✅ 良好",
            "warning": "⚠️ 要注意",
            "alert": "🔴 要改善"
        }
        verdict_color = {
            "good": "#28a745",
            "warning": "#ffc107",
            "alert": "#dc3545"
        }
        verdict = result["verdict"]
        st.markdown(f"""
        <div style="background: {verdict_color[verdict]}; color: white; padding: 1.5rem; border-radius: 0.5rem; text-align: center;">
            <h3 style="margin: 0; font-size: 1.2rem;">{verdict_text[verdict]}</h3>
            <p style="margin: 0.5rem 0 0 0;">判定ステータス</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.metric(
            label="処理件数",
            value=len(result['service_df']),
            delta=f"{int((result['service_df']['status'] == '完了').sum())}件完了"
        )

    st.divider()

    # グラフ1: 整備タイプ別売上
    col_graph1, col_graph2 = st.columns(2)

    with col_graph1:
        st.subheader("整備タイプ別売上")
        service_type_data = result['service_type_df'].sort_values('total_revenue', ascending=True)
        chart_data = service_type_data[['service_type', 'total_revenue']].set_index('service_type')
        st.bar_chart(chart_data, color=['#1f77b4'])

    with col_graph2:
        st.subheader("月次売上トレンド")
        monthly_data = result['monthly_df'].set_index('date')
        st.line_chart(monthly_data['total_revenue'], color=['#ff7f0e'])

    st.divider()

    # 詳細テーブル: 案件一覧
    st.subheader("案件一覧")

    # ステータス別フィルタ
    status_filter = st.multiselect(
        "ステータスでフィルタ",
        options=result['service_df']['status'].unique(),
        default=result['service_df']['status'].unique(),
        key="service_status_filter"
    )

    filtered_service = result['service_df'][result['service_df']['status'].isin(status_filter)].copy()

    # 表示用に整形
    display_service = filtered_service[[
        'date', 'job_id', 'customer', 'vehicle_type', 'service_type',
        'labor_hours', 'parts_cost', 'labor_cost', 'total_revenue', 'status'
    ]].copy()

    display_service['date'] = pd.to_datetime(display_service['date']).dt.strftime('%Y-%m-%d')
    display_service = display_service.rename(columns={
        'job_id': '案件ID',
        'customer': '顧客',
        'vehicle_type': '車種',
        'service_type': 'サービス',
        'labor_hours': '作業時間(h)',
        'parts_cost': '部品代(¥)',
        'labor_cost': '工賃(¥)',
        'total_revenue': '売上(¥)',
        'status': 'ステータス',
        'date': '日付'
    })

    # 数値フォーマット
    display_service['部品代(¥)'] = display_service['部品代(¥)'].apply(lambda x: f"¥{x:,.0f}")
    display_service['工賃(¥)'] = display_service['工賃(¥)'].apply(lambda x: f"¥{x:,.0f}")
    display_service['売上(¥)'] = display_service['売上(¥)'].apply(lambda x: f"¥{x:,.0f}")
    display_service['作業時間(h)'] = display_service['作業時間(h)'].apply(lambda x: f"{x:.1f}")

    st.dataframe(
        display_service,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ステータス": st.column_config.TextColumn(
                width="small"
            )
        }
    )

    # 統計情報
    st.divider()
    st.subheader("統計情報")

    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

    with stats_col1:
        avg_hours = result['service_df']['labor_hours'].mean()
        st.metric("平均作業時間", f"{avg_hours:.2f}h")

    with stats_col2:
        avg_parts = result['service_df']['parts_cost'].mean()
        st.metric("平均部品代", f"¥{avg_parts:,.0f}")

    with stats_col3:
        avg_revenue = result['service_df']['total_revenue'].mean()
        st.metric("平均売上", f"¥{avg_revenue:,.0f}")

    with stats_col4:
        st.metric("作業中件数", int((result['service_df']['status'] == '作業中').sum()))

# ==================== タブ2: 部品在庫 ====================
with tab2:
    # 在庫アラート KPI
    col_alert1, col_alert2, col_alert3 = st.columns(3)

    with col_alert1:
        alert_count = result['stock_alert_count']
        st.metric(
            label="在庫アラート件数",
            value=alert_count,
            delta="最小在庫未満" if alert_count > 0 else "正常",
            delta_color="inverse" if alert_count > 0 else "normal"
        )

    with col_alert2:
        total_parts = len(result['parts_df'])
        st.metric(
            label="管理部品数",
            value=total_parts
        )

    with col_alert3:
        avg_stock_ratio = (result['parts_df']['stock_ratio'].mean() * 100)
        st.metric(
            label="平均在庫充足率",
            value=f"{avg_stock_ratio:.1f}%"
        )

    st.divider()

    # グラフ1: カテゴリ別在庫量
    st.subheader("カテゴリ別在庫量")
    category_stock = result['parts_df'].groupby('category')['current_stock'].sum().sort_values(ascending=True)
    st.bar_chart(category_stock, color=['#2ca02c'])

    st.divider()

    # アラート部品一覧
    if len(result['alert_parts']) > 0:
        st.subheader("⚠️ 在庫アラート部品")

        alert_display = result['alert_parts'][[
            'part_id', 'part_name', 'category', 'current_stock', 'min_stock', 'stock_ratio', 'unit_cost', 'supplier'
        ]].copy()

        alert_display = alert_display.rename(columns={
            'part_id': '部品ID',
            'part_name': '部品名',
            'category': 'カテゴリ',
            'current_stock': '現在在庫',
            'min_stock': '最小在庫',
            'stock_ratio': '充足率',
            'unit_cost': '単価(¥)',
            'supplier': '仕入先'
        })

        alert_display['単価(¥)'] = alert_display['単価(¥)'].apply(lambda x: f"¥{x:,.0f}")
        alert_display['充足率'] = alert_display['充足率'].apply(lambda x: f"{x*100:.1f}%")

        st.dataframe(
            alert_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ 在庫アラートはありません")

    st.divider()

    # 全在庫テーブル
    st.subheader("全在庫一覧")

    # カテゴリフィルタ
    category_filter = st.multiselect(
        "カテゴリでフィルタ",
        options=result['parts_df']['category'].unique(),
        default=result['parts_df']['category'].unique(),
        key="parts_category_filter"
    )

    filtered_parts = result['parts_df'][result['parts_df']['category'].isin(category_filter)].copy()
    filtered_parts = filtered_parts.sort_values('stock_ratio')

    parts_display = filtered_parts[[
        'part_id', 'part_name', 'category', 'current_stock', 'min_stock', 'stock_ratio', 'unit_cost', 'supplier'
    ]].copy()

    parts_display = parts_display.rename(columns={
        'part_id': '部品ID',
        'part_name': '部品名',
        'category': 'カテゴリ',
        'current_stock': '現在在庫',
        'min_stock': '最小在庫',
        'stock_ratio': '充足率',
        'unit_cost': '単価(¥)',
        'supplier': '仕入先'
    })

    parts_display['単価(¥)'] = parts_display['単価(¥)'].apply(lambda x: f"¥{x:,.0f}")
    parts_display['充足率'] = parts_display['充足率'].apply(lambda x: f"{x*100:.1f}%")

    st.dataframe(
        parts_display,
        use_container_width=True,
        hide_index=True
    )
