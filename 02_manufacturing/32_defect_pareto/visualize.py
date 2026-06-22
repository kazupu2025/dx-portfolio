"""不良モード別パレート × 時系列複合分析 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_BG      = "#f5f7fa"
_NAVY    = "#1e3a5f"
_RED     = "#dc2626"
_GREEN   = "#16a34a"
_PALETTE = ["#1e3a5f","#16a34a","#d97706","#dc2626","#7c3aed","#0891b2","#be185d"]


def pareto_chart(pareto_df: pd.DataFrame) -> go.Figure:
    """パレート図（棒グラフ + 累積折れ線、2軸）。"""
    modes   = pareto_df["defect_mode"].tolist()
    totals  = pareto_df["total"].tolist()
    cumpcts = pareto_df["cumulative_pct"].tolist()
    bar_colors = [_NAVY if f else "#94a3b8" for f in pareto_df["pareto_flag"].tolist()]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=modes, y=totals, marker_color=bar_colors, name="件数"), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=modes, y=cumpcts, mode="lines+markers+text",
        line=dict(color=_RED, width=2), marker=dict(size=8),
        text=[f"{v:.1f}%" for v in cumpcts], textposition="top center",
        name="累積%",
    ), secondary_y=True)
    fig.add_hline(y=80.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="80%", secondary_y=True)
    fig.update_yaxes(title_text="件数", secondary_y=False)
    fig.update_yaxes(title_text="累積%", range=[0, 115], secondary_y=True)
    fig.update_layout(
        title="不良モード別パレート図（80%ルール）",
        xaxis_title="不良モード", height=380,
        plot_bgcolor=_BG, paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def trend_chart(trend_df: pd.DataFrame) -> go.Figure:
    """不良モード別 月次推移 積み上げ棒グラフ。"""
    months = trend_df.index.tolist()
    fig = go.Figure()
    for i, col in enumerate(trend_df.columns):
        fig.add_trace(go.Bar(x=months, y=trend_df[col].tolist(), name=col,
                             marker_color=_PALETTE[i % len(_PALETTE)]))
    fig.update_layout(
        barmode="stack", title="不良モード別 月次推移",
        xaxis_title="年月", yaxis_title="件数",
        height=340, plot_bgcolor=_BG, paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig
