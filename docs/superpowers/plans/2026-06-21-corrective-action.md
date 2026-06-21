# 是正処置（8D）効果検証 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 是正処置前後の品質データを t検定 + Mann-Whitney U検定で統計的に比較し、是正効果を自動判定する（verdict: good/warning/alert が C-66 と逆）。

**Architecture:** C-66（4M変更）の analyze.py を verdict ロジックのみ反転してコピー。visualize.py は C-66 のものを app.py から import して再利用。analyze.py（純粋関数）→ C-66 visualize.py（転用）→ app.py（Streamlit + DB）の3層構成。

**Tech Stack:** Python 3.11+, Streamlit, Plotly, pandas, numpy, scipy（shapiro/ttest_ind/mannwhitneyu）, pytest

---

## File Map

| ファイル | 操作 | 役割 |
|---------|------|------|
| `02_manufacturing/14_corrective_action/sample_data.py` | 新規 | デモCSV生成（是正前μ=12.0 / 是正後μ=8.0、n=30×2）|
| `02_manufacturing/14_corrective_action/tests/__init__.py` | 新規 | pytest パッケージ宣言 |
| `02_manufacturing/14_corrective_action/tests/test_analyze.py` | 新規 | 8テスト TDD（verdict 反転を検証）|
| `02_manufacturing/14_corrective_action/analyze.py` | 新規 | C-66 から verdict のみ反転 |
| `02_manufacturing/14_corrective_action/app.py` | 新規 | Streamlit UI（C-66 から label/title/DB のみ変更）|
| `02_manufacturing/14_corrective_action/STATUS.md` | 新規 | production-ready |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | 修正 | corrective_action カード追加 |
| `catalog.yml` | 修正 | C-70 エントリ追加 |

> **visualize.py は作成しない。** app.py 内で C-66 の visualize.py を sys.path 経由で import する。

---

### Task 1: scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/14_corrective_action/sample_data.py`
- Create: `02_manufacturing/14_corrective_action/STATUS.md`
- Create: `02_manufacturing/14_corrective_action/tests/__init__.py`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\14_corrective_action\tests"
```

- [ ] **Step 2: tests/__init__.py を作成（空ファイル）**

`02_manufacturing/14_corrective_action/tests/__init__.py`:
```python
```

- [ ] **Step 3: STATUS.md を作成**

`02_manufacturing/14_corrective_action/STATUS.md`:
```markdown
# C-70 是正処置（8D）効果検証

- name: 是正処置（8D）効果検証
- industry: 製造
- department: 品質
- status: in-progress
```

- [ ] **Step 4: sample_data.py を作成**

`02_manufacturing/14_corrective_action/sample_data.py`:
```python
"""是正処置効果検証 デモ用サンプルデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    是正前後の不良率(%)データを生成する。

    before: μ=12.0、σ=2.0、n=30（是正前の高い不良率）
    after:  μ=8.0、σ=1.5、n=30（是正後の改善）
    → p < 0.05、効果量大 → verdict = "good"（是正効果確認）が期待される
    """
    rng = np.random.default_rng(42)
    before_vals = rng.normal(12.0, 2.0, 30)
    after_vals  = rng.normal(8.0,  1.5, 30)

    rows = (
        [{"group": "before", "measurement": round(float(v), 4)} for v in before_vals]
        + [{"group": "after",  "measurement": round(float(v), 4)} for v in after_vals]
    )
    df = pd.DataFrame(rows)
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_corrective_action.csv"
    generate_sample_csv(str(out))
    print(f"Generated: {out}")
```

- [ ] **Step 5: 動作確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python 02_manufacturing/14_corrective_action/sample_data.py
```

期待出力: `Generated: ...sample_corrective_action.csv`

- [ ] **Step 6: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/14_corrective_action/
git commit -m "feat(C-70): scaffold + sample_data.py（是正前μ=12/是正後μ=8、n=30×2）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/14_corrective_action/tests/test_analyze.py`
- Create: `02_manufacturing/14_corrective_action/analyze.py`

