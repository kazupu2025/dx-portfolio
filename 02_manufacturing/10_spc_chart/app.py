# -*- coding: utf-8 -*-
"""
B-82: 製造 SPC管理図 X-bar/R + 異常ルール自動検出ダッシュボード
Streamlit ダッシュボード（ローカルモジュール依存を排除したスタンドアロン版）
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ── X-bar/R 計算ロジック（インライン） ────────────────────────────
_D3 = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0.076, 7: 0.136, 8: 0.184, 9: 0.223, 10: 0.256}
_D4 = {2: 3.267, 3: 2.574, 4: 2.282, 5: 2.114, 6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}
_A2 = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}


def compute_xbar_r(df: pd.DataFrame, value_col: str, subgroup_col: str) -> dict:
    df = df.copy()
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    groups = df.groupby(subgroup_col)[value_col].apply(list)
    subgroups = []
    for label, vals in groups.items():
        arr = [v for v in vals if pd.notna(v)]
        if len(arr) < 2:
            continue
        subgroups.append({
            "label": str(label),
            "xbar": np.mean(arr),
            "r": max(arr) - min(arr),
            "n": len(arr),
        })
    if len(subgroups) < 3:
        raise ValueError("サブグループが3つ以上必要です")

    n = subgroups[0]["n"]
    n_key = min(max(n, 2), 10)
    xbar_cl = np.mean([s["xbar"] for s in subgroups])
    r_bar = np.mean([s["r"] for s in subgroups])
    sigma = r_bar / (3.267 / _D4.get(n_key, 2.114))  # approximate
    # Control limits
    xbar_ucl = xbar_cl + _A2.get(n_key, 0.577) * r_bar
    xbar_lcl = xbar_cl - _A2.get(n_key, 0.577) * r_bar
    r_ucl = _D4.get(n_key, 2.114) * r_bar
    r_lcl = _D3.get(n_key, 0) * r_bar
    sigma_est = r_bar / (3.267 / _D4.get(n_key, 2.114))

    return {
        "subgroups": subgroups,
        "xbar_cl": xbar_cl, "xbar_ucl": xbar_ucl, "xbar_lcl": xbar_lcl,
        "r_bar": r_bar, "r_ucl": r_ucl, "r_lcl": r_lcl,
        "sigma": sigma_est,
    }


def detect_rule1(values: list[float], ucl: float, cl: float, lcl: float) -> list[int]:
    """Rule 1: 3σ超過"""
    return [i for i, v in enumerate(values) if v > ucl or v < lcl]


def detect_rule4(values: list[float], cl: float) -> list[int]:
    """Rule 4: 8点連続で同側"""
    violations = []
    for i in range(len(values) - 7):
        window = values[i:i+8]
        if all(v > cl for v in window) or all(v < cl for v in window):
            violations.extend(range(i, i+8))
    return list(set(violations))


def detect_rule5(values: list[float]) -> list[int]:
    """Rule 5: 6点連続トレンド"""
    violations = []
    for i in range(len(values) - 5):
        window = values[i:i+6]
        diffs = [window[j+1] - window[j] for j in range(5)]
        if all(d > 0 for d in diffs) or all(d < 0 for d in diffs):
            violations.extend(range(i, i+6))
    return list(set(violations))


RULE_NAMES = {
    "rule1": "Rule 1: 3σ超過",
    "rule4": "Rule 4: 8点連続で同側",
    "rule5": "Rule 5: 6点連続トレンド",
    "r_rule1": "R-Rule 1: R が UCL 超過",
}


def generate_sample_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for sg in range(1, 31):
        process = "工程A" if sg <= 15 else "工程B"
        for _ in range(5):
            rows.append({"subgroup": f"SG-{sg:02d}", "process": process,
                         "measurement": rng.normal(10.0, 0.3)})
    return pd.DataFrame(rows)


# ── UI ─────────────────────────────────────────────────────────────
st.title("📊 B-82 製造 SPC管理図 X-bar/R + 異常ルール自動検出")
st.caption("B-82 | 製造 × 品質管理 | CSVアップロード → X-bar/R管理図 + 異常8ルール検出")

for key, val in [("b82_df", None), ("b82_result", None),
                  ("b82_violations", {}), ("b82_proc_label", "")]:
    if key not in st.session_state:
        st.session_state[key] = val

with st.sidebar:
    st.header("⚙ 設定")
    if st.button("サンプルデータを使用", use_container_width=True, key="b82_sample"):
        st.session_state.b82_df = generate_sample_df()
    uploaded = st.file_uploader("CSVアップロード", type=["csv"], key="b82_upload")
    if uploaded:
        try:
            st.session_state.b82_df = pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            st.session_state.b82_df = pd.read_csv(uploaded, encoding="shift_jis")

    df = st.session_state.b82_df
    process_col = value_col = sub_col = process = None
    run_btn = False

    if df is not None:
        cols = df.columns.tolist()
        process_col = st.selectbox("工程列", cols, key="b82_proc_col")
        value_col = st.selectbox("測定値列", cols, index=min(2, len(cols)-1), key="b82_val_col")
        sub_col = st.selectbox("サブグループ列", cols, index=0, key="b82_sub_col")
        processes = df[process_col].dropna().unique().tolist() if process_col else []
        process = st.selectbox("分析する工程", processes, key="b82_process")
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True, key="b82_run")

df = st.session_state.b82_df
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    subset = df[df[process_col] == process].copy()
    try:
        result = compute_xbar_r(subset, value_col, sub_col)
        xbar_vals = [s["xbar"] for s in result["subgroups"]]
        r_vals = [s["r"] for s in result["subgroups"]]
        violations = {
            "rule1": detect_rule1(xbar_vals, result["xbar_ucl"], result["xbar_cl"], result["xbar_lcl"]),
            "rule4": detect_rule4(xbar_vals, result["xbar_cl"]),
            "rule5": detect_rule5(xbar_vals),
            "r_rule1": [i for i, v in enumerate(r_vals) if v > result["r_ucl"]],
        }
        st.session_state.b82_result = result
        st.session_state.b82_violations = violations
        st.session_state.b82_proc_label = process
    except ValueError as e:
        st.error(str(e))

result = st.session_state.b82_result
violations = st.session_state.b82_violations
proc_label = st.session_state.b82_proc_label

if result is None:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# KPI
xbar_vals = [s["xbar"] for s in result["subgroups"]]
r_vals = [s["r"] for s in result["subgroups"]]
labels = [s["label"] for s in result["subgroups"]]
all_violated = set()
for v_list in violations.values():
    all_violated.update(v_list)
total_sg = len(result["subgroups"])
pct = len(all_violated) / total_sg * 100 if total_sg else 0.0
v_label = "✅ 安定" if pct < 5 else ("⚠️ 要注意" if pct < 10 else "❌ 要確認")

c1, c2, c3, c4 = st.columns(4)
c1.metric("工程", proc_label)
c2.metric("サブグループ数", total_sg)
c3.metric("逸脱率", f"{pct:.1f}%")
c4.metric("状態判定", v_label)

st.divider()

# X-bar 管理図
st.subheader("X-bar 管理図")
xbar_df = pd.DataFrame({
    "X-bar": xbar_vals,
    "UCL": [result["xbar_ucl"]] * total_sg,
    "CL": [result["xbar_cl"]] * total_sg,
    "LCL": [result["xbar_lcl"]] * total_sg,
}, index=labels)
st.line_chart(xbar_df)

# R 管理図
st.subheader("R 管理図")
r_df = pd.DataFrame({
    "R": r_vals,
    "UCL": [result["r_ucl"]] * total_sg,
    "CL": [result["r_bar"]] * total_sg,
}, index=labels)
st.line_chart(r_df)

# 違反ポイント
all_rows = []
for rule_key, idxs in violations.items():
    rule_name = RULE_NAMES.get(rule_key, rule_key)
    for i in idxs:
        if i < len(result["subgroups"]):
            sg = result["subgroups"][i]
            all_rows.append({
                "ルール": rule_name,
                "サブグループ": sg["label"],
                "値": f"{sg['xbar']:.4f}" if "r_rule" not in rule_key else f"{sg['r']:.4f}(R)",
            })
if all_rows:
    st.subheader("⚠️ 違反ポイント一覧")
    st.dataframe(pd.DataFrame(all_rows), hide_index=True, use_container_width=True)
else:
    st.success("違反ポイントなし — 工程は安定しています")
