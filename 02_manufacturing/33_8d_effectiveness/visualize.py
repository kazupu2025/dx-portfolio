"""是正処置（8D）効果検証 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG     = "#f5f7fa"
_GREEN  = "#16a34a"
_AMBER  = "#d97706"
_RED    = "#dc2626"
_NAVY   = "#1e3a5f"
_ALPHA_LINE = 0.05


def effectiveness_bar_chart(result_summary: pd.DataFrame) -> go.Figure:
    """処置別 p値棒グラフ（p=0.05 基準線付き）。有効=green / 無効=amber。"""
    labels  = result_summary["action_id"].tolist()
    p_vals  = result_summary["p_value"].tolist()
    effectives = result_summary["effective"].tolist()
    colors  = [_GREEN if e else _AMBER for e in effectives]
    names   = result_summary["action_name"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=p_vals,
        marker_color=colors,
        text=[f"p={v:.4f}" for v in p_vals],
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            + "<br>".join(f"{n}" for n in names)
            + "<br>p値: %{y:.4f}<extra></extra>"
        ),
        name="p値",
    ))
    fig.add_hline(
        y=ALPHA_LINE,
        line_dash="dash",
        line_color=_RED,
        annotation_text=f"α={ALPHA_LINE}",
        annotation_position="right",
    )
    fig.update_layout(
        title="処置別 p値（Welch t検定）",
        xaxis_title="処置ID",
        yaxis_title="p値",
        yaxis=dict(rangemode="tozero"),
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig


def effect_size_chart(result_summary: pd.DataFrame) -> go.Figure:
    """処置別 Cohen's d 棒グラフ（絶対値）。効果量の大きさを可視化。"""
    labels  = result_summary["action_id"].tolist()
    cohen_d = result_summary["cohen_d"].abs().tolist()
    effectives = result_summary["effective"].tolist()
    colors  = [_GREEN if e else _AMBER for e in effectives]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=cohen_d,
        marker_color=colors,
        text=[f"d={v:.2f}" for v in cohen_d],
        textposition="outside",
        name="Cohen's d（絶対値）",
    ))
    # 効果量の参考線: small=0.2, medium=0.5, large=0.8
    for y_val, label in [(0.2, "小(0.2)"), (0.5, "中(0.5)"), (0.8, "大(0.8)")]:
        fig.add_hline(
            y=y_val,
            line_dash="dot",
            line_color="#94a3b8",
            annotation_text=label,
            annotation_position="right",
        )
    fig.update_layout(
        title="処置別 効果量（Cohen's d 絶対値）",
        xaxis_title="処置ID",
        yaxis_title="Cohen's d（絶対値）",
        yaxis=dict(rangemode="tozero"),
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig


ALPHA_LINE = _ALPHA_LINE
