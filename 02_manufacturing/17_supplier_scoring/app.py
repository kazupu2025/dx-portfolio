# -*- coding: utf-8 -*-
"""
B-86: 製造 サプライヤー品質スコアリングダッシュボード
重み付き合成スコア × 仕入先ランク評価
スタンドアロン版（ローカルモジュール依存を排除）
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path

try:
    import plotly.express as px
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

BASE_DIR = Path(__file__).resolve().parent

# ── サンプルデータ生成（インライン） ────────────────────────────
def generate_b86_sample() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    suppliers = [f"SUP-{i:03d}" for i in range(1, 21)]
    rows = []
    for s in suppliers:
        rows.append({
            "supplier_id":     s,
            "defect_rate":     round(float(rng.uniform(0.01, 0.12)), 4),
            "delivery_rate":   round(float(rng.uniform(0.70, 1.00)), 4),
            "price_variance":  round(float(rng.uniform(-0.15, 0.20)), 4),
        })
    return pd.DataFrame(rows)


# ── スコアリングロジック（インライン） ──────────────────────────
def run_b86_analysis(df: pd.DataFrame) -> dict:
    required = {"supplier_id", "defect_rate", "delivery_rate", "price_variance"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"必要な列が不足しています: {missing}")

    scored = df.copy()
    # 各指標を 0-100 点に変換
    scored["defect_score"]   = (1.0 - scored["defect_rate"].clip(0, 1)) * 100
    scored["delivery_score"] = scored["delivery_rate"].clip(0, 1) * 100
    scored["price_score"]    = (1.0 - scored["price_variance"].abs().clip(0, 1)) * 100

    # 重み付き合成スコア（不良率 50% / 納期 30% / 価格偏差 20%）
    scored["composite_score"] = (
        0.50 * scored["defect_score"]
        + 0.30 * scored["delivery_score"]
        + 0.20 * scored["price_score"]
    ).round(2)

    # 仕入先判定
    def _verdict(s):
        if s >= 70:
            return "good"
        elif s >= 50:
            return "warning"
        return "alert"

    scored["verdict"] = scored["composite_score"].apply(_verdict)

    avg_score     = float(scored["composite_score"].mean())
    best_supplier = scored.loc[scored["composite_score"].idxmax(), "supplier_id"]
    n_suppliers   = len(scored)

    # 全体判定
    good_ratio = (scored["verdict"] == "good").mean()
    if good_ratio >= 0.6:
        overall_verdict = "good"
    elif good_ratio >= 0.3:
        overall_verdict = "warning"
    else:
        overall_verdict = "alert"

    return {
        "scored_df":       scored,
        "avg_score":       avg_score,
        "best_supplier":   best_supplier,
        "n_suppliers":     n_suppliers,
        "verdict":         overall_verdict,
    }


# ── チャート（インライン） ──────────────────────────────────────
def _b86_score_bar(scored_df: pd.DataFrame):
    df_sorted = scored_df.sort_values("composite_score", ascending=False)
    color_map = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
    colors = [color_map.get(v, "#64748b") for v in df_sorted["verdict"]]
    fig = go.Figure()
    fig.add_bar(
        x=df_sorted["supplier_id"],
        y=df_sorted["composite_score"],
        marker_color=colors,
        name="合成スコア",
    )
    fig.add_hline(y=70, line_dash="dash", line_color="#16a34a",
                  annotation_text="優良ライン(70pt)")
    fig.add_hline(y=50, line_dash="dash", line_color="#d97706",
                  annotation_text="要改善ライン(50pt)")
    fig.update_layout(title="仕入先別 合成スコア",
                      xaxis_title="仕入先", yaxis_title="合成スコア（点）",
                      yaxis=dict(range=[0, 105]), height=380)
    return fig


def _b86_breakdown_chart(scored_df: pd.DataFrame):
    df_sorted = scored_df.sort_values("composite_score", ascending=False).head(10)
    fig = go.Figure()
    fig.add_bar(x=df_sorted["supplier_id"], y=df_sorted["defect_score"],
                name="不良スコア (×0.5)", marker_color="#ef4444", opacity=0.8)
    fig.add_bar(x=df_sorted["supplier_id"], y=df_sorted["delivery_score"],
                name="納期スコア (×0.3)", marker_color="#3b82f6", opacity=0.8)
    fig.add_bar(x=df_sorted["supplier_id"], y=df_sorted["price_score"],
                name="価格スコア (×0.2)", marker_color="#f59e0b", opacity=0.8)
    fig.update_layout(barmode="group", title="スコア内訳 上位10社",
                      xaxis_title="仕入先", yaxis_title="スコア（点）",
                      height=380)
    return fig


# ── UI ─────────────────────────────────────────────────────────
st.title("🏭 B-86 サプライヤー品質スコアリング")
st.caption("B-86 | 製造 × 調達管理 | 重み付き合成スコア（不良率50%・納期30%・価格偏差20%）× 仕入先ランク")

for key in ["b86_df", "b86_result"]:
    if key not in st.session_state:
        st.session_state[key] = None

with st.sidebar:
    st.header("⚙ 設定")
    st.caption("重み: 不良率 50% / 納期 30% / 価格偏差 20%")
    if st.button("サンプルデータを使用", use_container_width=True, key="b86_sample_btn"):
        st.session_state.b86_df = generate_b86_sample()
    uploaded = st.file_uploader("CSVアップロード", type=["csv"], key="b86_upload")
    if uploaded:
        try:
            st.session_state.b86_df = pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            st.session_state.b86_df = pd.read_csv(uploaded, encoding="shift_jis")

    df = st.session_state.b86_df
    run_btn = False
    if df is not None:
        st.caption(f"読込: {len(df)} 行")
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True,
                             key="b86_run")

df = st.session_state.b86_df
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.markdown("""
**必須列（列名は完全一致）:**
- `supplier_id` — 仕入先コード/名称
- `defect_rate` — 不良率（0.0〜1.0）
- `delivery_rate` — 納期遵守率（0.0〜1.0）
- `price_variance` — 価格偏差率（マイナス=安い、プラス=高い）
""")
    st.stop()

if run_btn:
    try:
        result = run_b86_analysis(df)
        st.session_state.b86_result = result
    except (ValueError, KeyError) as e:
        st.error(str(e))

result = st.session_state.b86_result
if result is None:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI 4列 ────────────────────────────────────────────────────
avg_score     = result["avg_score"]
best_supplier = result["best_supplier"]
verdict       = result["verdict"]
scored_df     = result["scored_df"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "優良仕入先多数", "warning": "改善余地あり", "alert": "取引見直し検討"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

best_score = float(
    scored_df.loc[scored_df["supplier_id"] == best_supplier, "composite_score"].iloc[0]
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("仕入先数", f"{result['n_suppliers']}社")
c2.metric("平均合成スコア", f"{avg_score:.1f}点")
c3.metric("最優良仕入先", best_supplier, delta=f"{best_score:.1f}点")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">avg={avg_score:.1f}点</span>'
    f'</div>',
    unsafe_allow_html=True,
)

st.divider()

# ── チャート ───────────────────────────────────────────────────
if _HAS_PLOTLY:
    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(_b86_score_bar(scored_df), use_container_width=True)
    with col_r:
        st.plotly_chart(_b86_breakdown_chart(scored_df), use_container_width=True)
else:
    st.subheader("合成スコア（Plotly未インストール）")
    st.bar_chart(
        scored_df.set_index("supplier_id")["composite_score"].sort_values(ascending=False)
    )

# ── スコア詳細テーブル ────────────────────────────────────────
st.subheader("仕入先別スコア詳細")
display_cols = [
    "supplier_id", "defect_rate", "delivery_rate", "price_variance",
    "defect_score", "delivery_score", "price_score", "composite_score", "verdict",
]
display_df = scored_df[display_cols].sort_values("composite_score", ascending=False).reset_index(drop=True)

# 日本語ラベルにリネーム
display_df = display_df.rename(columns={
    "supplier_id": "仕入先", "defect_rate": "不良率",
    "delivery_rate": "納期遵守率", "price_variance": "価格偏差",
    "defect_score": "不良スコア", "delivery_score": "納期スコア",
    "price_score": "価格スコア", "composite_score": "合成スコア",
    "verdict": "判定",
})
display_df["判定"] = display_df["判定"].map(
    {"good": "✅ 優良", "warning": "⚠️ 要改善", "alert": "❌ 要見直し"}
)
st.dataframe(display_df, hide_index=True, use_container_width=True)

# ── ランク別集計 ──────────────────────────────────────────────
st.subheader("ランク別集計")
rank_counts = scored_df["verdict"].value_counts().rename(
    {"good": "✅ 優良", "warning": "⚠️ 要改善", "alert": "❌ 要見直し"}
)
st.bar_chart(rank_counts)
