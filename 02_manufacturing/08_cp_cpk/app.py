"""C-62 工程能力指数（Cp/Cpk）分析システム"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
# ── analyze.py インライン（Streamlit Cloud 互換）──
"""Cp/Cpk計算・診断ロジック（純粋関数モジュール）"""
import numpy as np
import pandas as pd
from scipy import stats


def calculate_process(series: pd.Series, usl: float, lsl: float) -> dict:
    """単一工程の測定値シリーズからCp/Cpkを計算する。"""
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
    center_deviation = mean - center

    # 規格外推定割合（正規分布仮定）
    p_below = stats.norm.cdf(lsl, loc=mean, scale=std)
    p_above = 1 - stats.norm.cdf(usl, loc=mean, scale=std)
    out_of_spec_pct = round((p_below + p_above) * 100, 2)

    return {
        "cp": round(cp, 3),
        "cpk": round(cpk, 3),
        "mean": round(mean, 4),
        "std": round(std, 4),
        "n": n,
        "usl": usl,
        "lsl": lsl,
        "out_of_spec_pct": out_of_spec_pct,
        "center_deviation": round(center_deviation, 4),
        "low_sample": n < 20,
    }


def get_verdict(cpk: float) -> str:
    """Cpk値から判定文字列を返す。"""
    if cpk >= 1.67:
        return "非常に良好"
    if cpk >= 1.33:
        return "良好"
    if cpk >= 1.00:
        return "要改善"
    return "不可"


def get_action(cp: float, cpk: float) -> str:
    """Cp/Cpkの関係から改善アクションを返す。"""
    if cpk < 0:
        return "工程が規格外に逸脱（直ちに生産停止・原因究明が必要）"
    if cp >= 1.33 and cpk < 1.00:
        return "平均値を規格中心に調整（センタリング優先・ばらつきは許容範囲内）"
    if cp < 1.00:
        return "工程のばらつきを低減（設備精度・材料・作業手順の見直し）"
    if cp < 1.33:
        return "ばらつき低減と中心合わせの両立が必要"
    return "現状維持（定期モニタリング継続）"


def run_analysis(
    df: pd.DataFrame,
    process_col: str,
    value_col: str,
    spec_values: dict,
) -> list[dict]:
    """
    全工程のCp/Cpkを計算して結果リストを返す。
    spec未設定の工程はスキップ。数値変換できない行は除外。
    """
    results = []
    df = df.copy()
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

    for process, spec in spec_values.items():
        usl = spec["usl"]
        lsl = spec["lsl"]
        subset = df[df[process_col] == process][value_col].dropna()
        if len(subset) == 0:
            continue
        try:
            r = calculate_process(subset, usl=usl, lsl=lsl)
        except ValueError:
            continue

        r["process"] = process
        r["verdict"] = get_verdict(r["cpk"])
        r["action"] = get_action(r["cp"], r["cpk"])
        results.append(r)

    return results

# ────────────────────────────────────────────────
from visualize import plot_histogram

st.set_page_config(
    page_title="工程能力分析 Cp/Cpk",
    page_icon="📐",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f5f7fa; }
[data-testid="stHeader"] { background-color: #f5f7fa; }
.block-container { padding-top: 1.5rem; }
.kpi-card {
    border-radius: 8px; padding: 14px 16px; text-align: center;
    border: 2px solid; margin: 4px 0;
}
.verdict-good  { background:#f0fdf4; border-color:#16a34a; }
.verdict-warn  { background:#fff7ed; border-color:#d97706; }
.verdict-ng    { background:#fef2f2; border-color:#dc2626; }
.action-box {
    border-radius: 6px; padding: 10px 14px; font-size: 0.88em;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── セッション状態初期化 ──────────────────────────────────────
if "spec_values" not in st.session_state:
    st.session_state.spec_values = {}
if "results" not in st.session_state:
    st.session_state.results = []
if "df" not in st.session_state:
    st.session_state.df = None
if "selected_process" not in st.session_state:
    st.session_state.selected_process = None
if "process_col" not in st.session_state:
    st.session_state.process_col = None
if "value_col" not in st.session_state:
    st.session_state.value_col = None


def _verdict_style(verdict: str) -> str:
    if verdict in ("良好", "非常に良好"):
        return "verdict-good"
    if verdict == "要改善":
        return "verdict-warn"
    return "verdict-ng"


def _verdict_color(verdict: str) -> str:
    mapping = {"非常に良好": "#16a34a", "良好": "#16a34a",
               "要改善": "#d97706", "不可": "#dc2626"}
    return mapping.get(verdict, "#374151")


def _verdict_icon(verdict: str) -> str:
    if verdict in ("良好", "非常に良好"):
        return "✓"
    if verdict == "要改善":
        return "⚠"
    return "✗"


# ── ヘッダー ─────────────────────────────────────────────────
st.markdown(
    '<div style="background:#1e3a5f;padding:16px 24px;border-radius:8px;margin-bottom:16px">'
    '<span style="color:#fff;font-size:1.4em;font-weight:700">📐 工程能力指数（Cp/Cpk）分析システム</span>'
    '<span style="color:#94a3b8;font-size:0.85em;margin-left:16px">C-62 | 製造業 / 生産・品質</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ── 左右レイアウト ────────────────────────────────────────────
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("### ⚙ 設定パネル")

    # ① CSV アップロード
    sample_path = Path(__file__).parent / "data" / "sample_measurement.csv"
    if sample_path.exists():
        with open(sample_path, "rb") as f:
            st.download_button(
                "📥 サンプルCSVをダウンロード",
                data=f,
                file_name="sample_measurement.csv",
                mime="text/csv",
            )

    uploaded = st.file_uploader("測定データCSV をアップロード", type=["csv"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded, encoding="shift_jis")
        st.session_state.df = df
        st.caption(f"読み込み完了: {len(df):,} 行 × {len(df.columns)} 列")

    df = st.session_state.df
    if df is None:
        st.info("CSVをアップロードしてください")
        st.stop()

    # ② 列マッピング
    st.markdown("**列マッピング**")
    cols = list(df.columns)
    default_proc = next((c for c in cols if "工程" in c), cols[0])
    default_val = next((c for c in cols if "測定" in c or "値" in c), cols[-1])

    process_col = st.selectbox("工程名列", cols,
                               index=cols.index(default_proc))
    value_col = st.selectbox("測定値列", cols,
                             index=cols.index(default_val))
    st.session_state.process_col = process_col
    st.session_state.value_col = value_col

    # 工程リスト取得
    processes = sorted(df[process_col].dropna().unique().tolist())
    if not processes:
        st.error("工程名列に有効な値がありません")
        st.stop()

    # ③ 規格値入力（アコーディオン）
    st.markdown("**工程別 規格値（USL / LSL）**")

    # 一括コピーボタン
    bulk_col1, bulk_col2, bulk_col3 = st.columns([2, 2, 2])
    with bulk_col1:
        bulk_lsl = st.number_input("一括 LSL", value=9.80, step=0.01,
                                   key="bulk_lsl", label_visibility="collapsed")
    with bulk_col2:
        bulk_usl = st.number_input("一括 USL", value=10.20, step=0.01,
                                   key="bulk_usl", label_visibility="collapsed")
    with bulk_col3:
        if st.button("全工程に適用", use_container_width=True):
            for p in processes:
                st.session_state.spec_values[p] = {
                    "usl": bulk_usl, "lsl": bulk_lsl
                }

    for proc in processes:
        spec = st.session_state.spec_values.get(proc, {})
        is_set = "usl" in spec and "lsl" in spec
        badge = "✓ 設定済" if is_set else "✗ 未設定"
        badge_color = "#16a34a" if is_set else "#dc2626"
        label = (
            f'<span style="font-weight:600">{proc}</span> '
            f'<span style="font-size:0.78em;color:{badge_color};'
            f'background:{"#f0fdf4" if is_set else "#fef2f2"};'
            f'padding:1px 6px;border-radius:10px">{badge}</span>'
        )
        with st.expander(label, expanded=not is_set):
            c1, c2 = st.columns(2)
            with c1:
                lsl_val = st.number_input(
                    "LSL", value=float(spec.get("lsl", 9.80)),
                    step=0.01, key=f"lsl_{proc}",
                )
            with c2:
                usl_val = st.number_input(
                    "USL", value=float(spec.get("usl", 10.20)),
                    step=0.01, key=f"usl_{proc}",
                )
            if usl_val <= lsl_val:
                st.error("USL > LSL である必要があります")
            else:
                st.session_state.spec_values[proc] = {
                    "usl": usl_val, "lsl": lsl_val
                }

    # ④ 分析実行ボタン
    missing = [p for p in processes
               if p not in st.session_state.spec_values]
    if missing:
        st.warning(f"未設定工程: {', '.join(missing)}（スキップされます）")

    if st.button("▶ 分析実行", type="primary", use_container_width=True):
        with st.spinner("計算中..."):
            try:
                results = run_analysis(
                    df,
                    process_col=process_col,
                    value_col=value_col,
                    spec_values=st.session_state.spec_values,
                )
                st.session_state.results = results
                # ── 統合DB への書き込み ──────────────────────────────
                if results:
                    try:
                        _db_root = Path(__file__).parent.parent.parent
                        if str(_db_root) not in sys.path:
                            sys.path.insert(0, str(_db_root))
                        from _common.db_writer import init_db as _init_db
                        from _common.db_writer import write_upload, write_kpi, write_cpk_results, cpk_to_verdict as _cpk_to_verdict
                        _init_db()
                        _fname = uploaded.name if uploaded else "sample"
                        _uid = write_upload("cpk", _fname, len(df))
                        write_cpk_results(_uid, results)
                        from datetime import datetime as _dt
                        _ym = _dt.now().strftime("%Y-%m")
                        _min_cpk = min(r["cpk"] for r in results)
                        _v = _cpk_to_verdict(_min_cpk)
                        write_kpi(_uid, "cpk", _ym, "min_cpk", _min_cpk, _v)
                    except Exception as _e:
                        st.caption(f"⚠ DB書き込みスキップ: {_e}")
                # ────────────────────────────────────────────────────
                if results:
                    st.session_state.selected_process = results[0]["process"]
                st.success(f"{len(results)} 工程の分析が完了しました")
            except Exception as e:
                st.error(f"分析エラー: {e}")

# ── 右パネル：結果ダッシュボード ─────────────────────────────
with col_right:
    results = st.session_state.results
    if not results:
        st.markdown("### 📊 結果ダッシュボード")
        st.info("左パネルでCSVをアップロードし、規格値を入力して「分析実行」ボタンを押してください。")
        st.stop()

    st.markdown("### 📊 工程能力サマリー")

    # st.radio で工程選択
    proc_options = [r["process"] for r in results]
    current_idx = (proc_options.index(st.session_state.selected_process)
                   if st.session_state.selected_process in proc_options else 0)

    # 表示用 HTML テーブル
    header_bg = "#1e3a5f"
    table_rows = ""
    for r in results:
        color = _verdict_color(r["verdict"])
        icon = _verdict_icon(r["verdict"])
        is_selected = r["process"] == st.session_state.selected_process
        row_bg = "#e8f0fe" if is_selected else "#ffffff"
        table_rows += (
            f'<tr style="background:{row_bg}">'
            f'<td style="padding:6px 10px;font-weight:{"700" if is_selected else "400"}">'
            f'{"▶ " if is_selected else ""}{r["process"]}</td>'
            f'<td style="padding:6px 10px;text-align:center">{r["cp"]:.2f}</td>'
            f'<td style="padding:6px 10px;text-align:center">{r["cpk"]:.2f}</td>'
            f'<td style="padding:6px 10px;text-align:center">{r["n"]}</td>'
            f'<td style="padding:6px 10px;text-align:center;color:{color};font-weight:600">'
            f'{icon} {r["verdict"]}</td>'
            f'</tr>'
        )
    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;font-size:0.88em">'
        f'<tr style="background:{header_bg};color:#fff">'
        f'<th style="padding:7px 10px;text-align:left">工程</th>'
        f'<th style="padding:7px 10px">Cp</th>'
        f'<th style="padding:7px 10px">Cpk</th>'
        f'<th style="padding:7px 10px">n</th>'
        f'<th style="padding:7px 10px">判定</th>'
        f'</tr>{table_rows}</table>',
        unsafe_allow_html=True,
    )

    selected = st.radio(
        "詳細を見る工程",
        proc_options,
        index=current_idx,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.selected_process = selected

    # ── 詳細スコアカード ────────────────────────────────────
    r = next((x for x in results if x["process"] == selected), None)
    if r is None:
        st.stop()

    st.markdown(f"---\n#### {r['process']} — 詳細")

    verdict_class = _verdict_style(r["verdict"])
    color = _verdict_color(r["verdict"])
    icon = _verdict_icon(r["verdict"])

    # Cp分析コメント
    cp_comment = "▲ 分布幅は十分" if r["cp"] >= 1.33 else "▼ 分布幅が不足"
    cpk_comment = "▼ 中心ずれあり" if abs(r["cpk"] - r["cp"]) > 0.15 else "▲ 中心は良好"

    kc1, kc2, kc3 = st.columns(3)
    with kc1:
        cp_color = "#16a34a" if r["cp"] >= 1.33 else "#dc2626"
        st.markdown(
            f'<div class="kpi-card" style="background:{"#f0fdf4" if r["cp"]>=1.33 else "#fef2f2"};'
            f'border-color:{cp_color}">'
            f'<div style="font-size:0.78em;color:#6b7280">Cp</div>'
            f'<div style="font-size:2em;font-weight:800;color:#1e3a5f">{r["cp"]:.2f}</div>'
            f'<div style="font-size:0.75em;color:{cp_color}">{cp_comment}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with kc2:
        cpk_color = _verdict_color(r["verdict"])
        st.markdown(
            f'<div class="kpi-card {verdict_class}">'
            f'<div style="font-size:0.78em;color:#6b7280">Cpk</div>'
            f'<div style="font-size:2em;font-weight:800;color:{cpk_color}">{r["cpk"]:.2f}</div>'
            f'<div style="font-size:0.75em;color:{cpk_color}">{cpk_comment}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with kc3:
        st.markdown(
            f'<div class="kpi-card {verdict_class}">'
            f'<div style="font-size:0.78em;color:#6b7280">総合判定</div>'
            f'<div style="font-size:1.5em;font-weight:800;color:{color}">{icon} {r["verdict"]}</div>'
            f'<div style="font-size:0.72em;color:#6b7280">n={r["n"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # 改善アクション
    action_bg = "#fef2f2" if r["verdict"] == "不可" else (
        "#fff7ed" if r["verdict"] == "要改善" else "#f0fdf4"
    )
    action_border = color
    deviation_note = (
        f"（規格中心から {r['center_deviation']:+.4f} のずれ）"
        if abs(r["center_deviation"]) > 0.001 else ""
    )
    st.markdown(
        f'<div class="action-box" style="background:{action_bg};border-left:4px solid {action_border}">'
        f'<div style="font-weight:600;color:{action_border};margin-bottom:4px">📋 改善アクション</div>'
        f'<div style="color:#374151">{r["action"]}{deviation_note}</div>'
        f'<div style="color:#6b7280;font-size:0.82em;margin-top:4px">'
        f'規格外推定割合: {r["out_of_spec_pct"]:.2f}%'
        f'{"  ⚠ サンプル数が少ないため信頼性に注意" if r["low_sample"] else ""}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ヒストグラム
    st.markdown("**測定値分布**")
    df_full = st.session_state.df
    if df_full is not None:
        proc_col = st.session_state.process_col
        val_col = st.session_state.value_col
        subset = df_full[df_full[proc_col] == r["process"]][val_col]
        try:
            png = plot_histogram(
                subset,
                usl=r["usl"],
                lsl=r["lsl"],
                cp=r["cp"],
                cpk=r["cpk"],
                process=r["process"],
                verdict=r["verdict"],
            )
            st.image(png, use_container_width=True)
        except Exception as e:
            st.error(f"グラフ生成エラー: {e}")
