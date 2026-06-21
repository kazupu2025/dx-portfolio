"""品質コスト明細集計（4分類）— Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_BG = "#f5f7fa"

_CAT_COLOR = {
    "予防コスト":    "#16a34a",
    "評価コスト":    "#0891b2",
    "内部損失コスト": "#d97706",
    "外部損失コスト": "#dc2626",
}
_DEFAULT_COLOR = "#1e3a5f"

_CATEGORY_ORDER = ["予防コスト", "評価コスト", "内部損失コスト", "外部損失コスト"]


def monthly_cost_chart(result_df: pd.DataFrame) -> go.Figure:
    """月次 × 4分類 の積み上げ棒グラフ。

    result_df must contain columns: month, category, amount.
    """
    months = sorted(result_df["month"].unique())

    pivot = (
        result_df.groupby(["month", "category"])["amount"]
        .sum()
        .reset_index()
        .pivot(index="month", columns="category", values="amount")
        .reindex(months)
        .fillna(0)
    )

    fig = go.Figure()
    for cat in _CATEGORY_ORDER:
        if cat not in pivot.columns:
            continue
        fig.add_trace(go.Bar(
            x=months,
            y=pivot[cat].tolist(),
            name=cat,
            marker_color=_CAT_COLOR.get(cat, _DEFAULT_COLOR),
        ))

    fig.update_layout(
        barmode="stack",
        title="品質コスト月次推移（4分類）",
        xaxis_title="年月",
        yaxis_title="コスト（円）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
        yaxis=dict(tickformat=","),
    )
    return fig


def category_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """分類別 総コスト 横棒グラフ（金額降順）。

    result_df must contain columns: category, amount.
    """
    cat_totals = (
        result_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=True)
    )

    colors = [_CAT_COLOR.get(str(cat), _DEFAULT_COLOR) for cat in cat_totals.index]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat_totals.values,
        y=cat_totals.index,
        orientation="h",
        marker_color=colors,
        text=[f"¥{int(v):,}" for v in cat_totals.values],
        textposition="outside",
    ))
    fig.update_layout(
        title="分類別 品質コスト合計",
        xaxis=dict(title="コスト（円）", tickformat=",", range=[0, None]),
        yaxis_title="分類",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
