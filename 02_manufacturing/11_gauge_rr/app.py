# -*- coding: utf-8 -*-
"""
B-88: 製造 ゲージR&R（MSA）測定システム解析ダッシュボード
2因子交差 ANOVA による繰り返し性（EV）・再現性（AV）・部品変動（PV）の分散成分推定
スタンドアロン版（ローカルモジュール依存を排除）
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path

try:
    import plotly.graph_objects as go
    import plotly.express as px
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

BASE_DIR = Path(__file__).resolve().parent


# ── サンプルデータ生成（インライン） ────────────────────────────
def generate_b88_sample() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    parts     = [f"P{i:02d}" for i in range(1, 11)]   # 10部品
    operators = ["山田", "鈴木", "田中"]                  # 3作業者
    rows = []
    part_true = {p: rng.normal(50.0, 2.0) for p in parts}
    for part in parts:
        for op in operators:
            for rep in range(1, 3):  # 2回繰り返し
                meas = part_true[part] + rng.normal(0, 0.5) + rng.normal(0, 0.2)
                rows.append({"part": part, "operator": op,
                              "rep": rep, "measurement": round(float(meas), 4)})
    return pd.DataFrame(rows)


# ── GRR ANOVA（インライン）─────────────────────────────────────
def run_b88_grr(df: pd.DataFrame, value_col: str,
                part_col: str, op_col: str) -> dict:
    df = df.copy()
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[value_col, part_col, op_col])

    parts = sorted(df[part_col].unique())
    ops   = sorted(df[op_col].unique())
    p = len(parts)
    o = len(ops)

    # レプリケーション数（各 part×operator セルの平均）
    cell_means = df.groupby([part_col, op_col])[value_col].agg(["mean", "count"])
    r = int(cell_means["count"].mode().iloc[0])  # 最頻値をレプリケーション数とする
    if r < 2:
        raise ValueError("各セル（部品×作業者）に2回以上の測定が必要です。")
    if p < 2:
        raise ValueError("部品が2種類以上必要です。")
    if o < 2:
        raise ValueError("作業者が2名以上必要です。")

    grand_mean = df[value_col].mean()

    # SS_part
    part_means = df.groupby(part_col)[value_col].mean()
    ss_part = o * r * float(((part_means - grand_mean) ** 2).sum())
    df_part = p - 1

    # SS_op
    op_means = df.groupby(op_col)[value_col].mean()
    ss_op = p * r * float(((op_means - grand_mean) ** 2).sum())
    df_op = o - 1

    # SS_interaction (part × operator)
    ss_interaction = 0.0
    for pt in parts:
        for ot in ops:
            cell_m = df[(df[part_col] == pt) & (df[op_col] == ot)][value_col].mean()
            ss_interaction += (cell_m - part_means[pt] - op_means[ot] + grand_mean) ** 2
    ss_interaction *= r
    df_interaction = (p - 1) * (o - 1)

    # SS_total and SS_error
    ss_total = float(((df[value_col] - grand_mean) ** 2).sum())
    ss_error = ss_total - ss_part - ss_op - ss_interaction
    df_error = p * o * (r - 1)
    if df_error <= 0:
        df_error = max(1, int(len(df) - p * o))

    ss_error = max(ss_error, 0.0)

    ms_part   = ss_part   / df_part        if df_part > 0        else 0.0
    ms_op     = ss_op     / df_op          if df_op > 0          else 0.0
    ms_inter  = ss_interaction / df_interaction if df_interaction > 0 else 0.0
    ms_error  = ss_error  / df_error       if df_error > 0        else 0.0

    # F 統計量
    f_part  = ms_part  / ms_inter  if ms_inter  > 0 else float("nan")
    f_op    = ms_op    / ms_inter  if ms_inter  > 0 else float("nan")
    f_inter = ms_inter / ms_error  if ms_error  > 0 else float("nan")

    # 分散成分推定（AIAG GRR 標準手法）
    var_error = ms_error                                           # σ²_e = EV
    var_inter = max(0.0, (ms_inter - ms_error) / r)               # σ²_op×part
    var_op    = max(0.0, (ms_op    - ms_inter) / (p * r))         # σ²_op = AV
    var_part  = max(0.0, (ms_part  - ms_inter) / (o * r))         # σ²_p  = PV

    var_grr   = var_error + var_op                                 # GRR
    var_total = var_grr   + var_part                               # TV

    sigma_grr   = float(np.sqrt(max(var_grr,   0.0)))
    sigma_ev    = float(np.sqrt(max(var_error, 0.0)))
    sigma_av    = float(np.sqrt(max(var_op,    0.0)))
    sigma_part  = float(np.sqrt(max(var_part,  0.0)))
    sigma_total = float(np.sqrt(max(var_total, 0.0)))

    grr_pct = (sigma_grr   / sigma_total * 100) if sigma_total > 0 else 0.0
    ev_pct  = (sigma_ev    / sigma_total * 100) if sigma_total > 0 else 0.0
    av_pct  = (sigma_av    / sigma_total * 100) if sigma_total > 0 else 0.0
    pv_pct  = (sigma_part  / sigma_total * 100) if sigma_total > 0 else 0.0
    ndc     = max(1, int(1.41 * sigma_part / sigma_grr)) if sigma_grr > 0 else 0

    anova_table = pd.DataFrame([
        {"要因": "部品間（Parts）",   "SS": ss_part,        "df": df_part,
         "MS": ms_part,  "F": f_part,  "p値": float("nan")},
        {"要因": "作業者間（Operators）","SS": ss_op,       "df": df_op,
         "MS": ms_op,    "F": f_op,    "p値": float("nan")},
        {"要因": "交互作用（Part×Op）","SS": ss_interaction,"df": df_interaction,
         "MS": ms_inter, "F": f_inter, "p値": float("nan")},
        {"要因": "繰り返し誤差（Error）","SS": ss_error,    "df": df_error,
         "MS": ms_error, "F": float("nan"), "p値": float("nan")},
        {"要因": "合計（Total）",     "SS": ss_total,
         "df": df_part+df_op+df_interaction+df_error,
         "MS": float("nan"), "F": float("nan"), "p値": float("nan")},
    ])

    return {
        "grr_pct": grr_pct, "ev_pct": ev_pct, "av_pct": av_pct, "pv_pct": pv_pct,
        "ndc": ndc,
        "sigma_grr": sigma_grr, "sigma_ev": sigma_ev, "sigma_av": sigma_av,
        "sigma_part": sigma_part, "sigma_total": sigma_total,
        "var_error": var_error, "var_op": var_op, "var_part": var_part,
        "anova_table": anova_table,
        "part_means": part_means, "op_means": op_means,
        "grand_mean": grand_mean,
    }


# ── チャート（インライン） ──────────────────────────────────────
def _b88_cov_chart(result: dict):
    labels = ["%EV（繰り返し性）", "%AV（再現性）", "%PV（部品変動）"]
    vals   = [result["ev_pct"], result["av_pct"], result["pv_pct"]]
    colors = ["#ef4444", "#3b82f6", "#22c55e"]
    fig = go.Figure()
    fig.add_bar(x=labels, y=vals, marker_color=colors, name="変動成分(%)")
    fig.add_hline(y=10, line_dash="dash", line_color="#16a34a",
                  annotation_text="合格ライン 10%")
    fig.add_hline(y=30, line_dash="dash", line_color="#dc2626",
                  annotation_text="不合格ライン 30%")
    fig.update_layout(title="変動成分内訳（%Study Variation）",
                      yaxis_title="%", yaxis=dict(range=[0, 110]), height=360)
    return fig


def _b88_scatter_chart(df: pd.DataFrame, part_col: str, op_col: str, value_col: str):
    if not _HAS_PLOTLY:
        return None
    fig = px.scatter(df, x=part_col, y=value_col, color=op_col,
                     title="部品別測定値（作業者別）",
                     labels={part_col: "部品", value_col: "測定値", op_col: "作業者"})
    fig.update_layout(height=350)
    return fig


# ── UI ─────────────────────────────────────────────────────────
st.title("🔬 B-88 ゲージR&R（MSA）測定システム解析")
st.caption("B-88 | 製造 × 品質管理 | 2因子交差ANOVA — 繰り返し性(EV)・再現性(AV)・%GRR算出")

for key in ["b88_df", "b88_result", "b88_part_col", "b88_op_col", "b88_value_col"]:
    if key not in st.session_state:
        st.session_state[key] = None

with st.sidebar:
    st.header("⚙ 設定")
    if st.button("サンプルデータを使用", use_container_width=True, key="b88_sample_btn"):
        st.session_state.b88_df = generate_b88_sample()
    uploaded = st.file_uploader("CSVアップロード", type=["csv"], key="b88_upload")
    if uploaded:
        try:
            st.session_state.b88_df = pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            st.session_state.b88_df = pd.read_csv(uploaded, encoding="shift_jis")

    df = st.session_state.b88_df
    part_col = op_col = value_col = None
    run_btn = False

    if df is not None:
        cols      = df.columns.tolist()
        part_col  = st.selectbox("部品列",   cols, key="b88_part_sel")
        op_col    = st.selectbox("作業者列", cols,
                                  index=min(1, len(cols)-1), key="b88_op_sel")
        value_col = st.selectbox("測定値列", cols,
                                  index=min(3, len(cols)-1), key="b88_val_sel")
        run_btn = st.button("▶ 分析実行", type="primary",
                             use_container_width=True, key="b88_run")

df = st.session_state.b88_df
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.markdown("""
**必須列（列名は自由に指定可）:**
- 部品列 — 部品ID/品番  
- 作業者列 — 測定者名/ID  
- 測定値列 — 実測値（数値）  
- 各セル（部品×作業者）に **2回以上** の繰り返し測定が必要
""")
    st.stop()

if run_btn:
    if not all([part_col, op_col, value_col]):
        st.error("列をすべて選択してください。")
    else:
        try:
            result = run_b88_grr(df, value_col, part_col, op_col)
            st.session_state.b88_result    = result
            st.session_state.b88_part_col  = part_col
            st.session_state.b88_op_col    = op_col
            st.session_state.b88_value_col = value_col
        except ValueError as e:
            st.error(str(e))

result    = st.session_state.b88_result
part_col  = st.session_state.b88_part_col  or part_col
op_col    = st.session_state.b88_op_col    or op_col
value_col = st.session_state.b88_value_col or value_col

if not result:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI 4列 ────────────────────────────────────────────────────
pct     = result["grr_pct"]
v_color = "#16a34a" if pct < 10 else ("#d97706" if pct < 30 else "#dc2626")
v_label = "✅ 合格" if pct < 10 else ("⚠️ 条件付き合格" if pct < 30 else "❌ 不合格")

c1, c2, c3, c4 = st.columns(4)
c1.metric("%GRR",              f"{result['grr_pct']:.1f}%")
c2.metric("%EV（繰り返し性）", f"{result['ev_pct']:.1f}%")
c3.metric("%AV（再現性）",     f"{result['av_pct']:.1f}%")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">ndc = {result["ndc"]}</span></div>',
    unsafe_allow_html=True,
)

st.divider()

# ── チャート ───────────────────────────────────────────────────
if _HAS_PLOTLY:
    st.plotly_chart(_b88_cov_chart(result), use_container_width=True)
    col_l, col_r = st.columns(2)
    with col_l:
        sc = _b88_scatter_chart(df, part_col, op_col, value_col)
        if sc:
            st.plotly_chart(sc, use_container_width=True)
    with col_r:
        op_means_df = result["op_means"].reset_index()
        op_means_df.columns = [op_col, "平均測定値"]
        fig_op = go.Figure()
        fig_op.add_bar(x=op_means_df[op_col], y=op_means_df["平均測定値"],
                       marker_color=["#3b82f6","#f97316","#22c55e"])
        fig_op.add_hline(y=result["grand_mean"], line_dash="dash",
                          annotation_text=f"全平均 {result['grand_mean']:.3f}")
        fig_op.update_layout(title="作業者別 平均測定値", height=350)
        st.plotly_chart(fig_op, use_container_width=True)
else:
    st.bar_chart(
        pd.DataFrame({"変動成分(%)": [result["ev_pct"], result["av_pct"], result["pv_pct"]]},
                     index=["%EV", "%AV", "%PV"])
    )

# ── ANOVA テーブル ────────────────────────────────────────────
st.subheader("ANOVA テーブル")
anova_disp = result["anova_table"].copy()
for col in ["SS", "MS", "F"]:
    anova_disp[col] = anova_disp[col].apply(
        lambda x: f"{x:.4f}" if pd.notna(x) and not np.isinf(x) else "—"
    )
anova_disp["p値"] = "—"
st.dataframe(anova_disp, hide_index=True, use_container_width=True)

# ── 分散成分サマリー ──────────────────────────────────────────
st.subheader("分散成分サマリー（%Study Variation）")
vc_df = pd.DataFrame([
    {"成分": "EV（繰り返し性）", "σ": f"{result['sigma_ev']:.4f}",
     "%Study Var": f"{result['ev_pct']:.1f}%", "判定基準": "<10% 合格"},
    {"成分": "AV（再現性）",     "σ": f"{result['sigma_av']:.4f}",
     "%Study Var": f"{result['av_pct']:.1f}%", "判定基準": ""},
    {"成分": "GRR（合計）",      "σ": f"{result['sigma_grr']:.4f}",
     "%Study Var": f"{result['grr_pct']:.1f}%", "判定基準": "<10% 合格 / <30% 条件付き"},
    {"成分": "PV（部品変動）",   "σ": f"{result['sigma_part']:.4f}",
     "%Study Var": f"{result['pv_pct']:.1f}%", "判定基準": ""},
    {"成分": "TV（合計）",       "σ": f"{result['sigma_total']:.4f}",
     "%Study Var": "100.0%", "判定基準": ""},
])
st.dataframe(vc_df, hide_index=True, use_container_width=True)
st.caption(f"ndc（識別カテゴリ数）= {result['ndc']}  （5以上が望ましい）")
