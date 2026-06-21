"""統合品質ダッシュボード — C-61/C-62 の結果を横断表示"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from _common.db_writer import init_db
from db_reader import get_latest_kpis, get_kpi_trend, get_latest_cpk

st.set_page_config(
    page_title="品質横断ダッシュボード",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f5f7fa; }
[data-testid="stHeader"] { background-color: #f5f7fa; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── カード定義 ──────────────────────────────────────────────────
CARDS = [
    {"system_id": "defect_rate", "metric": "defect_rate",
     "title": "月次不良率",      "fmt": lambda v: f"{v*100:.2f}%"},
    {"system_id": "claim",       "metric": "claim_count",
     "title": "クレーム件数",    "fmt": lambda v: f"{int(v)}件"},
    {"system_id": "yield",       "metric": "yield_rate",
     "title": "歩留まり率",      "fmt": lambda v: f"{v*100:.1f}%"},
    {"system_id": "cpk",         "metric": "min_cpk",
     "title": "最悪工程 Cpk",   "fmt": lambda v: f"{v:.2f}"},
    {"system_id": "inspector",   "metric": "avg_detection_rate",
     "title": "検査員検出率",    "fmt": lambda v: f"{v*100:.1f}%"},
    {"system_id": "lot",         "metric": "pass_rate",
     "title": "ロット合否率",    "fmt": lambda v: f"{v*100:.1f}%"},
    {"system_id": "spc",         "metric": "out_of_control_pct",
     "title": "SPC 管理逸脱率", "fmt": lambda v: f"{v:.1f}%"},
    {"system_id": "msa",         "metric": "grr_pct",
     "title": "ゲージR&R（%GRR）", "fmt": lambda v: f"{v:.1f}%"},
    {"system_id": "4m_change",   "metric": "p_value",
     "title": "4M変更有意差（p値）", "fmt": lambda v: f"{v:.4f}"},
    {"system_id": "defect_pareto", "metric": "top_mode_pct",
     "title": "最多不良モード構成比", "fmt": lambda v: f"{v:.1f}%"},
    {"system_id": "corrective_action", "metric": "p_value",
     "title": "是正処置効果（p値）", "fmt": lambda v: f"{v:.4f}"},
    {"system_id": "process_correlation", "metric": "max_r",
     "title": "工程間最強相関（r）", "fmt": lambda v: f"{v:.3f}"},
    {"system_id": "quality_cost_roi", "metric": "roi",
     "title": "品質コストROI", "fmt": lambda v: f"{v:.2f}x"},
    {"system_id": "supplier_scoring", "metric": "avg_score",
     "title": "仕入先平均スコア", "fmt": lambda v: f"{v:.1f}点"},
    {"system_id": "aql_sampling", "metric": "acceptance",
     "title": "直近ロット合否", "fmt": lambda v: "合格" if v >= 1.0 else "不合格"},
]

VERDICT_STYLE: dict[str, dict] = {
    "good":    {"bg": "#dcfce7", "color": "#16a34a", "icon": "✓"},
    "warning": {"bg": "#fff7ed", "color": "#d97706", "icon": "△"},
    "alert":   {"bg": "#fef2f2", "color": "#dc2626", "icon": "✗"},
    "no_data": {"bg": "#f1f5f9", "color": "#94a3b8", "icon": "—"},
}


def _card_html(title: str, value_str: str, verdict: str) -> str:
    s = VERDICT_STYLE[verdict]
    return (
        f'<div style="background:{s["bg"]};border-radius:8px;padding:14px 10px;'
        f'text-align:center;min-height:90px">'
        f'<div style="font-size:11px;color:#64748b;margin-bottom:6px">{title}</div>'
        f'<div style="font-size:22px;font-weight:700;color:{s["color"]}">{value_str}</div>'
        f'<div style="font-size:16px;color:{s["color"]};margin-top:2px">{s["icon"]}</div>'
        f'</div>'
    )


# ── ヘッダー ───────────────────────────────────────────────────
st.markdown(
    '<div style="background:#1e3a5f;padding:16px 24px;border-radius:8px;margin-bottom:20px">'
    '<h2 style="color:white;margin:0;font-size:20px">📊 品質横断ダッシュボード</h2>'
    '</div>',
    unsafe_allow_html=True,
)

init_db()

kpis = get_latest_kpis()
kpi_map = {(r["system_id"], r["metric_name"]): r for r in kpis}

if not kpis:
    st.info(
        "まだデータがありません。\n\n"
        "C-62 で分析を実行するか、C-61 ポータルでパイプラインを実行してください。"
    )

# ── KPI カード ────────────────────────────────────────────────
cols = st.columns(len(CARDS))
for i, card in enumerate(CARDS):
    data = kpi_map.get((card["system_id"], card["metric"]))
    verdict = data["verdict"] if data else "no_data"
    value_str = card["fmt"](data["value"]) if data else "—"
    with cols[i]:
        st.markdown(_card_html(card["title"], value_str, verdict), unsafe_allow_html=True)

st.markdown("---")

# ── トレンドセクション ─────────────────────────────────────────
col_sel, col_chart = st.columns([1, 3])

with col_sel:
    st.markdown("**表示設定**")
    months = st.radio("期間", [3, 6, 12], format_func=lambda x: f"直近 {x} ヶ月", index=0)
    selected_title = st.radio(
        "KPI を選択",
        [c["title"] for c in CARDS],
        index=0,
    )

with col_chart:
    card = next(c for c in CARDS if c["title"] == selected_title)
    trend = get_kpi_trend(card["system_id"], card["metric"], months=months)

    if not trend:
        st.info(f"「{selected_title}」のデータがまだ蓄積されていません。")
    else:
        trend_sorted = sorted(trend, key=lambda x: x["year_month"])
        colors = [VERDICT_STYLE.get(r["verdict"], VERDICT_STYLE["no_data"])["color"]
                  for r in trend_sorted]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[r["year_month"] for r in trend_sorted],
            y=[r["value"] for r in trend_sorted],
            mode="lines+markers",
            line=dict(color="#1e3a5f", width=2),
            marker=dict(size=9, color=colors),
        ))
        fig.update_layout(
            title=dict(text=f"{selected_title} — 月次推移", font=dict(size=14)),
            plot_bgcolor="#f5f7fa",
            paper_bgcolor="white",
            height=320,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(title=""),
            yaxis=dict(title=""),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── 直近 Cpk テーブル ──────────────────────────────────────────
cpk_data = get_latest_cpk()
if cpk_data:
    st.markdown("---")
    st.markdown("### 直近 Cp/Cpk 一覧")
    df = pd.DataFrame(cpk_data)[["process", "cp", "cpk", "verdict", "out_of_spec_pct", "n"]]
    df.columns = ["工程", "Cp", "Cpk", "判定", "規格外%", "n"]
    st.dataframe(df, use_container_width=True, hide_index=True)
