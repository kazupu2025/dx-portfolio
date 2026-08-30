# -*- coding: utf-8 -*-
"""
B-81: 製造 工程能力指数（Cp/Cpk）分析ダッシュボード
Streamlit ダッシュボード
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

try:
    from scipy import stats as _scipy_stats
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

BASE_DIR = Path(__file__).resolve().parent


# ── Cp/Cpk 計算ロジック（インライン） ──────────────────────────────
def calculate_process(series: pd.Series, usl: float, lsl: float) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    n = len(s)
    if n == 0:
        raise ValueError("有効な測定値がありません")
    std = s.std(ddof=1)
    if std == 0:
        raise ValueError("標準偏差が0です（全測定値が同一）")
    mean = s.mean()
    cp = (usl - lsl) / (6 * std)
    cpk = min((usl - mean) / (3 * std), (mean - lsl) / (3 * std))
    center = (usl + lsl) / 2
    if _HAS_SCIPY:
        p_below = _scipy_stats.norm.cdf(lsl, loc=mean, scale=std)
        p_above = 1 - _scipy_stats.norm.cdf(usl, loc=mean, scale=std)
        out_of_spec_pct = round((p_below + p_above) * 100, 2)
    else:
        out_of_spec_pct = None
    return {
        "cp": round(cp, 3), "cpk": round(cpk, 3),
        "mean": round(mean, 4), "std": round(std, 4),
        "n": n, "usl": usl, "lsl": lsl,
        "out_of_spec_pct": out_of_spec_pct,
        "center_deviation": round(mean - center, 4),
        "low_sample": n < 20,
    }


def get_verdict(cpk: float) -> str:
    if cpk >= 1.67: return "非常に良好"
    if cpk >= 1.33: return "良好"
    if cpk >= 1.00: return "要改善"
    return "不可"


def get_action(cp: float, cpk: float) -> str:
    if cpk < 0:
        return "工程が規格外に逸脱（直ちに生産停止・原因究明が必要）"
    if cp >= 1.33 and cpk < 1.00:
        return "平均値を規格中心に調整（センタリング優先・ばらつきは許容範囲内）"
    if cp < 1.00:
        return "工程のばらつきを低減（設備精度・材料・作業手順の見直し）"
    if cp < 1.33:
        return "ばらつき低減と中心合わせの両立が必要"
    return "現状維持（定期モニタリング継続）"


def run_analysis(df, process_col, value_col, spec_values) -> list[dict]:
    df = df.copy()
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    results = []
    for process, spec in spec_values.items():
        subset = df[df[process_col] == process][value_col].dropna()
        if len(subset) == 0:
            continue
        try:
            r = calculate_process(subset, usl=spec["usl"], lsl=spec["lsl"])
        except ValueError:
            continue
        r["process"] = process
        r["verdict"] = get_verdict(r["cpk"])
        r["action"] = get_action(r["cp"], r["cpk"])
        results.append(r)
    return results


# ── UI ─────────────────────────────────────────────────────────────
st.title("📐 B-81 製造 工程能力指数（Cp/Cpk）分析ダッシュボード")
st.caption("B-81 | 製造 × 品質管理 | CSVアップロード → USL/LSL入力 → Cp/Cpk一括計算")

# セッション状態
for key, val in [("spec_values", {}), ("results", []), ("df", None),
                  ("selected_process", None), ("b81_process_col", None), ("b81_value_col", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("⚙ 設定パネル")

    # サンプルCSV
    sample_path = BASE_DIR / "data" / "sample_measurement.csv"
    if sample_path.exists():
        with open(sample_path, "rb") as f:
            st.download_button("📥 サンプルCSVをダウンロード", data=f,
                               file_name="sample_measurement.csv", mime="text/csv")

    uploaded = st.file_uploader("測定データCSVをアップロード", type=["csv"], key="b81_upload")
    if uploaded:
        try:
            df_new = pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df_new = pd.read_csv(uploaded, encoding="shift_jis")
        st.session_state.df = df_new
        st.caption(f"読み込み完了: {len(df_new):,} 行 × {len(df_new.columns)} 列")

    df = st.session_state.df
    if df is None:
        st.info("CSVをアップロードしてください")
        st.stop()

    # 列マッピング
    cols = list(df.columns)
    default_proc = next((c for c in cols if "工程" in c or "process" in c.lower()), cols[0])
    default_val = next((c for c in cols if "測定" in c or "値" in c or "value" in c.lower()), cols[-1])
    process_col = st.selectbox("工程名列", cols, index=cols.index(default_proc), key="b81_proc_col")
    value_col = st.selectbox("測定値列", cols, index=cols.index(default_val), key="b81_val_col")

    processes = sorted(df[process_col].dropna().unique().tolist())
    if not processes:
        st.error("工程名列に有効な値がありません")
        st.stop()

    # 規格値入力
    st.markdown("**工程別 規格値（USL / LSL）**")
    bc1, bc2, bc3 = st.columns([2, 2, 2])
    with bc1:
        bulk_lsl = st.number_input("LSL", value=9.80, step=0.01, key="b81_bulk_lsl")
    with bc2:
        bulk_usl = st.number_input("USL", value=10.20, step=0.01, key="b81_bulk_usl")
    with bc3:
        if st.button("全工程に適用", use_container_width=True, key="b81_bulk_apply"):
            for p in processes:
                st.session_state.spec_values[p] = {"usl": bulk_usl, "lsl": bulk_lsl}

    for proc in processes:
        spec = st.session_state.spec_values.get(proc, {})
        is_set = "usl" in spec and "lsl" in spec
        with st.expander(f"{'✓' if is_set else '✗'} {proc}", expanded=not is_set):
            sc1, sc2 = st.columns(2)
            with sc1:
                lsl_v = st.number_input("LSL", value=float(spec.get("lsl", 9.80)),
                                        step=0.01, key=f"b81_lsl_{proc}")
            with sc2:
                usl_v = st.number_input("USL", value=float(spec.get("usl", 10.20)),
                                        step=0.01, key=f"b81_usl_{proc}")
            if usl_v > lsl_v:
                st.session_state.spec_values[proc] = {"usl": usl_v, "lsl": lsl_v}
            else:
                st.error("USL > LSL が必要です")

    if st.button("▶ 分析実行", type="primary", use_container_width=True, key="b81_run"):
        with st.spinner("計算中..."):
            try:
                results = run_analysis(df, process_col, value_col, st.session_state.spec_values)
                st.session_state.results = results
                st.session_state.b81_process_col = process_col
                st.session_state.b81_value_col = value_col
                if results:
                    st.session_state.selected_process = results[0]["process"]
                st.success(f"{len(results)} 工程の分析完了")
            except Exception as e:
                st.error(f"分析エラー: {e}")

with col_right:
    results = st.session_state.results
    if not results:
        st.info("左パネルでCSVをアップロードし、規格値を設定して「▶ 分析実行」を押してください。")
        st.stop()

    st.subheader("📊 工程能力サマリー")

    # サマリーテーブル
    summary_rows = []
    for r in results:
        verdict = r["verdict"]
        icon = "✅" if verdict in ("良好", "非常に良好") else ("⚠️" if verdict == "要改善" else "❌")
        summary_rows.append({
            "工程": r["process"], "Cp": r["cp"], "Cpk": r["cpk"],
            "n": r["n"], "判定": f"{icon} {verdict}"
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    # 工程選択
    proc_options = [r["process"] for r in results]
    current_idx = (proc_options.index(st.session_state.selected_process)
                   if st.session_state.selected_process in proc_options else 0)
    selected = st.radio("詳細を見る工程", proc_options, index=current_idx,
                        horizontal=True, label_visibility="collapsed", key="b81_radio")
    st.session_state.selected_process = selected

    r = next((x for x in results if x["process"] == selected), None)
    if r is None:
        st.stop()

    st.markdown(f"---\n#### {r['process']} — 詳細")
    verdict = r["verdict"]
    c1, c2, c3 = st.columns(3)
    cp_ok = r["cp"] >= 1.33
    c1.metric("Cp", f"{r['cp']:.3f}", delta="良好" if cp_ok else "要改善",
              delta_color="normal" if cp_ok else "inverse")
    cpk_ok = r["cpk"] >= 1.33
    c2.metric("Cpk", f"{r['cpk']:.3f}", delta=verdict,
              delta_color="normal" if cpk_ok else "inverse")
    c3.metric("n / 規格外推定",
              f"{r['n']}件",
              delta=f"{r['out_of_spec_pct']:.2f}% 規格外" if r["out_of_spec_pct"] is not None else "scipy未インストール",
              delta_color="inverse" if (r["out_of_spec_pct"] or 0) > 0 else "normal")

    st.info(f"📋 改善アクション: {r['action']}")
    if r["low_sample"]:
        st.warning("⚠ サンプル数 < 20 のため信頼性に注意してください")

    # 測定値分布（ヒストグラム近似）
    df_full = st.session_state.df
    proc_col_s = st.session_state.b81_process_col
    val_col_s = st.session_state.b81_value_col
    if df_full is not None and proc_col_s and val_col_s:
        subset = df_full[df_full[proc_col_s] == r["process"]][val_col_s].dropna()
        if len(subset) > 0:
            st.subheader("測定値分布（ビン集計）")
            counts, bin_edges = np.histogram(subset, bins=20)
            bin_labels = [f"{e:.3f}" for e in bin_edges[:-1]]
            hist_df = pd.Series(counts, index=bin_labels, name="件数")
            st.bar_chart(hist_df)
            st.caption(f"LSL={r['lsl']} / 平均={r['mean']:.4f} / USL={r['usl']}  |  σ={r['std']:.4f}")
