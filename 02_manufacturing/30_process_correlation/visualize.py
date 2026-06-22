"""工程間品質相関分析 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG    = "#f5f7fa"
_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_AMBER = "#d97706"


def correlation_bar_chart(target_corr: pd.DataFrame) -> go.Figure:
    """defect_rateとの相関係数 棒グラフ（絶対値で色分け）。"""
    params = target_corr["parameter"].tolist()
    corrs  = target_corr["correlation"].tolist()
    pvals  = target_corr["p_value"].tolist()
    colors = []
    for r, p in zip(corrs, pvals):
        if p < 0.05 and abs(r) >= 0.7:
            colors.append(_GREEN)
        elif p < 0.05:
            colors.append(_AMBER)
        else:
            colors.append("#94a3b8")  # gray

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=params, y=corrs, marker_color=colors,
        text=[f"r={r:.3f}<br>p={p:.3f}" for r, p in zip(corrs, pvals)],
        textposition="outside",
    ))
    fig.add_hline(y=0.7,  line_dash="dash", line_color=_GREEN, annotation_text="+0.7", annotation_position="right")
    fig.add_hline(y=-0.7, line_dash="dash", line_color=_GREEN, annotation_text="-0.7", annotation_position="right")
    fig.add_hline(y=0.4,  line_dash="dot",  line_color=_AMBER, annotation_text="+0.4", annotation_position="right")
    fig.add_hline(y=-0.4, line_dash="dot",  line_color=_AMBER, annotation_text="-0.4", annotation_position="right")
    fig.update_layout(
        title="工程パラメータと不良率の相関係数",
        xaxis_title="パラメータ", yaxis=dict(title="相関係数 r", range=[-1.1, 1.1]),
        height=360, plot_bgcolor=_BG, paper_bgcolor=_BG, showlegend=False,
    )
    return fig


def scatter_chart(result_df: pd.DataFrame, param: str, target: str = "defect_rate") -> go.Figure:
    """最強相関パラメータ vs 不良率 散布図。"""
    import numpy as np
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=result_df[param], y=result_df[target],
        mode="markers+text",
        marker=dict(size=10, color=_NAVY),
        text=result_df.get("month", [""]*len(result_df)),
        textposition="top center",
    ))
    # 回帰直線
    x_arr = result_df[param].to_numpy(dtype=float)
    y_arr = result_df[target].to_numpy(dtype=float)
    if len(x_arr) >= 2:
        m, b = np.polyfit(x_arr, y_arr, 1)
        x_line = [float(x_arr.min()), float(x_arr.max())]
        y_line = [m * xi + b for xi in x_line]
        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines",
                                 line=dict(color=_RED, dash="dash"), name="回帰直線"))
    fig.update_layout(
        title=f"{param} vs {target} 散布図",
        xaxis_title=param, yaxis_title=target,
        height=340, plot_bgcolor=_BG, paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
