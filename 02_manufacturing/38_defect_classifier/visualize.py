"""不良原因自動分類 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG      = "#f5f7fa"
_PALETTE = ["#1e3a5f", "#16a34a", "#d97706", "#dc2626", "#7c3aed"]


def category_pie_chart(category_counts: dict) -> go.Figure:
    """カテゴリ分布ドーナツグラフ。"""
    labels = list(category_counts.keys())
    values = list(category_counts.values())
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=_PALETTE[:len(labels)],
        hole=0.3,
    ))
    fig.update_layout(
        title="不良カテゴリ分布", height=340,
        plot_bgcolor=_BG, paper_bgcolor=_BG,
    )
    return fig


def category_bar_chart(category_counts: dict) -> go.Figure:
    """カテゴリ別件数棒グラフ。"""
    sorted_items = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    cats = [i[0] for i in sorted_items]
    vals = [i[1] for i in sorted_items]
    fig = go.Figure(go.Bar(
        x=cats, y=vals, marker_color=_PALETTE[:len(cats)],
        text=vals, textposition="outside",
    ))
    fig.update_layout(
        title="カテゴリ別 件数", xaxis_title="カテゴリ", yaxis_title="件数",
        height=320, plot_bgcolor=_BG, paper_bgcolor=_BG,
    )
    return fig
