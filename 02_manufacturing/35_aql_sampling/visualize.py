"""AQL/受入サンプリング計画最適化 — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG      = "#f5f7fa"
_NAVY    = "#1e3a5f"
_GREEN   = "#16a34a"
_AMBER   = "#d97706"
_RED     = "#dc2626"
_PALETTE = ["#1e3a5f", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2"]


def oc_curve_chart(result_df: pd.DataFrame, oc_curves: list[dict]) -> go.Figure:
    """検査計画ごとの OC 曲線（横軸: 不良率%, 縦軸: 合格確率 Pa）。"""
    fig = go.Figure()
    for i, (_, row) in enumerate(result_df.iterrows()):
        oc = oc_curves[i]
        label = f"lot={int(row['lot_size'])} n={int(row['sample_size'])} c={int(row['acceptance_number'])}"
        fig.add_trace(go.Scatter(
            x=[p * 100 for p in oc["p_range"]],
            y=oc["pa_values"],
            mode="lines",
            name=label,
            line=dict(color=_PALETTE[i % len(_PALETTE)], width=2),
        ))
    # AQL 垂直線（代表値）
    if len(result_df) > 0:
        aql = float(result_df["aql_pct"].iloc[0])
        fig.add_vline(
            x=aql,
            line_dash="dash",
            line_color=_RED,
            annotation_text=f"AQL={aql}%",
            annotation_position="top right",
        )
    fig.add_hline(
        y=0.95,
        line_dash="dot",
        line_color="#94a3b8",
        annotation_text="Pa=0.95",
        annotation_position="right",
    )
    fig.update_layout(
        title="OC曲線（Operating Characteristic Curve）",
        xaxis_title="不良率（%）",
        yaxis_title="合格確率 Pa",
        yaxis=dict(range=[0, 1.05]),
        height=400,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.3),
    )
    return fig


def protection_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """計画別 protection_score 棒グラフ。"""
    labels = [f"lot={int(row['lot_size'])}" for _, row in result_df.iterrows()]
    scores = result_df["protection_score"].tolist()
    colors = [_GREEN if s >= 0.7 else _AMBER if s >= 0.5 else _RED for s in scores]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=scores,
        marker_color=colors,
        text=[f"{v:.4f}" for v in scores],
        textposition="outside",
        name="保護スコア",
    ))
    fig.update_layout(
        title="計画別 保護スコア（protection_score = Pa_AQL - Pa_RQL）",
        xaxis_title="検査計画（ロットサイズ）",
        yaxis_title="保護スコア",
        yaxis=dict(range=[0, 1.1]),
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
