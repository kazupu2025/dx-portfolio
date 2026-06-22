"""検査員別 検査数・不良検出率・精度レポート — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG     = "#f5f7fa"
_NAVY   = "#1e3a5f"
_GREEN  = "#16a34a"
_RED    = "#dc2626"
_AMBER  = "#d97706"
_PALETTE = ["#1e3a5f","#16a34a","#d97706","#dc2626","#7c3aed","#0891b2"]

def inspector_rate_chart(result_df: pd.DataFrame) -> go.Figure:
    """検査員別 不良検出率 月次折れ線グラフ。"""
    months     = sorted(result_df["month"].unique())
    inspectors = sorted(result_df["inspector"].unique())
    fig = go.Figure()
    for i, insp in enumerate(inspectors):
        sub = result_df[result_df["inspector"] == insp].groupby("month")[["inspected","defects"]].sum()
        rates = [(sub.loc[m,"defects"] / sub.loc[m,"inspected"] * 100) if m in sub.index else 0
                 for m in months]
        fig.add_trace(go.Scatter(x=months, y=rates, mode="lines+markers", name=insp,
                                 line=dict(color=_PALETTE[i % len(_PALETTE)], width=2),
                                 marker=dict(size=8)))
    fig.add_hline(y=3.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="3.0%（good）", annotation_position="right")
    fig.add_hline(y=1.0, line_dash="dash", line_color=_RED,
                  annotation_text="1.0%（alert）", annotation_position="right")
    fig.update_layout(title="検査員別 不良検出率 月次推移",
                      xaxis_title="年月", yaxis=dict(title="不良検出率（%）", range=[0, None]),
                      height=380, plot_bgcolor=_BG, paper_bgcolor=_BG,
                      legend=dict(orientation="h", y=-0.25))
    return fig

def inspector_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """検査員別 不良検出率 横棒グラフ（降順）。"""
    insp_stats = result_df.groupby("inspector")[["inspected","defects"]].sum()
    insp_stats["rate"] = insp_stats["defects"] / insp_stats["inspected"] * 100
    insp_stats = insp_stats.sort_values("rate", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=insp_stats["rate"].values, y=insp_stats.index, orientation="h",
                         marker_color=_NAVY,
                         text=[f"{v:.2f}%" for v in insp_stats["rate"].values],
                         textposition="outside"))
    fig.update_layout(title="検査員別 不良検出率",
                      xaxis=dict(title="不良検出率（%）", range=[0,None]),
                      yaxis_title="検査員", height=300,
                      plot_bgcolor=_BG, paper_bgcolor=_BG, showlegend=False)
    return fig
