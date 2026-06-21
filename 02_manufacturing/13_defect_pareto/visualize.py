"""不良モード別パレート × 時系列複合分析 Plotly 描画モジュール。"""
from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

_NAVY    = "#1e3a5f"
_ALERT   = "#dc2626"
_GREEN   = "#16a34a"
_WARNING = "#d97706"
_BG      = "#f5f7fa"
_FONT    = "BIZ UDGothic"
_COLORS  = [_NAVY, _ALERT, _GREEN, _WARNING, "#7c3aed"]


def pareto_chart(
    pareto_df: pd.DataFrame,
    mode_col: str,
    vital_few: list[str],
) -> go.Figure:
    """
    パレート図: 降順棒グラフ + 累積% 折れ線（secondary_y）+ 80% 閾値線。
    vital few のモードは alert 色（それ以外は navy）。

    Note: make_subplots の secondary_y に add_hline は使えない。
    80% ラインは Scatter トレースとして secondary_y に追加する。
    """
    modes     = pareto_df[mode_col].tolist()
    counts    = pareto_df["count"].tolist()
    cum_pct   = pareto_df["cumulative_pct"].tolist()
    bar_colors = [_ALERT if m in vital_few else _NAVY for m in modes]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=modes, y=counts, marker_color=bar_colors,
            name="件数", text=counts, textposition="outside",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=modes, y=cum_pct, mode="lines+markers",
            line=dict(color=_WARNING, width=2),
            marker=dict(size=7, color=_WARNING),
            name="累積%",
        ),
        secondary_y=True,
    )
    # 80% 閾値線（secondary_y Scatter として追加）
    fig.add_trace(
        go.Scatter(
            x=modes, y=[80.0] * len(modes),
            mode="lines",
            line=dict(color=_ALERT, width=1.2, dash="dash"),
            name="80%閾値", showlegend=False,
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=dict(text="不良モード別パレート図", font=dict(size=14, color=_NAVY)),
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG, paper_bgcolor=_BG,
        height=350, margin=dict(l=60, r=90, t=40, b=40),
        legend=dict(orientation="h", y=1.12),
        showlegend=True,
    )
    fig.update_yaxes(title_text="件数", secondary_y=False)
    fig.update_yaxes(title_text="累積 (%)", secondary_y=True, range=[0, 110])
    return fig


def trend_chart(trend_df: pd.DataFrame) -> go.Figure:
    """月別不良モード推移折れ線グラフ（最大5モード、パレート降順）。"""
    fig  = go.Figure()
    cols = trend_df.columns.tolist()[:5]

    for i, col in enumerate(cols):
        fig.add_trace(go.Scatter(
            x=trend_df.index.tolist(),
            y=trend_df[col].tolist(),
            mode="lines+markers",
            name=str(col),
            line=dict(color=_COLORS[i % len(_COLORS)], width=2),
            marker=dict(size=7),
        ))

    fig.update_layout(
        title=dict(text="不良モード別 月次推移", font=dict(size=14, color=_NAVY)),
        xaxis_title="年月", yaxis_title="件数",
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG, paper_bgcolor=_BG,
        height=300, margin=dict(l=60, r=90, t=40, b=40),
        legend=dict(orientation="h", y=1.15),
    )
    return fig
