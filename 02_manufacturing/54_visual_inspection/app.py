import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import io
import plotly.graph_objects as go
from inspector import inspect

st.set_page_config(page_title="C-108 AI外観検査", layout="wide")
st.title("🔍 AI外観検査自動判定")
st.caption("PIL + ルールベース解析による外観不良検出")

with st.sidebar:
    st.header("検査設定")
    uploaded = st.file_uploader("検査画像をアップロード", type=["jpg","jpeg","png","bmp"])
    use_sample = st.radio("サンプル画像", ["正常品", "不良品（傷）", "不良品（汚れ）"])
    run_btn = st.button("🔍 検査実行", use_container_width=True)

def make_sample(kind):
    """サンプル画像を生成"""
    arr = np.ones((256,256,3), dtype=np.uint8) * 180
    if kind == "不良品（傷）":
        for i in range(0, 256, 4):
            arr[i, :] = [20,20,20]
            arr[:, i] = [20,20,20]
    elif kind == "不良品（汚れ）":
        arr[:80, :80] = [30,30,30]
        arr[180:, 180:] = [20,20,20]
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

if run_btn or uploaded:
    if uploaded:
        img_bytes = uploaded.read()
    else:
        img_bytes = make_sample(use_sample)

    result = inspect(img_bytes)
    img = Image.open(io.BytesIO(img_bytes)).resize((256,256))

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(img, caption="検査画像", use_column_width=True)

    with col2:
        verdict = result["verdict"]
        if verdict == "合格":
            st.success(f"## ✅ {verdict}")
        else:
            st.error(f"## ❌ {verdict}")

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("輝度", f"{result['brightness']:.3f}")
        c2.metric("エッジ密度", f"{result['edge_density']:.3f}")
        c3.metric("暗領域率", f"{result['dark_ratio']:.3f}")
        c4.metric("色分散", f"{result['color_variance']:.1f}")

        if result["defects"]:
            st.warning("検出された不良:")
            for d in result["defects"]:
                st.write(f"  - {d}")

        # スコアゲージ
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=result["defect_score"] * 100,
            title={"text": "不良スコア (%)"},
            gauge={"axis": {"range": [0,100]},
                   "bar": {"color": "red" if result["defect_score"] > 0.3 else "green"},
                   "steps": [{"range":[0,30],"color":"lightgreen"},
                             {"range":[30,60],"color":"lightyellow"},
                             {"range":[60,100],"color":"lightcoral"}]},
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("左サイドバーから画像をアップロードするか、サンプル画像を選択して「検査実行」ボタンを押してください。")
