"""AQL 受入サンプリング計画 — Plotly OC 曲線チャート。"""
from __future__ import annotations

import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_BG    = "#f5f7fa"


def oc_chart(
    oc_p: list[float],
    oc_pa: list[float],
    aql: float,
    alpha: float,
    rql: float,
    beta: float,
) -> go.Figure:
    """OC 曲線（Pa vs 不良率 p）を生産者・消費者リスクマーカー付きで描画する。"""
    p_pct   = [p * 100 for p in oc_p]
    rql_pct = rql * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=p_pct,
        y=list(oc_pa),
        mode="lines",
        line=dict(color=_NAVY, width=2),
        name="合格確率 Pa",
    ))

    fig.add_vline(
        x=aql,
        line_dash="dash",
        line_color=_GREEN,
        annotation_text=f"AQL={aql}%  α={alpha:.1%}",
        annotation_position="top right",
        annotation_font_color=_GREEN,
    )
    fig.add_vline(
        x=rql_pct,
        line_dash="dot",
        line_color=_RED,
        annotation_text=f"RQL={rql_pct:.1f}%  β={beta:.1%}",
        annotation_position="top left",
        annotation_font_color=_RED,
    )

    fig.update_layout(
        title="OC 曲線（Operating Characteristic Curve）",
        xaxis=dict(title="不良率 p（%）", range=[0, 20]),
        yaxis=dict(title="合格確率 Pa", range=[0, 1.05]),
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