**核心差分:** C-66 の verdict ロジック（p≥0.05→"good"、大効果→"alert"）を逆転させる。
- C-70: p≥0.05 → `"alert"` / p<0.05 + 効果量<0.5 → `"warning"` / p<0.05 + 効果量≥0.5 → `"good"`

- [ ] **Step 1: テストを書く**

`02_manufacturing/14_corrective_action/tests/test_analyze.py`:
```python
"""analyze.run_analysis の検定ロジック ユニットテスト（是正処置版）。"""
from __future__ import annotations
import sys
from pathlib import Path
import math
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(before_vals, after_vals) -> pd.DataFrame:
    rows = (
        [{"group": "before", "measurement": float(v)} for v in before_vals]
        + [{"group": "after",  "measurement": float(v)} for v in after_vals]
    )
    return pd.DataFrame(rows)


def _normal_same() -> pd.DataFrame:
    """同一正規分布 → 有意差なし（C-70: alert 期待）"""
    rng = np.random.default_rng(0)
    return _make_df(rng.normal(10.0, 1.0, 50), rng.normal(10.0, 1.0, 50))


def _large_effect() -> pd.DataFrame:
    """大きな平均差 → p < 0.05 かつ効果量 ≥ 0.5（C-70: good 期待）"""
    rng = np.random.default_rng(1)
    return _make_df(rng.normal(10.0, 0.3, 30), rng.normal(11.5, 0.3, 30))


def _small_effect() -> pd.DataFrame:
    """小さな平均差・n大 → p < 0.05 かつ効果量 < 0.5（C-70: warning 期待）"""
    rng = np.random.default_rng(2)
    return _make_df(rng.normal(10.0, 0.3, 200), rng.normal(10.1, 0.3, 200))


def _nonnormal() -> pd.DataFrame:
    """指数分布（非正規）→ Shapiro-Wilk で少なくとも片方が非正規"""
    rng = np.random.default_rng(3)
    return _make_df(rng.exponential(1.0, 30), rng.exponential(2.0, 30))


def test_no_significant_diff():
    """同一分布では p ≥ 0.05 → verdict = 'alert'（C-66 は 'good'）"""
    result = analyze.run_analysis(_normal_same(), "group", "measurement", "before", "after")
    assert result["p_value"] >= 0.05
    assert result["verdict"] == "alert"


def test_significant_large_effect():
    """大きな平均差は p < 0.05 かつ effect_size ≥ 0.5 → 'good'（C-66 は 'alert'）"""
    result = analyze.run_analysis(_large_effect(), "group", "measurement", "before", "after")
    assert result["p_value"] < 0.05
    assert result["effect_size"] >= 0.5
    assert result["verdict"] == "good"


def test_significant_small_effect():
    """小さな平均差・大きな n は p < 0.05 かつ effect_size < 0.5 → 'warning'"""
    result = analyze.run_analysis(_small_effect(), "group", "measurement", "before", "after")
    assert result["p_value"] < 0.05
    assert result["effect_size"] < 0.5
    assert result["verdict"] == "warning"


def test_normality_selects_ttest():
    """両グループが正規分布なら recommended = 't'"""
    rng = np.random.default_rng(10)
    df = _make_df(rng.normal(10, 1, 50), rng.normal(10.5, 1, 50))
    result = analyze.run_analysis(df, "group", "measurement", "before", "after")
    assert result["normal_before"] is True
    assert result["normal_after"] is True
    assert result["recommended"] == "t"


def test_nonnormal_selects_mannwhitney():
    """非正規分布では recommended = 'mw'"""
    result = analyze.run_analysis(_nonnormal(), "group", "measurement", "before", "after")
    assert not (result["normal_before"] and result["normal_after"]), \
        "Expected at least one group to be non-normal with exponential distribution"
    assert result["recommended"] == "mw"


def test_cohens_d_formula():
    """Cohen's d = |mean_after - mean_before| / pooled_std の計算が正しいこと"""
    rng = np.random.default_rng(99)
    before = rng.normal(10.0, 1.0, 50)
    after  = rng.normal(11.0, 1.0, 50)
    df = _make_df(before, after)
    result = analyze.run_analysis(df, "group", "measurement", "before", "after")
    n_b, n_a = 50, 50
    pooled_std = math.sqrt(
        ((n_b - 1) * before.std(ddof=1) ** 2 + (n_a - 1) * after.std(ddof=1) ** 2)
        / (n_b + n_a - 2)
    )
    expected_d = abs(after.mean() - before.mean()) / pooled_std
    assert result["cohens_d"] == pytest.approx(expected_d, rel=1e-5)


def test_output_keys():
    """全20出力キーが揃っていること"""
    result = analyze.run_analysis(_large_effect(), "group", "measurement", "before", "after")
    required_keys = {
        "n_before", "n_after", "mean_before", "mean_after",
        "std_before", "std_after",
        "shapiro_before_p", "shapiro_after_p",
        "normal_before", "normal_after",
        "t_stat", "t_pvalue", "cohens_d",
        "mw_stat", "mw_pvalue", "rank_biserial_r",
        "recommended", "p_value", "effect_size", "verdict",
    }
    assert required_keys <= set(result.keys())


def test_insufficient_data_raises():
    """各グループ n < 3 のとき ValueError が発生すること"""
    df = _make_df([10.0, 10.1], [11.0, 11.1])
    with pytest.raises(ValueError, match="3"):
        analyze.run_analysis(df, "group", "measurement", "before", "after")
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/14_corrective_action/tests/test_analyze.py -v 2>&1 | head -10
```

