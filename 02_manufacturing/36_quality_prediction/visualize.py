"""品質予測モデル — Plotly チャート。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_BG = "#f5f7fa"
_NAVY = "#1e3a5f"
_GREEN = "#16a34a"
_RED = "#dc2626"


def feature_importance_chart(feature_importances: pd.DataFrame) -> go.Figure:
    """特徴量重要度 横棒グラフ。

    Args:
        feature_importances: feature/importance 列を持つ DataFrame

    Returns:
        Plotly Figure
    """
    df = feature_importances.sort_values("importance")
    fig = go.Figure(go.Bar(
        x=df["importance"],
        y=df["feature"],
        orientation="h",
        marker_color=_NAVY,
        text=[f"{v:.3f}" for v in df["importance"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="特徴量重要度（Feature Importance）",
        xaxis_title="重要度",
        yaxis_title="特徴量",
        height=max(300, len(df) * 50 + 100),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
    )
    return fig


def classification_report_chart(cr: dict) -> go.Figure:
    """クラス別精度指標（precision/recall/f1-score）棒グラフ。

    Args:
        cr: sklearn.metrics.classification_report(output_dict=True) の出力

    Returns:
        Plotly Figure
    """
    classes = [k for k in cr.keys() if k not in ("accuracy", "macro avg", "weighted avg")]
    metrics = ["precision", "recall", "f1-score"]
    colors = [_NAVY, _GREEN, "#d97706"]
    fig = go.Figure()
    for m, c in zip(metrics, colors):
        vals = [cr[cls][m] for cls in classes]
        fig.add_trace(go.Bar(name=m, x=classes, y=vals, marker_color=c))
    fig.update_layout(
        barmode="group",
        title="クラス別 精度指標",
        xaxis_title="クラス",
        yaxis_title="スコア",
        yaxis_range=[0, 1.1],
        height=340,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig
