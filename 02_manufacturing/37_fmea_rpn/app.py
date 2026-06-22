"""FMEA RPN動的更新システム — SQLite CRUD + RPN自動計算。"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import db, analyze, visualize

db.init_db()
db.seed_sample_data()

st.set_page_config(page_title="FMEA RPN動的更新", page_icon="⚠", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""", unsafe_allow_html=True)
st.markdown('<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px"><h3 style="margin:0;font-family:BIZ UDGothic">⚠ FMEA RPN 動的更新システム</h3></div>', unsafe_allow_html=True)

df = db.get_all_items()
result = analyze.run_analysis(df)

avg_rpn = result["avg_rpn"]
max_rpn = result["max_rpn"]
hrc     = result["high_risk_count"]
vd      = result["verdict"]
_C = {"good":"#16a34a","warning":"#d97706","alert":"#dc2626"}
_L = {"good":"リスク低","warning":"要注意","alert":"高リスク"}
vc, vl = _C[vd], _L[vd]

c1,c2,c3,c4 = st.columns(4)
c1.metric("平均RPN", f"{avg_rpn:.0f}")
c2.metric("最大RPN", f"{max_rpn}")
c3.metric("高リスク件数(>200)", f"{hrc}件")
c4.markdown(f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px"><b style="color:{vc};font-size:16px">{vl}</b></div>', unsafe_allow_html=True)

tab_list, tab_add, tab_edit = st.tabs(["📋 一覧・分析", "➕ 新規登録", "✏️ 更新・削除"])

with tab_list:
    if len(df) > 0:
        col_l, col_r = st.columns(2)
        with col_l:
            st.plotly_chart(visualize.rpn_bar_chart(df), use_container_width=True)
        with col_r:
            st.plotly_chart(visualize.severity_scatter(df), use_container_width=True)
        display_cols = ["id","process_name","failure_mode","severity","occurrence","detection","rpn","action_required"]
        st.dataframe(df[display_cols], use_container_width=True)
    else:
        st.info("FMEA 項目がありません。「新規登録」タブから追加してください。")

with tab_add:
    with st.form("add_form"):
        st.subheader("FMEA 新規項目登録")
        col1, col2 = st.columns(2)
        with col1:
            pn  = st.text_input("工程名 *", placeholder="例: 溶接工程")
            fm  = st.text_input("故障モード *", placeholder="例: 溶接強度不足")
            eff = st.text_input("影響 *", placeholder="例: 製品強度低下")
            cau = st.text_input("原因 *", placeholder="例: 溶接電流の変動")
        with col2:
            sev = st.slider("重大度 S (1-10)", 1, 10, 5)
            occ = st.slider("発生頻度 O (1-10)", 1, 10, 3)
            det = st.slider("検出難度 D (1-10)", 1, 10, 3)
            st.metric("RPN (S×O×D)", sev * occ * det)
        ctrl = st.text_input("現行管理方法", placeholder="例: 目視検査")
        act  = st.text_input("推奨処置", placeholder="例: センサー導入")
        submitted = st.form_submit_button("登録", type="primary", use_container_width=True)
        if submitted:
            if not (pn and fm and eff and cau):
                st.error("必須項目（*）を入力してください。")
            else:
                db.add_item(pn, fm, eff, sev, cau, occ, det, ctrl, act)
                st.success("登録しました。一覧タブを更新してください。")
                try:
                    from _common.db_writer import init_db as _idb, write_upload, write_kpi
                    _idb()
                    uid = write_upload("fmea_rpn", "form_input", 1)
                    new_result = analyze.run_analysis(db.get_all_items())
                    write_kpi(uid, "fmea_rpn", datetime.now().strftime("%Y-%m"),
                              "avg_rpn", float(new_result["avg_rpn"]),
                              new_result["verdict"])
                except Exception:
                    pass

with tab_edit:
    if len(df) == 0:
        st.info("編集対象の項目がありません。")
    else:
        st.subheader("項目の更新・削除")
        item_id = st.selectbox("対象 ID を選択", df["id"].tolist(),
                               format_func=lambda x: f"ID:{x} — {df[df['id']==x]['failure_mode'].values[0]}")
        row = df[df["id"] == item_id].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            sev2 = st.slider("重大度 S", 1, 10, int(row["severity"]), key="s2")
            occ2 = st.slider("発生頻度 O", 1, 10, int(row["occurrence"]), key="o2")
            det2 = st.slider("検出難度 D", 1, 10, int(row["detection"]), key="d2")
            st.metric("新 RPN", sev2 * occ2 * det2, delta=sev2*occ2*det2 - int(row["rpn"]))
        with col2:
            ctrl2 = st.text_input("現行管理方法", value=str(row["current_control"]), key="c2")
            act2  = st.text_input("推奨処置", value=str(row["action_required"]), key="a2")
        col_upd, col_del = st.columns(2)
        with col_upd:
            if st.button("更新", type="primary", use_container_width=True):
                db.update_item(item_id, sev2, occ2, det2, ctrl2, act2)
                st.success("更新しました。")
        with col_del:
            if st.button("削除", type="secondary", use_container_width=True):
                db.delete_item(item_id)
                st.warning("削除しました。")