期待: `ModuleNotFoundError: No module named 'analyze'`

- [ ] **Step 3: analyze.py を実装（C-66 から verdict のみ反転）**

`02_manufacturing/14_corrective_action/analyze.py`:
```python
"""是正処置効果検証 統計的有意差検定ロジック（純粋関数モジュール）。"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from scipy import stats


def run_analysis(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    before_label: str,
    after_label: str,
) -> dict:
    """
    是正前後2グループの測定値を t検定 + Mann-Whitney U検定で比較する。

    verdict ロジックは C-66（4M変更）と逆:
    - p ≥ 0.05           → "alert"   （有意差なし: 効果不明）
    - p < 0.05, eff < 0.5 → "warning" （有意だが効果量小）
    - p < 0.05, eff ≥ 0.5 → "good"    （是正効果確認）

    Parameters
    ----------
    df : pd.DataFrame
    group_col : str
    value_col : str
    before_label : str
    after_label : str

    Returns
    -------
    dict
        n_before, n_after, mean_before, mean_after, std_before, std_after,
        shapiro_before_p, shapiro_after_p, normal_before, normal_after,
        t_stat, t_pvalue, cohens_d,
        mw_stat, mw_pvalue, rank_biserial_r,
        recommended, p_value, effect_size, verdict

    Raises
    ------
    ValueError
        いずれかのグループの n < 3 のとき
    """
    before = pd.to_numeric(
        df.loc[df[group_col] == before_label, value_col], errors="coerce"
    ).dropna().to_numpy(dtype=float)

    after = pd.to_numeric(
        df.loc[df[group_col] == after_label, value_col], errors="coerce"
    ).dropna().to_numpy(dtype=float)

    if len(before) < 3 or len(after) < 3:
        raise ValueError(
            f"各グループは最低 3 サンプル必要です。before={len(before)}, after={len(after)}"
        )

    # ── 記述統計 ────────────────────────────────────────────────
    n_before    = len(before)
    n_after     = len(after)
    mean_before = float(before.mean())
    mean_after  = float(after.mean())
    std_before  = float(before.std(ddof=1))
    std_after   = float(after.std(ddof=1))

    # ── 正規性検定（Shapiro-Wilk）────────────────────────────────
    shapiro_before_p = float(stats.shapiro(before).pvalue)
    shapiro_after_p  = float(stats.shapiro(after).pvalue)
    normal_before    = shapiro_before_p >= 0.05
    normal_after     = shapiro_after_p  >= 0.05

    # ── t検定（Welch の t検定）──────────────────────────────────
    t_stat, t_pvalue = stats.ttest_ind(before, after, equal_var=False)
    t_stat   = float(t_stat)
    t_pvalue = float(t_pvalue)

    pooled_std = math.sqrt(
        ((n_before - 1) * std_before ** 2 + (n_after - 1) * std_after ** 2)
        / (n_before + n_after - 2)
    )
    cohens_d = abs(mean_after - mean_before) / pooled_std if pooled_std > 0 else 0.0

    # ── Mann-Whitney U検定 ────────────────────────────────────────
    mw_result = stats.mannwhitneyu(before, after, alternative="two-sided")
    mw_stat   = float(mw_result.statistic)
    mw_pvalue = float(mw_result.pvalue)

    rank_biserial_r = float(1.0 - (2.0 * mw_stat) / (n_before * n_after))

    # ── 推奨検定の選択 ────────────────────────────────────────────
    if normal_before and normal_after:
        recommended = "t"
        p_value     = t_pvalue
        effect_size = cohens_d
    else:
        recommended = "mw"
        p_value     = mw_pvalue
        effect_size = abs(rank_biserial_r)

    # ── verdict 判定（C-66 から反転）──────────────────────────────
    if p_value >= 0.05:
        verdict = "alert"
    elif effect_size < 0.5:
        verdict = "warning"
    else:
        verdict = "good"

    return {
        "n_before": n_before,
        "n_after":  n_after,
        "mean_before": mean_before,
        "mean_after":  mean_after,
        "std_before":  std_before,
        "std_after":   std_after,
        "shapiro_before_p": shapiro_before_p,
        "shapiro_after_p":  shapiro_after_p,
        "normal_before": normal_before,
        "normal_after":  normal_after,
        "t_stat":   t_stat,
        "t_pvalue": t_pvalue,
        "cohens_d": cohens_d,
        "mw_stat":         mw_stat,
        "mw_pvalue":       mw_pvalue,
        "rank_biserial_r": rank_biserial_r,
        "recommended": recommended,
        "p_value":     p_value,
        "effect_size": effect_size,
        "verdict":     verdict,
    }
```

