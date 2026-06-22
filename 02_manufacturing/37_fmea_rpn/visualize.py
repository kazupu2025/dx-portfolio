"""FMEA RPN — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG   = "#f5f7fa"
_RED  = "#dc2626"
_AMB  = "#d97706"
_GRN  = "#16a34a"
_NAVY = "#1e3a5f"


def _rpn_color(rpn: int) -> str:
    if rpn > 200: return _RED
    elif rpn > 100: return _AMB
    return _GRN


def rpn_bar_chart(df: pd.DataFrame) -> go.Figure:
    """RPN 降順棒グラフ（高リスクを赤で強調）。"""
    df_sorted = df.sort_values("rpn", ascending=True)
    labels  = df_sorted["failure_mode"].tolist()
    rpn_vals = df_sorted["rpn"].tolist()
    colors  = [_rpn_color(v) for v in rpn_vals]

    fig = go.Figure(go.Bar(
        y=labels, x=rpn_vals, orientation="h",
        marker_color=colors,
        text=rpn_vals, textposition="outside",
    ))
    fig.add_vline(x=200, line_dash="dash", line_color=_RED, annotation_text="高リスク")
    fig.add_vline(x=100, line_dash="dash", line_color=_AMB, annotation_text="要注意")
    fig.update_layout(
        title="故障モード別 RPN（Risk Priority Number）",
        xaxis_title="RPN", yaxis_title="故障モード",
        height=max(320, len(df) * 40 + 100),
        plot_bgcolor=_BG, paper_bgcolor=_BG,
    )
    return fig


def severity_scatter(df: pd.DataFrame) -> go.Figure:
    """重大度 × 発生頻度 散布図（バブルサイズ=RPN）。"""
    fig = go.Figure(go.Scatter(
        x=df["occurrence"], y=df["severity"],
        mode="markers+text",
        marker=dict(
            size=[r/10 for r in df["rpn"]],
            color=df["rpn"],
            colorscale="RdYlGn_r",
            showscale=True,
            colorbar=dict(title="RPN"),
        ),
        text=df["failure_mode"],
        textposition="top center",
    ))
    fig.update_layout(
        title="重大度 × 発生頻度 リスクマップ（バブル=RPN）",
        xaxis=dict(title="発生頻度 (O)", range=[0, 11]),
        yaxis=dict(title="重大度 (S)", range=[0, 11]),
        height=380, plot_bgcolor=_BG, paper_bgcolor=_BG,
    )
    return fig
