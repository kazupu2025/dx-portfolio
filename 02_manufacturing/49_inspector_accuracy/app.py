import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
# ── analyze.py インライン（Streamlit Cloud 互換）──
import pandas as pd

REQUIRED_COLUMNS = ["date", "inspector", "inspected", "defects_found", "true_defects"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["detection_rate"] = df["defects_found"] / df["true_defects"].clip(lower=1) * 100
    df["miss_count"] = df["true_defects"] - df["defects_found"]

    inspector_df = df.groupby("inspector").agg(
        total_inspected=("inspected", "sum"),
        total_found=("defects_found", "sum"),
        total_true=("true_defects", "sum"),
        avg_detection_rate=("detection_rate", "mean"),
    ).reset_index()
    inspector_df["detection_rate"] = inspector_df["total_found"] / inspector_df["total_true"].clip(lower=1) * 100

    avg_detection_rate = float(inspector_df["detection_rate"].mean())
    worst_inspector = inspector_df.loc[inspector_df["detection_rate"].idxmin(), "inspector"]

    if avg_detection_rate >= 95:
        verdict = "good"
    elif avg_detection_rate >= 85:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "inspector_df": inspector_df,
        "avg_detection_rate": avg_detection_rate,
        "worst_inspector": worst_inspector,
        "total_miss": int(df["miss_count"].sum()),
        "verdict": verdict,
    }

# ────────────────────────────────────────────────

st.title("C-103 検査員別 検査数・不良検出率・精度レポート")

# サイドバー
with st.sidebar:
    st.header("データ入力")

    uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")

    if st.button("サンプルデータを読み込む"):
        sample_path = Path(__file__).parent / "sample_inspector_accuracy.csv"
        uploaded_file = sample_path

    if uploaded_file is not None:
        if isinstance(uploaded_file, Path):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        # バリデーション
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            st.error(f"必須列が不足しています: {', '.join(missing)}")
            st.stop()

        # 分析実行
        result = analyze(df)

        # KPIカード表示
        st.subheader("KPI")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均検出率", f"{result['avg_detection_rate']:.1f}%")
        with col2:
            st.metric("最低検出員", result['worst_inspector'])
        with col3:
            st.metric("見逃し総数", f"{result['total_miss']} 件")
        with col4:
            verdict_color = {"good": "green", "warning": "orange", "alert": "red"}
            verdict_label = {"good": "良好", "warning": "注意", "alert": "警告"}
            st.metric("判定", verdict_label[result['verdict']])

        # グラフ：検査員別 不良検出率
        st.subheader("検査員別 不良検出率")
        inspector_df_sorted = result['inspector_df'].sort_values('detection_rate', ascending=False)
        fig = px.bar(
            inspector_df_sorted,
            x='inspector',
            y='detection_rate',
            color='detection_rate',
            color_continuous_scale='RdYlGn',
            range_color=[75, 100],
            title="",
            labels={'inspector': '検査員', 'detection_rate': '検出率（%）'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        # 詳細テーブル
        st.subheader("検査員別 詳細")
        display_df = result['inspector_df'].copy()
        display_df['detection_rate'] = display_df['detection_rate'].round(1)
        display_df = display_df.sort_values('detection_rate', ascending=False)
        display_df.columns = ['検査員', '検査数', '見つけた不良', '実際の不良', '平均検出率（個別記録）', '検出率（集計）']
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("サイドバーからCSVをアップロード、またはサンプルデータボタンをクリックしてください。")
