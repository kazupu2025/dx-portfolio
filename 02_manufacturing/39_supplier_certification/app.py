"""サプライヤー品質認定・改善追跡システム。"""
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

import db
import analyze
import visualize

# Initialize DB
db.init_db()
db.seed_sample_data()

# Page Config
st.set_page_config(
    page_title="サプライヤー品質認定", page_icon="🏢", layout="wide"
)
st.markdown(
    """<style>
[data-testid="stAppViewContainer"]{background-color:#f5f7fa;}
[data-testid="stHeader"]{background-color:#f5f7fa;}
.block-container{padding-top:1rem;}
</style>""",
    unsafe_allow_html=True,
)

# Header
st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;border-radius:6px;margin-bottom:16px"><h3 style="margin:0;font-family:BIZ UDGothic">🏢 サプライヤー品質認定・改善追跡システム</h3></div>',
    unsafe_allow_html=True,
)

# Get data
latest_df = db.get_latest_assessments()
all_df = db.get_all_assessments()
result = analyze.run_analysis(latest_df, all_df)

# Metrics
avg = result["avg_total_score"]
cert = result["certified_count"]
ns = result["n_suppliers"]
vd = result["verdict"]
_C = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_L = {"good": "全体良好", "warning": "要注意", "alert": "要改善"}
vc, vl = _C[vd], _L[vd]

c1, c2, c3, c4 = st.columns(4)
c1.metric("平均スコア", f"{avg:.1f}点")
c2.metric("認定サプライヤー", f"{cert}/{ns}社")
c3.metric("評価件数", f"{result['n_assessments']}件")
c4.markdown(
    f'<div style="background:{vc}22;border-left:4px solid {vc};padding:8px 12px;border-radius:4px;margin-top:4px"><b style="color:{vc};font-size:16px">{vl}</b></div>',
    unsafe_allow_html=True,
)

# Tabs
tab_list, tab_assess, tab_add = st.tabs(
    ["📋 認定状況一覧", "➕ 評価登録", "🏢 サプライヤー追加"]
)

with tab_list:
    if len(latest_df) > 0:
        col_l, col_r = st.columns([3, 2])
        with col_l:
            st.plotly_chart(
                visualize.score_bar_chart(latest_df), use_container_width=True
            )
        with col_r:
            sel = st.selectbox("詳細表示", latest_df["name"].tolist())
            row = latest_df[latest_df["name"] == sel].iloc[0]
            st.plotly_chart(
                visualize.radar_chart(row), use_container_width=True
            )
        display_cols = [
            "name",
            "category",
            "period",
            "quality_score",
            "delivery_score",
            "cost_score",
            "total_score",
            "certification",
        ]
        st.dataframe(
            latest_df[[c for c in display_cols if c in latest_df.columns]],
            use_container_width=True,
        )
    else:
        st.info("評価データがありません。")

with tab_assess:
    suppliers_df = db.get_suppliers()
    if len(suppliers_df) == 0:
        st.info("まずサプライヤーを追加してください。")
    else:
        with st.form("assess_form"):
            st.subheader("品質評価登録")
            sup_name = st.selectbox("サプライヤー", suppliers_df["name"].tolist())
            period = st.text_input(
                "評価期間（YYYY-MM）", value=datetime.now().strftime("%Y-%m")
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                q = st.slider("品質スコア(50%)", 0, 100, 80)
            with col2:
                d = st.slider("納期スコア(30%)", 0, 100, 80)
            with col3:
                c = st.slider("コストスコア(20%)", 0, 100, 80)
            total = q * 0.5 + d * 0.3 + c * 0.2
            cert_label = (
                "認定"
                if total >= 80
                else ("条件付認定" if total >= 60 else "保留")
            )
            col_t, col_c = st.columns(2)
            col_t.metric("総合スコア（プレビュー）", f"{total:.1f}点")
            col_c.metric("認定区分", cert_label)
            memo = st.text_area("メモ")
            submitted = st.form_submit_button(
                "評価登録", type="primary", use_container_width=True
            )
            if submitted:
                sup_id = suppliers_df[suppliers_df["name"] == sup_name]["id"].values[
                    0
                ]
                db.add_assessment(sup_id, period, q, d, c, memo)
                st.success(
                    f"{sup_name} の評価を登録しました（スコア: {total:.1f}点 / {cert_label}）"
                )
                # Try to write KPI to unified DB
                try:
                    from _common.db_writer import (
                        init_db as _idb,
                        write_upload,
                        write_kpi,
                    )

                    _idb()
                    uid = write_upload("supplier_cert", "form_input", 1)
                    new_result = analyze.run_analysis(
                        db.get_latest_assessments(), db.get_all_assessments()
                    )
                    write_kpi(
                        uid,
                        "supplier_cert",
                        period,
                        "avg_score",
                        float(new_result["avg_total_score"]),
                        new_result["verdict"],
                    )
                except Exception:
                    pass

with tab_add:
    with st.form("add_supplier_form"):
        st.subheader("サプライヤー新規登録")
        name = st.text_input("社名 *")
        cat = st.selectbox("カテゴリ", ["材料", "部品", "加工", "サービス"])
        contact = st.text_input("担当者・連絡先")
        if st.form_submit_button("登録", type="primary", use_container_width=True):
            if not name:
                st.error("社名を入力してください。")
            else:
                try:
                    db.add_supplier(name, cat, contact)
                    st.success(f"{name} を登録しました。")
                except Exception as e:
                    st.error(f"登録エラー: {e}")
