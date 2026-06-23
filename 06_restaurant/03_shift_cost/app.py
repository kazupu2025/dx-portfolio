import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from analyze import analyze, REQUIRED_COLUMNS

st.set_page_config(page_title="C-110 シフト管理・人件費集計", layout="wide")

st.title("C-110 アルバイトシフト管理・人件費集計")

# ========== サイドバー ==========
with st.sidebar:
    st.subheader("データ入力")

    # サンプルデータ or アップロード
    data_source = st.radio("データソース選択", ["サンプルデータを使用", "CSVアップロード"])

    if data_source == "サンプルデータを使用":
        sample_file = Path(__file__).parent / "sample_shift_cost.csv"
        df = pd.read_csv(sample_file)
        st.success("✓ サンプルデータ(40行)をロードしました")
    else:
        uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.success(f"✓ {len(df)}行のシフトデータをロードしました")
        else:
            st.info("CSVを選択してください")
            st.stop()

    # 月間売上入力
    monthly_sales = st.number_input(
        "月間売上（円）",
        value=1500000,
        step=100000,
        format="%d"
    )

    st.divider()
    st.markdown("**CSVフォーマット**")
    st.code("date,staff_name,role,start_time,end_time,hourly_rate,break_minutes")

# ========== メイン処理 ==========
try:
    # 必須列チェック
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"❌ 必須列が不足しています: {', '.join(missing)}")
        st.stop()

    # analyze関数実行
    result = analyze(df, monthly_sales=monthly_sales)

    # ========== KPIカード ==========
    st.subheader("📊 主要指標")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "月間人件費",
            f"¥{result['total_cost']:,.0f}",
            delta=f"{result['monthly_sales']-result['total_cost']:,.0f}利益"
        )

    with col2:
        st.metric("総労働時間", f"{result['total_hours']:.1f}h")

    with col3:
        ratio_display = f"{result['labor_ratio']:.1f}%"
        st.metric("人件費率", ratio_display)

    with col4:
        verdict_emoji = {"good": "✅", "warning": "⚠️", "alert": "🚨"}
        verdict_text = {"good": "良好", "warning": "注意", "alert": "危険"}
        st.metric(
            "判定",
            f"{verdict_emoji[result['verdict']]} {verdict_text[result['verdict']]}"
        )

    st.divider()

    # ========== グラフ ==========
    col_graph1, col_graph2 = st.columns(2)

    # 日次人件費推移
    with col_graph1:
        st.subheader("📈 日次人件費推移")
        daily_df = result["daily_df"].sort_values("date")
        fig_daily = px.line(
            daily_df,
            x="date",
            y="daily_cost",
            title="",
            markers=True,
            labels={"date": "日付", "daily_cost": "人件費（円）"}
        )
        fig_daily.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_daily, use_container_width=True)

    # スタッフ別コスト
    with col_graph2:
        st.subheader("👥 スタッフ別人件費")
        staff_df = result["staff_df"]
        fig_staff = px.bar(
            staff_df,
            x="staff_name",
            y="total_cost",
            title="",
            labels={"staff_name": "スタッフ名", "total_cost": "合計人件費（円）"}
        )
        fig_staff.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_staff, use_container_width=True)

    col_graph3, col_graph4 = st.columns(2)

    # 役割別時間（円グラフ）
    with col_graph3:
        st.subheader("⏱️ 役割別労働時間")
        role_df = result["role_df"]
        fig_role_time = px.pie(
            role_df,
            names="role",
            values="total_hours",
            title="",
            labels={"role": "役割"}
        )
        fig_role_time.update_layout(height=300)
        st.plotly_chart(fig_role_time, use_container_width=True)

    # 役割別コスト（円グラフ）
    with col_graph4:
        st.subheader("💰 役割別人件費")
        fig_role_cost = px.pie(
            role_df,
            names="role",
            values="total_cost",
            title="",
            labels={"role": "役割"}
        )
        fig_role_cost.update_layout(height=300)
        st.plotly_chart(fig_role_cost, use_container_width=True)

    st.divider()

    # ========== 詳細テーブル ==========
    st.subheader("📋 シフト詳細")

    # ソートとフィルタの設定
    col_filter1, col_filter2, col_filter3 = st.columns(3)

    with col_filter1:
        selected_staff = st.multiselect(
            "スタッフフィルタ",
            sorted(result["df"]["staff_name"].unique()),
            default=sorted(result["df"]["staff_name"].unique())
        )

    with col_filter2:
        selected_role = st.multiselect(
            "役割フィルタ",
            sorted(result["df"]["role"].unique()),
            default=sorted(result["df"]["role"].unique())
        )

    with col_filter3:
        sort_by = st.selectbox(
            "ソート順",
            ["日付", "スタッフ", "人件費（高）", "人件費（低）", "労働時間（多）"]
        )

    # フィルタリング
    filtered_df = result["df"][
        (result["df"]["staff_name"].isin(selected_staff)) &
        (result["df"]["role"].isin(selected_role))
    ].copy()

    # ソート
    if sort_by == "日付":
        filtered_df = filtered_df.sort_values("date")
    elif sort_by == "スタッフ":
        filtered_df = filtered_df.sort_values("staff_name")
    elif sort_by == "人件費（高）":
        filtered_df = filtered_df.sort_values("cost", ascending=False)
    elif sort_by == "人件費（低）":
        filtered_df = filtered_df.sort_values("cost")
    elif sort_by == "労働時間（多）":
        filtered_df = filtered_df.sort_values("work_hours", ascending=False)

    # 表示列の整形
    display_df = filtered_df[[
        "date", "staff_name", "role", "start_time", "end_time",
        "work_hours", "hourly_rate", "cost"
    ]].copy()

    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    display_df["work_hours"] = display_df["work_hours"].round(2)
    display_df["cost"] = display_df["cost"].round(0).astype(int)

    display_df = display_df.rename(columns={
        "date": "日付",
        "staff_name": "スタッフ名",
        "role": "役割",
        "start_time": "開始",
        "end_time": "終了",
        "work_hours": "実働時間",
        "hourly_rate": "時給",
        "cost": "人件費"
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ========== スタッフ別サマリー ==========
    st.subheader("👥 スタッフ別サマリー")

    staff_summary = result["staff_df"].copy()
    staff_summary["total_hours"] = staff_summary["total_hours"].round(2)
    staff_summary["total_cost"] = staff_summary["total_cost"].round(0).astype(int)

    staff_summary = staff_summary.rename(columns={
        "staff_name": "スタッフ名",
        "total_hours": "総労働時間",
        "total_cost": "総人件費",
        "shift_count": "シフト数"
    })

    st.dataframe(staff_summary, use_container_width=True, hide_index=True)

    # ========== 役割別サマリー ==========
    st.subheader("🏢 役割別サマリー")

    role_summary = result["role_df"].copy()
    role_summary["total_hours"] = role_summary["total_hours"].round(2)
    role_summary["total_cost"] = role_summary["total_cost"].round(0).astype(int)

    role_summary = role_summary.rename(columns={
        "role": "役割",
        "total_hours": "総労働時間",
        "total_cost": "総人件費"
    })

    st.dataframe(role_summary, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"❌ エラーが発生しました: {str(e)}")
