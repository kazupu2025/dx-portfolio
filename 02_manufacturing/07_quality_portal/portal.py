"""品質管理ポータル — メインアプリ"""
import importlib
import sys
from pathlib import Path

import streamlit as st
import yaml

# Ensure pages/ is importable
sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="品質管理ポータル",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── カスタムCSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* サイドバー背景 */
[data-testid="stSidebar"] {
    background-color: #1e3a5f !important;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
/* ページ背景 */
.main .block-container {
    background-color: #f5f7fa;
    padding-top: 1.5rem;
}
/* ナビボタン（デフォルト） */
div[data-testid="stSidebar"] .stButton > button {
    background-color: transparent !important;
    color: #ffffff !important;
    border: none !important;
    text-align: left !important;
    padding: 10px 16px !important;
    width: 100% !important;
    border-radius: 6px !important;
    font-size: 0.95em !important;
    transition: background-color 0.15s !important;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #2a5298 !important;
}
/* アクティブボタン */
div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: #2a5298 !important;
    font-weight: 700 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── ナビゲーション定義 ────────────────────────────────────────────────────────
PAGES = [
    ("📉", "月次不良率集計", "pages.p1_defect_rate"),
    ("📋", "クレーム件数集計", "pages.p2_claim"),
    ("📈", "歩留まりトレンド", "pages.p3_yield"),
    ("👤", "検査員別実績",    "pages.p4_inspector"),
    ("🗂️", "ロット別合否判定", "pages.p5_lot"),
]

# ── セッション状態 ────────────────────────────────────────────────────────────
if "active_page" not in st.session_state:
    st.session_state.active_page = 0

# ── サイドバー ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<h2 style="margin:0 0 1.5rem 0;font-size:1.2em">🏭 品質管理ポータル</h2>',
        unsafe_allow_html=True,
    )
    for i, (icon, label, _) in enumerate(PAGES):
        is_active = st.session_state.active_page == i
        btn_type = "primary" if is_active else "secondary"
        if st.button(f"{icon} {label}", key=f"nav_{i}", type=btn_type, use_container_width=True):
            st.session_state.active_page = i
            st.rerun()

    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.75em;opacity:0.6;margin:0">DX Portfolio v1.0<br>品質保証部門向け</p>',
        unsafe_allow_html=True,
    )

# ── ページルーティング ─────────────────────────────────────────────────────────
idx = st.session_state.active_page
_, _, module_path = PAGES[idx]

try:
    page_module = importlib.import_module(module_path)
    page_module.show()
except Exception as e:
    st.error(f"ページの読み込みに失敗しました: {e}")
    import traceback
    st.code(traceback.format_exc())
