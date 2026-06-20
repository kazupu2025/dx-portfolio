"""ゲージR&R 分析結果の Plotly 描画モジュール。"""
from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd

_NAVY    = "#1e3a5f"
_ALERT   = "#dc2626"
_GREEN   = "#16a34a"
_WARNING = "#d97706"
_BG      = "#f5f7fa"
_FONT    = "BIZ UDGothic"
_OP_COLORS = ["#1e3a5f", "#16a34a", "#d97706", "#7c3aed", "#0891b2"]


def cov_chart(result: dict) -> go.Figure:
    """Components of Variation 棒グラフ（%GRR / %EV / %AV / %Int / %PV）。"""
    categories = ["%GRR", "%EV", "%AV", "%Int", "%PV"]
    values = [
        result["grr_pct"], result["ev_pct"], result["av_pct"],
        result["int_pct"], result["pv_pct"],
    ]
    colors = [_ALERT if v > 30 else _WARNING if v > 10 else _GREEN for v in values]

    fig = go.Figure(go.Bar(
        x=categories, y=values, marker_color=colors,
        text=[f"{v:.1f}%" for v in values], textposition="outside",
    ))
    for y_val, lbl, color in [
        (10, "10% (good境界)",  _GREEN),
        (30, "30% (alert境界)", _ALERT),
    ]:
        fig.add_hline(
            y=y_val, line_dash="dash", line_color=color, line_width=1.2,
            annotation_text=lbl, annotation_position="right",
            annotation_font_size=10,
        )
    fig.update_layout(
        title=dict(text="変動成分の割合（Components of Variation）", font=dict(size=14, color=_NAVY)),
        yaxis_title="割合 (%)",
        yaxis_range=[0, max(max(values) * 1.15, 35)],
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG, paper_bgcolor=_BG,
        height=280, margin=dict(l=60, r=90, t=40, b=40),
        showlegend=False,
    )
    return fig


def scatter_chart(
    df: pd.DataFrame, part_col: str, operator_col: str, value_col: str
) -> go.Figure:
    """部品 × 測定値の散布図（作業者別色分け）。"""
    operators = df[operator_col].unique()
    fig = go.Figure()
    for idx, op in enumerate(operators):
        sub = df[df[operator_col] == op]
        color = _OP_COLORS[idx % len(_OP_COLORS)]
        fig.add_trace(go.Scatter(
            x=sub[part_col].astype(str).tolist(),
            y=sub[value_col].tolist(),
            mode="markers",
            marker=dict(color=color, size=7, opacity=0.8),
            name=str(op),
        ))
    fig.update_layout(
        title=dict(text="部品別測定値（作業者別色分け）", font=dict(size=14, color=_NAVY)),
        xaxis_title="部品", yaxis_title="測定値",
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG, paper_bgcolor=_BG,
        height=300, margin=dict(l=60, r=90, t=40, b=40),
    )
    return fig


def xbar_chart(
    df: pd.DataFrame, part_col: str, operator_col: str, value_col: str
) -> go.Figure:
    """作業者別 部品平均値折れ線グラフ（再現性の可視化）。"""
    operators = df[operator_col].unique()
    parts     = df[part_col].unique()
    fig = go.Figure()
    for idx, op in enumerate(operators):
        sub   = df[df[operator_col] == op]
        means = sub.groupby(part_col, sort=False)[value_col].mean()
        color = _OP_COLORS[idx % len(_OP_COLORS)]
        fig.add_trace(go.Scatter(
            x=[str(p) for p in parts],
            y=[float(means.get(p, float("nan"))) for p in parts],
            mode="lines+markers",
            line=dict(color=color, width=1.5),
            marker=dict(color=color, size=7),
            name=str(op),
        ))
    fig.update_layout(
        title=dict(text="作業者別 部品平均値（再現性確認）", font=dict(size=14, color=_NAVY)),
        xaxis_title="部品", yaxis_title="平均測定値",
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG, paper_bgcolor=_BG,
        height=280, margin=dict(l=60, r=90, t=40, b=40),
    )
    return fig