- [ ] **Step 4: 全テスト PASS を確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/14_corrective_action/tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/14_corrective_action/tests/test_analyze.py \
        02_manufacturing/14_corrective_action/analyze.py
git commit -m "feat(C-70): analyze.py TDD — 8テスト all PASS（verdict 反転）"
```

---

### Task 3: app.py + STATUS.md

**Files:**
- Create: `02_manufacturing/14_corrective_action/app.py`
- Modify: `02_manufacturing/14_corrective_action/STATUS.md`

**重要:** visualize.py は作成しない。C-66 の `02_manufacturing/12_4m_change/visualize.py` を sys.path 経由で import する。

- [ ] **Step 1: app.py を作成**

`02_manufacturing/14_corrective_action/app.py`:
```python
"""是正処置（8D）効果検証 — 統計的有意差検定（t検定/Mann-Whitney）。"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# C-66 の visualize.py を転用
_C66 = Path(__file__).parent.parent / "12_4m_change"
if str(_C66) not in sys.path:
    sys.path.insert(0, str(_C66))

import analyze
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="是正処置効果検証", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f5f7fa; }
[data-testid="stHeader"] { background-color: #f5f7fa; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div style="background:#1e3a5f;color:white;padding:12px 20px;'
    'border-radius:6px;margin-bottom:16px">'
    '<h3 style="margin:0;font-family:BIZ UDGothic">'
    '📊 是正処置（8D）効果検証 — 統計的有意差検定（t検定/Mann-Whitney）</h3>'
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 設定")
    use_sample = st.button("サンプルデータを使用", use_container_width=True)
    uploaded   = st.file_uploader("CSVアップロード", type=["csv"])

    if use_sample:
        st.session_state["df"] = generate_sample_csv()
    elif uploaded:
        st.session_state["df"] = pd.read_csv(uploaded)

    df: pd.DataFrame | None = st.session_state.get("df")

    group_col = value_col = before_label = after_label = None
    run_btn = False

    if df is not None:
        cols      = df.columns.tolist()
        group_col = st.selectbox("グループ列", cols, key="group_col")
        value_col = st.selectbox("測定値列",   cols, index=min(1, len(cols) - 1), key="value_col")

        if group_col and group_col in df.columns:
            unique_vals  = sorted(df[group_col].dropna().unique().tolist())
            before_label = st.selectbox(
                "是正前ラベル", unique_vals, index=0, key="before_label"
            )
            after_label = st.selectbox(
                "是正後ラベル", unique_vals,
                index=min(1, len(unique_vals) - 1), key="after_label"
            )

        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    if not all([group_col, value_col, before_label, after_label]):
        st.error("列とラベルをすべて選択してください。")
        st.stop()
    if before_label == after_label:
        st.error("是正前ラベルと是正後ラベルは別の値を選択してください。")
        st.stop()
    try:
        result = analyze.run_analysis(df, group_col, value_col, before_label, after_label)
        st.session_state.update({
            "result":       result,
            "group_col":    group_col,
            "value_col":    value_col,
            "before_label": before_label,
            "after_label":  after_label,
            "uploaded_name": uploaded.name if uploaded else "sample_corrective_action.csv",
            "row_count": len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result       = st.session_state.get("result")
group_col    = st.session_state.get("group_col",    group_col)
value_col    = st.session_state.get("value_col",    value_col)
before_label = st.session_state.get("before_label", before_label)
after_label  = st.session_state.get("after_label",  after_label)

if not result:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI サマリー（4列）───────────────────────────────────────────
p_val   = result["p_value"]
eff     = result["effect_size"]
rec     = "t検定（Welch）" if result["recommended"] == "t" else "Mann-Whitney U"
verdict = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "是正効果確認", "warning": "軽微な効果", "alert": "効果不明"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("p値（推奨検定）", f"{p_val:.4f}")
c2.metric("効果量", f"{eff:.3f}")
c3.metric("推奨検定", rec)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">'
    f'n前={result["n_before"]} / n後={result["n_after"]}'
    f'</span></div>',
    unsafe_allow_html=True,
)

# ── チャート（C-66 の visualize.py を転用）───────────────────────
before_arr = pd.to_numeric(
    df[df[group_col] == before_label][value_col], errors="coerce"
).dropna().to_numpy(dtype=float)
after_arr = pd.to_numeric(
    df[df[group_col] == after_label][value_col], errors="coerce"
).dropna().to_numpy(dtype=float)

col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.hist_chart(before_arr, after_arr, before_label, after_label),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.box_chart(before_arr, after_arr, before_label, after_label),
        use_container_width=True,
    )

# ── 検定結果テーブル ──────────────────────────────────────────────
st.subheader("検定結果詳細")

_star = lambda rec_val: "★ 推奨" if result["recommended"] == rec_val else "—"
table_df = pd.DataFrame([
    {
        "検定手法": "t検定（Welch）",
        "統計量": f"{result['t_stat']:.4f}",
        "p値": f"{result['t_pvalue']:.4f}",
        "効果量": f"Cohen's d = {result['cohens_d']:.3f}",
        "推奨": _star("t"),
    },
    {
        "検定手法": "Mann-Whitney U",
        "統計量": f"{result['mw_stat']:.1f}",
        "p値": f"{result['mw_pvalue']:.4f}",
        "効果量": f"r = {result['rank_biserial_r']:.3f}",
        "推奨": _star("mw"),
    },
])
st.dataframe(table_df, hide_index=True, use_container_width=True)

st.subheader("正規性検定（Shapiro-Wilk）")
normality_df = pd.DataFrame([
    {
        "グループ": before_label,
        "n": result["n_before"],
        "平均": f"{result['mean_before']:.4f}",
        "標準偏差": f"{result['std_before']:.4f}",
        "Shapiro-Wilk p値": f"{result['shapiro_before_p']:.4f}",
        "正規性": "✓ 正規" if result["normal_before"] else "✗ 非正規",
    },
    {
        "グループ": after_label,
        "n": result["n_after"],
        "平均": f"{result['mean_after']:.4f}",
        "標準偏差": f"{result['std_after']:.4f}",
        "Shapiro-Wilk p値": f"{result['shapiro_after_p']:.4f}",
        "正規性": "✓ 正規" if result["normal_after"] else "✗ 非正規",
    },
])
st.dataframe(normality_df, hide_index=True, use_container_width=True)

# ── DB 書き込み（失敗してもアプリは継続）────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "corrective_action",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "corrective_action",
        datetime.now().strftime("%Y-%m"),
        "p_value", p_val, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")
```

- [ ] **Step 2: STATUS.md を production-ready に更新**

`02_manufacturing/14_corrective_action/STATUS.md`:
```markdown
# C-70 是正処置（8D）効果検証

- name: 是正処置（8D）効果検証
- industry: 製造
- department: 品質
- status: production-ready
```

- [ ] **Step 3: Syntax チェック**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "
import ast
with open('02_manufacturing/14_corrective_action/app.py', encoding='utf-8') as f:
    ast.parse(f.read())
print('app.py: syntax OK')
"
```

期待: `app.py: syntax OK`

- [ ] **Step 4: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/14_corrective_action/app.py \
        02_manufacturing/14_corrective_action/STATUS.md
git commit -m "feat(C-70): app.py + STATUS.md production-ready（C-66 visualize 転用）"
```

---

### Task 4: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`
- Modify: `catalog.yml`

- [ ] **Step 1: dashboard.py を Read して CARDS リストを確認**

`02_manufacturing/09_unified_dashboard/dashboard.py` を Read し、現在の末尾カード（`defect_pareto`）を確認する。

- [ ] **Step 2: CARDS リストに corrective_action カードを追加**

`defect_pareto` カードの直後に以下を追加:

```python
    {"system_id": "corrective_action", "metric": "p_value",
     "title": "是正処置効果（p値）", "fmt": lambda v: f"{v:.4f}"},
```

追加後の末尾:
```python
    {"system_id": "defect_pareto", "metric": "top_mode_pct",
     "title": "最多不良モード構成比", "fmt": lambda v: f"{v:.1f}%"},
    {"system_id": "corrective_action", "metric": "p_value",
     "title": "是正処置効果（p値）", "fmt": lambda v: f"{v:.4f}"},
]
```

- [ ] **Step 3: catalog.yml に C-70 エントリを追加**

`catalog.yml` を Read し、C-69 エントリの直後に追記:

```yaml
- id: "C-70"
  name: "是正処置（8D）効果検証 — 統計的有意差検定（t検定/Mann-Whitney）"
  industry: "製造"
  department: "品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/14_corrective_action"
  demo: "streamlit run 02_manufacturing/14_corrective_action/app.py"
  description: |
    是正処置（8Dメソッド）実施前後の品質データを比較し、統計的有意差を自動判定。
    t検定（Welch）とMann-Whitney U検定を両方実行し、Shapiro-Wilk正規性検定で推奨手法を自動選択。
    有意差あり + 効果量大 → "good"（是正効果確認）という C-66 と逆の verdict 設計が特徴。
```

- [ ] **Step 4: 全テスト PASS を確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/14_corrective_action/tests/ -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-70): C-63ダッシュボード + catalog.yml に C-70 追加"
```

---

## 完了チェックリスト

- [ ] `sample_data.py` — before μ=12.0 / after μ=8.0, n=30×2、seed=42
- [ ] `tests/test_analyze.py` — 8テスト all PASS（verdict 反転を確認）
- [ ] `analyze.py` — C-66 と同一ロジック、verdict のみ反転
- [ ] `app.py` — C-66 visualize.py を sys.path 経由で import、ラベル "是正効果確認/軽微な効果/効果不明"
- [ ] `STATUS.md` — production-ready
- [ ] `dashboard.py` — corrective_action カード追加
- [ ] `catalog.yml` — C-70 エントリ追加
