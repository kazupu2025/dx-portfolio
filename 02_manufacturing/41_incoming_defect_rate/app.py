import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
# ── analyze.py インライン（Streamlit Cloud 互換）──
import pandas as pd

REQUIRED_COLUMNS = ["date", "supplier", "inspection_count", "defect_count"]

def analyze(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["defect_rate"] = df["defect_count"] / df["inspection_count"] * 100

    supplier_df = df.groupby("supplier").agg(
        total_inspection=("inspection_count", "sum"),
        total_defect=("defect_count", "sum"),
    ).reset_index()
    supplier_df["defect_rate"] = supplier_df["total_defect"] / supplier_df["total_inspection"] * 100

    df["month"] = df["date"].dt.to_period("M").astype(str)
    trend_df = df.groupby("month").agg(
        total_inspection=("inspection_count", "sum"),
        total_defect=("defect_count", "sum"),
    ).reset_index()
    trend_df["defect_rate"] = trend_df["total_defect"] / trend_df["total_inspection"] * 100

    avg_defect_rate = supplier_df["defect_rate"].mean()

    if avg_defect_rate <= 1.0:
        verdict = "good"
    elif avg_defect_rate <= 3.0:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "supplier_df": supplier_df,
        "trend_df": trend_df,
        "avg_defect_rate": avg_defect_rate,
        "worst_supplier": supplier_df.loc[supplier_df["defect_rate"].idxmax(), "supplier"],
        "verdict": verdict,
    }

# ────────────────────────────────────────────────

st.title("C-95 協力会社別受入不良率月報")

# サイドバー
with st.sidebar:
    st.header("データ入力")

    # サンプルデータボタン
    if st.button("📊 サンプルデータを読み込む"):
        sample_path = Path(__file__).parent / "sample_incoming_defect.csv"
        df = pd.read_csv(sample_path)
        st.session_state.data = df
        st.success("サンプルデータを読み込みました")

    # CSVアップロード
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        # カラム検証
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            st.error(f"必須カラムが不足しています: {', '.join(missing_cols)}")
        else:
            st.session_state.data = df
            st.success("ファイルを読み込みました")

# データ処理
if "data" not in st.session_state:
    sample_path = Path(__file__).parent / "sample_incoming_defect.csv"
    st.session_state.data = pd.read_csv(sample_path)

df = st.session_state.data

try:
    result = analyze(df)

    # KPIカード
    st.subheader("主要指標")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("平均不良率 (%)", f"{result['avg_defect_rate']:.2f}%")

    with col2:
        st.metric("最悪サプライヤー", result['worst_supplier'])

    with col3:
        verdict_display = {
            "good": "🟢 良好",
            "warning": "🟡 要注意",
            "alert": "🔴 警告"
        }
        st.metric("判定", verdict_display.get(result['verdict'], result['verdict']))

    # 仕入先別棒グラフ
    st.subheader("仕入先別不良率")
    supplier_chart = px.bar(
        result["supplier_df"],
        x="supplier",
        y="defect_rate",
        title="各サプライヤーの不良率",
        labels={"supplier": "サプライヤー", "defect_rate": "不良率 (%)"},
        color="defect_rate",
        color_continuous_scale="RdYlGn_r"
    )
    supplier_chart.update_layout(height=400)
    st.plotly_chart(supplier_chart, use_container_width=True)

    # 月次トレンド折れ線グラフ
    st.subheader("月次トレンド")
    trend_chart = px.line(
        result["trend_df"],
        x="month",
        y="defect_rate",
        title="月別不良率推移",
        labels={"month": "月", "defect_rate": "不良率 (%)"},
        markers=True
    )
    trend_chart.update_layout(height=400)
    st.plotly_chart(trend_chart, use_container_width=True)

    # 詳細テーブル
    st.subheader("詳細データ")
    st.dataframe(result["supplier_df"], use_container_width=True)

except Exception as e:
    st.error(f"エラーが発生しました: {str(e)}")
