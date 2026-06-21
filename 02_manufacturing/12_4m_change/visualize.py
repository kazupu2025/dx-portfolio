"""4M変更前後品質比較 Plotly 描画モジュール。"""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go

_NAVY    = "#1e3a5f"
_ALERT   = "#dc2626"
_GREEN   = "#16a34a"
_WARNING = "#d97706"
_BG      = "#f5f7fa"
_FONT    = "BIZ UDGothic"


def hist_chart(
    before: np.ndarray,
    after: np.ndarray,
    before_label: str = "変更前",
    after_label: str  = "変更後",
) -> go.Figure:
    """半透明ヒストグラム重ね（before=navy, after=alert red）。"""
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=before,
        name=before_label,
        opacity=0.6,
        marker_color=_NAVY,
        nbinsx=15,
    ))
    fig.add_trace(go.Histogram(
        x=after,
        name=after_label,
        opacity=0.6,
        marker_color=_ALERT,
        nbinsx=15,
    ))
    fig.update_layout(
        barmode="overlay",
        title=dict(text="分布比較（ヒストグラム重ね）", font=dict(size=14, color=_NAVY)),
        xaxis_title="測定値",
        yaxis_title="度数",
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=300,
        margin=dict(l=50, r=30, t=40, b=40),
        legend=dict(orientation="h", y=1.1),
    )
    return fig


def box_chart(
    before: np.ndarray,
    after: np.ndarray,
    before_label: str = "変更前",
    after_label: str  = "変更後",
) -> go.Figure:
    """箱ひげ図（前後並列）— 中央値・IQR・外れ値を表示。"""
    fig = go.Figure()
    fig.add_trace(go.Box(
        y=before,
        name=before_label,
        marker_color=_NAVY,
        boxpoints="outliers",
        line_width=1.5,
    ))
    fig.add_trace(go.Box(
        y=after,
        name=after_label,
        marker_color=_ALERT,
        boxpoints="outliers",
        line_width=1.5,
    ))
    fig.update_layout(
        title=dict(text="前後比較（箱ひげ図）", font=dict(size=14, color=_NAVY)),
        yaxis_title="測定値",
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=300,
        margin=dict(l=50, r=30, t=40, b=40),
        showlegend=False,
    )
    return fig
