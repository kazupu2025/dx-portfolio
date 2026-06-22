"""品質予測モデル — 工程パラメータ → 最終検査合否 ML予測。"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import analyze
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="品質予測モデル", page_icon="🤖", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)

st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px">'
    '<h3 style="margin:0;font-family:BIZ UDGothic">🤖 品質予測モデル（工程パラメータ → 合否予測）</h3>'
    '</div>',
    unsafe_allow_html=True
)

# ============ Sidebar Setup ============
with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: 工程パラメータ列（複数可）+ result列（pass/fail）")
    uploaded = st.file_uploader("学習用 CSVアップロード", type=["csv"])
    use_sample = st.button("サンプルデータを使用", use_container_width=True)

    if uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)
    elif use_sample:
        st.session_state["df"] = generate_sample_csv()

    df = st.session_state.get("df")
    run_btn = False
    if df is not None:
        run_btn = st.button("▶ モデル学習・評価", type="primary", use_container_width=True)

# ============ Check if data is loaded ============
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

# ============ Run analysis if button clicked ============
if run_btn:
    with st.spinner("モデル学習中..."):
        try:
            result = analyze.run_analysis(df)
            st.session_state.update({
                "result": result,
                "uploaded_name": uploaded.name if uploaded else "sample_quality_prediction.csv",
                "row_count": len(df)
            })
        except ValueError as e:
            st.error(str(e))
            st.stop()

    # Try to write to DB
    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "quality_prediction",
            st.session_state.get("uploaded_name"),
            st.session_state.get("row_count")
        )
        write_kpi(
            uid,
            "quality_prediction",
            datetime.now().strftime("%Y-%m"),
            "accuracy",
            float(st.session_state["result"]["accuracy"]),
            st.session_state["result"]["verdict"]
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")

# ============ Display results ============
result = st.session_state.get("result")
if not result:
    st.info("「▶ モデル学習・評価」を押してください。")
    st.stop()

acc = result["accuracy"]
n = result["n_samples"]
nf = result["n_features"]
vd = result["verdict"]
_C = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_L = {"good": "予測精度良好", "warning": "要改善", "alert": "精度不足"}
vc, vl = _C[vd], _L[vd]

# ============ Metrics Row ============
c1, c2, c3, c4 = st.columns(4)
c1.metric("予測精度", f"{acc:.1f}%")
c2.metric("学習サンプル数", f"{n}件")
c3.metric("特徴量数", f"{nf}個")
c4.markdown(
    f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{vc};font-size:16px">{vl}</b><br>'
    f'<span style="font-size:12px;color:#64748b">精度 {acc:.1f}%</span>'
    f'</div>',
    unsafe_allow_html=True
)

# ============ Charts Row ============
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.feature_importance_chart(result["feature_importances"]),
        use_container_width=True
    )
with col_r:
    st.plotly_chart(
        visualize.classification_report_chart(result["classification_report"]),
        use_container_width=True
    )

# ============ Feature Importance Table ============
st.subheader("特徴量重要度詳細")
st.dataframe(result["feature_importances"], use_container_width=True)

# ============ Prediction Interface ============
st.divider()
st.subheader("🔮 新規データ予測")
feature_cols = [c for c in df.columns if c != "result"]
input_vals = {}
cols = st.columns(len(feature_cols))
for i, col in enumerate(feature_cols):
    with cols[i]:
        input_vals[col] = st.number_input(
            col,
            value=float(df[col].mean()),
            format="%.2f"
        )

if st.button("予測実行", type="secondary"):
    X_new = np.array([[input_vals[c] for c in feature_cols]])
    pred = result["model"].predict(X_new)[0]
    prob = result["model"].predict_proba(X_new)[0]
    classes = result["model"].classes_
    prob_dict = dict(zip(classes, prob))
    color = "#16a34a" if pred == "pass" else "#dc2626"
    prob_text = " / ".join([f"{k}: {v:.1%}" for k, v in prob_dict.items()])
    st.markdown(
        f'<div style="background:{color}22;border-left:4px solid {color};padding:12px;border-radius:4px">'
        f'<b style="color:{color};font-size:20px">予測結果: {pred.upper()}</b><br>'
        f'確率: {prob_text}'
        f'</div>',
        unsafe_allow_html=True
    )
