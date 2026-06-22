"""品質コストROI分析 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG      = "#f5f7fa"
_NAVY    = "#1e3a5f"
_GREEN   = "#16a34a"
_AMBER   = "#d97706"
_RED     = "#dc2626"
_BLUE    = "#2563eb"
_PALETTE = {
    "prevention_cost":  "#1e3a5f",
    "appraisal_cost":   "#2563eb",
    "internal_failure": "#d97706",
    "external_failure": "#dc2626",
}


def cost_trend_chart(result_df: pd.DataFrame) -> go.Figure:
    """月次コスト積み上げ棒グラフ（prevention/appraisal/internal/external 4分類）。"""
    months = result_df["month"].tolist()
    fig = go.Figure()
    labels = {
        "prevention_cost":  "予防コスト",
        "appraisal_cost":   "評価コスト",
        "internal_failure": "内部失敗コスト",
        "external_failure": "外部失敗コスト",
    }
    for col, label in labels.items():
        fig.add_trace(go.Bar(
            x=months,
            y=result_df[col].tolist(),
            name=label,
            marker_color=_PALETTE[col],
        ))
    fig.update_layout(
        barmode="stack",
        title="月次 品質コスト内訳（積み上げ棒グラフ）",
        xaxis_title="年月",
        yaxis_title="コスト（万円）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def failure_ratio_chart(result_df: pd.DataFrame) -> go.Figure:
    """失敗コスト比率 月次折れ線グラフ（改善トレンド確認）。"""
    months = result_df["month"].tolist()
    ratios = result_df["failure_ratio"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months,
        y=ratios,
        mode="lines+markers+text",
        line=dict(color=_RED, width=2),
        marker=dict(size=8, color=_RED),
        text=[f"{v:.1f}%" for v in ratios],
        textposition="top center",
        name="失敗コスト比率",
    ))
    fig.update_layout(
        title="失敗コスト比率 月次推移",
        xaxis_title="年月",
        yaxis_title="失敗コスト比率（%）",
        yaxis=dict(rangemode="tozero"),
        height=360,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
