# 工程間品質相関分析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 複数工程の測定値（Wide CSV）から Pearson 相関行列を計算し、ヒートマップ + 散布図で工程間の品質影響関係を可視化する。

**Architecture:** analyze.py（純粋関数）→ visualize.py（ヒートマップ + 散布図）→ app.py（Streamlit + DB）の3層構成。C-66/C-70 と同パターン。verdict は max |r| の絶対値で判定（≥0.7=good / ≥0.4=warning / <0.4=alert）。

**Tech Stack:** Python 3.11+, Streamlit, Plotly, pandas, numpy, scipy（pearsonr）, pytest

---

## File Map

| ファイル | 操作 | 役割 |
|---------|------|------|
| `02_manufacturing/15_process_correlation/sample_data.py` | 新規 | デモCSV生成（5工程×50ロット、A-B強相関）|
| `02_manufacturing/15_process_correlation/tests/__init__.py` | 新規 | pytest パッケージ宣言 |
| `02_manufacturing/15_process_correlation/tests/test_analyze.py` | 新規 | 8テスト TDD |
| `02_manufacturing/15_process_correlation/analyze.py` | 新規 | Pearson 相関行列 + verdict |
| `02_manufacturing/15_process_correlation/visualize.py` | 新規 | heatmap_chart + scatter_chart |
| `02_manufacturing/15_process_correlation/app.py` | 新規 | Streamlit UI（multiselect + 2チャート + テーブル）|
| `02_manufacturing/15_process_correlation/STATUS.md` | 新規 | production-ready |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | 修正 | process_correlation カード追加 |
| `catalog.yml` | 修正 | C-67 エントリ追加 |

---

### Task 1: scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/15_process_correlation/tests/__init__.py`
- Create: `02_manufacturing/15_process_correlation/STATUS.md`
- Create: `02_manufacturing/15_process_correlation/sample_data.py`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio\02_manufacturing\15_process_correlation\tests"
```

- [ ] **Step 2: tests/__init__.py を作成（空ファイル）**

`02_manufacturing/15_process_correlation/tests/__init__.py`:
```python
```

- [ ] **Step 3: STATUS.md を作成**

`02_manufacturing/15_process_correlation/STATUS.md`:
```markdown
# C-67 工程間品質相関分析

- name: 工程間品質相関分析
- industry: 製造
- department: 品質
- status: in-progress
```

- [ ] **Step 4: sample_data.py を作成**

`02_manufacturing/15_process_correlation/sample_data.py`:
```python
"""工程間品質相関分析 デモ用サンプルデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    5工程（A〜E）× 50ロットのデモデータを生成する。

    相関設定:
    - process_A → process_B: r ≈ 0.85（強い正相関）
    - process_B → process_C: r ≈ 0.75（強い正相関）
    - process_D, process_E: A と無相関（独立）

    → max_abs_r ≥ 0.7 → verdict = "good"（強い相関あり）が期待される
    """
    rng = np.random.default_rng(42)
    n = 50

    process_A = rng.normal(10.0, 2.0, n)
    process_B = 0.9 * process_A + rng.normal(0, 0.8, n)
    process_C = 0.8 * process_B + rng.normal(0, 1.2, n)
    process_D = rng.normal(8.0, 1.5, n)
    process_E = rng.normal(5.0, 1.0, n)

    df = pd.DataFrame({
        "lot_id":    [f"L{i+1:03d}" for i in range(n)],
        "process_A": np.round(process_A, 4),
        "process_B": np.round(process_B, 4),
        "process_C": np.round(process_C, 4),
        "process_D": np.round(process_D, 4),
        "process_E": np.round(process_E, 4),
    })
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_process_correlation.csv"
    generate_sample_csv(str(out))
    print(f"Generated: {out}")
```

- [ ] **Step 5: 動作確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python 02_manufacturing/15_process_correlation/sample_data.py
```

期待出力: `Generated: ...sample_process_correlation.csv`

- [ ] **Step 6: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/15_process_correlation/
git commit -m "feat(C-67): scaffold + sample_data.py（5工程×50ロット、A-B強相関）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/15_process_correlation/tests/test_analyze.py`
- Create: `02_manufacturing/15_process_correlation/analyze.py`

- [ ] **Step 1: テストを書く**

`02_manufacturing/15_process_correlation/tests/test_analyze.py`:
```python
"""analyze.run_analysis の相関計算ロジック ユニットテスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _strong_corr() -> pd.DataFrame:
    """強い正相関（r > 0.7）→ verdict = 'good'"""
    rng = np.random.default_rng(0)
    a = rng.normal(10.0, 2.0, 50)
    b = 0.9 * a + rng.normal(0, 0.8, 50)
    return pd.DataFrame({"A": a, "B": b})


def _medium_corr() -> pd.DataFrame:
    """中程度の相関（0.4 ≤ r < 0.7）→ verdict = 'warning'
    理論値: r = 0.5*Var(A) / sqrt(Var(A) * (0.25*Var(A) + Var(noise)))
           = 2 / sqrt(4 * 5) ≈ 0.447
    """
    rng = np.random.default_rng(5)
    a = rng.normal(10.0, 2.0, 50)
    b = 0.5 * a + rng.normal(0, 2.0, 50)
    return pd.DataFrame({"A": a, "B": b})


def _no_corr() -> pd.DataFrame:
    """無相関（r < 0.4）→ verdict = 'alert'"""
    rng = np.random.default_rng(99)
    a = rng.normal(10.0, 2.0, 50)
    b = rng.normal(8.0, 2.0, 50)
    return pd.DataFrame({"A": a, "B": b})


def _three_col() -> pd.DataFrame:
    """3工程: A-B 強相関、C は独立 → top_pair が (A, B) または (B, A)"""
    rng = np.random.default_rng(7)
    a = rng.normal(10.0, 2.0, 50)
    b = 0.9 * a + rng.normal(0, 0.8, 50)
    c = rng.normal(8.0, 2.0, 50)
    return pd.DataFrame({"A": a, "B": b, "C": c})


def test_corr_matrix_shape():
    """corr_df の shape が (工程数, 工程数) であること"""
    result = analyze.run_analysis(_three_col(), ["A", "B", "C"])
    assert result["corr_df"].shape == (3, 3)
    assert result["pvalue_df"].shape == (3, 3)


def test_corr_diagonal_ones():
    """相関行列の対角要素がすべて 1.0 であること"""
    result = analyze.run_analysis(_strong_corr(), ["A", "B"])
    diag = [result["corr_df"].iloc[i, i] for i in range(2)]
    assert all(abs(v - 1.0) < 1e-9 for v in diag)


def test_verdict_good():
    """強い相関（|r| ≥ 0.7）→ verdict = 'good'"""
    result = analyze.run_analysis(_strong_corr(), ["A", "B"])
    assert result["max_abs_r"] >= 0.7
    assert result["verdict"] == "good"


def test_verdict_warning():
    """中程度の相関（0.4 ≤ |r| < 0.7）→ verdict = 'warning'"""
    result = analyze.run_analysis(_medium_corr(), ["A", "B"])
    assert 0.4 <= result["max_abs_r"] < 0.7
    assert result["verdict"] == "warning"


def test_verdict_alert():
    """無相関（|r| < 0.4）→ verdict = 'alert'"""
    result = analyze.run_analysis(_no_corr(), ["A", "B"])
    assert result["max_abs_r"] < 0.4
    assert result["verdict"] == "alert"


def test_top_pair_is_max():
    """top_pair の |r| が全ペアの最大値と一致すること"""
    result = analyze.run_analysis(_three_col(), ["A", "B", "C"])
    assert abs(result["top_r"]) == pytest.approx(result["max_abs_r"], rel=1e-9)
    assert set(result["top_pair"]) == {"A", "B"}


def test_output_keys():
    """全9出力キーが揃っていること"""
    result = analyze.run_analysis(_strong_corr(), ["A", "B"])
    required_keys = {
        "corr_df", "pvalue_df", "top_pair", "top_r",
        "top_pvalue", "max_abs_r", "n_samples", "n_processes", "verdict",
    }
    assert required_keys <= set(result.keys())


def test_insufficient_data_raises():
    """工程 < 2 または n < 3 で ValueError が発生すること"""
    df = pd.DataFrame({"A": [1.0, 2.0], "B": [1.0, 2.0]})
    with pytest.raises(ValueError, match="3"):
        analyze.run_analysis(df, ["A", "B"])

    df2 = pd.DataFrame({"A": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="2"):
        analyze.run_analysis(df2, ["A"])
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/15_process_correlation/tests/test_analyze.py -v 2>&1 | head -10
```

期待: `ModuleNotFoundError: No module named 'analyze'`

- [ ] **Step 3: analyze.py を実装**

`02_manufacturing/15_process_correlation/analyze.py`:
```python
"""工程間品質相関分析 Pearson 相関行列計算ロジック（純粋関数モジュール）。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import pearsonr


def run_analysis(
    df: pd.DataFrame,
    process_cols: list[str],
) -> dict:
    """
    複数工程の測定値から Pearson 相関行列と工程間の品質影響強度を計算する。

    verdict 基準（最強相関ペアの絶対値で判定）:
    - max |r| ≥ 0.7 → "good"    （強い相関: 工程間影響が明確）
    - max |r| ≥ 0.4 → "warning" （中程度の相関: 要監視）
    - max |r| < 0.4 → "alert"   （相関弱: 工程間に関係なし）

    Parameters
    ----------
    df : pd.DataFrame
    process_cols : list[str]  工程列名リスト（最低2列）

    Returns
    -------
    dict
        corr_df, pvalue_df, top_pair, top_r, top_pvalue,
        max_abs_r, n_samples, n_processes, verdict

    Raises
    ------
    ValueError
        工程列 < 2 のとき、または有効サンプル数 n < 3 のとき
    """
    if len(process_cols) < 2:
        raise ValueError(
            f"工程列は最低 2 列必要です。現在 {len(process_cols)} 列が指定されています。"
        )

    data = df[process_cols].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(data)

    if n < 3:
        raise ValueError(
            f"有効サンプル数が不足しています（n={n}、最低 3 必要）。"
        )

    # ── 相関行列（Pearson）────────────────────────────────────────
    corr_df = data.corr(method="pearson")

    # ── p値行列 ───────────────────────────────────────────────────
    pvalue_dict: dict[str, dict[str, float]] = {col: {} for col in process_cols}
    for col1 in process_cols:
        for col2 in process_cols:
            if col1 == col2:
                pvalue_dict[col1][col2] = 0.0
            else:
                _, p = pearsonr(data[col1].to_numpy(), data[col2].to_numpy())
                pvalue_dict[col1][col2] = float(p)
    pvalue_df = pd.DataFrame(pvalue_dict, index=process_cols)

    # ── 最強相関ペアを特定（対角を除く |r| 最大）────────────────
    corr_abs = corr_df.abs().copy()
    np.fill_diagonal(corr_abs.values, 0.0)
    max_idx = corr_abs.stack().idxmax()
    top_pair: tuple[str, str] = (str(max_idx[0]), str(max_idx[1]))
    top_r     = float(corr_df.loc[top_pair[0], top_pair[1]])
    top_pvalue = float(pvalue_df.loc[top_pair[0], top_pair[1]])
    max_abs_r  = float(abs(top_r))

    # ── verdict 判定 ──────────────────────────────────────────────
    if max_abs_r >= 0.7:
        verdict = "good"
    elif max_abs_r >= 0.4:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "corr_df":     corr_df,
        "pvalue_df":   pvalue_df,
        "top_pair":    top_pair,
        "top_r":       top_r,
        "top_pvalue":  top_pvalue,
        "max_abs_r":   max_abs_r,
        "n_samples":   n,
        "n_processes": len(process_cols),
        "verdict":     verdict,
    }
```

- [ ] **Step 4: 全テスト PASS を確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/15_process_correlation/tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/15_process_correlation/tests/test_analyze.py \
        02_manufacturing/15_process_correlation/analyze.py
git commit -m "feat(C-67): analyze.py TDD — 8テスト all PASS（Pearson 相関行列 + verdict）"
```

---

### Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/15_process_correlation/visualize.py`

- [ ] **Step 1: visualize.py を作成**

`02_manufacturing/15_process_correlation/visualize.py`:
```python
"""工程間品質相関分析 Plotly 描画モジュール。"""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go

_NAVY    = "#1e3a5f"
_ALERT   = "#dc2626"
_GREEN   = "#16a34a"
_WARNING = "#d97706"
_BG      = "#f5f7fa"
_FONT    = "BIZ UDGothic"


def heatmap_chart(corr_df: pd.DataFrame, pvalue_df: pd.DataFrame) -> go.Figure:
    """Pearson 相関行列のヒートマップ（-1=青〜0=白〜+1=赤）。
    p < 0.05 のセルには r 値に * を付与する。
    """
    cols = corr_df.columns.tolist()
    z = corr_df.values.tolist()

    text: list[list[str]] = []
    for i, row_col in enumerate(cols):
        row: list[str] = []
        for j, col in enumerate(cols):
            r_val = corr_df.iloc[i, j]
            p_val = pvalue_df.iloc[i, j]
            cell = f"{r_val:.2f}"
            if i != j and p_val < 0.05:
                cell += "*"
            row.append(cell)
        text.append(row)

    colorscale = [
        [0.0, _NAVY],
        [0.5, "#ffffff"],
        [1.0, _ALERT],
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=cols,
        y=cols,
        text=text,
        texttemplate="%{text}",
        colorscale=colorscale,
        zmin=-1,
        zmax=1,
        colorbar=dict(title="r", thickness=12),
    ))
    fig.update_layout(
        title=dict(text="工程間 Pearson 相関行列", font=dict(size=14, color=_NAVY)),
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=400,
        margin=dict(l=60, r=60, t=50, b=60),
    )
    return fig


def scatter_chart(
    df: pd.DataFrame,
    col_x: str,
    col_y: str,
    r: float,
    pvalue: float,
) -> go.Figure:
    """最強相関ペアの散布図 + 回帰直線。"""
    x = pd.to_numeric(df[col_x], errors="coerce").dropna().to_numpy(dtype=float)
    y = pd.to_numeric(df[col_y], errors="coerce").dropna().to_numpy(dtype=float)

    min_len = min(len(x), len(y))
    x, y = x[:min_len], y[:min_len]

    m, b = np.polyfit(x, y, 1)
    x_line = np.array([x.min(), x.max()])
    y_line = m * x_line + b

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="markers",
        name="データ",
        marker=dict(color=_WARNING, size=8, opacity=0.7),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode="lines",
        name="回帰直線",
        line=dict(color=_NAVY, width=2),
        showlegend=False,
    ))
    fig.update_layout(
        title=dict(
            text=f"{col_x} vs {col_y}  r={r:.3f}  p={pvalue:.4f}",
            font=dict(size=13, color=_NAVY),
        ),
        xaxis_title=col_x,
        yaxis_title=col_y,
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        height=350,
        margin=dict(l=60, r=30, t=50, b=50),
    )
    return fig
```

- [ ] **Step 2: syntax チェック**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "
import ast
with open('02_manufacturing/15_process_correlation/visualize.py', encoding='utf-8') as f:
    ast.parse(f.read())
print('visualize.py: syntax OK')
"
```

期待: `visualize.py: syntax OK`

- [ ] **Step 3: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/15_process_correlation/visualize.py
git commit -m "feat(C-67): visualize.py — heatmap_chart + scatter_chart"
```

---

### Task 4: app.py + STATUS.md

**Files:**
- Create: `02_manufacturing/15_process_correlation/app.py`
- Modify: `02_manufacturing/15_process_correlation/STATUS.md`

- [ ] **Step 1: app.py を作成**

`02_manufacturing/15_process_correlation/app.py`:
```python
"""工程間品質相関分析 — Pearson 相関行列 × ヒートマップ。"""
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

import analyze
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="工程間品質相関分析", page_icon="📊", layout="wide")

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
    '📊 工程間品質相関分析 — Pearson 相関行列 × ヒートマップ</h3>'
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

    process_cols: list[str] = []
    run_btn = False

    if df is not None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            st.error("数値列が見つかりません。")
        else:
            process_cols = st.multiselect(
                "工程列を選択（2列以上）",
                numeric_cols,
                default=numeric_cols,
                key="process_cols",
            )
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    if len(process_cols) < 2:
        st.error("工程列を 2 列以上選択してください。")
        st.stop()
    try:
        result = analyze.run_analysis(df, process_cols)
        st.session_state.update({
            "result":        result,
            "process_cols":  process_cols,
            "uploaded_name": uploaded.name if uploaded else "sample_process_correlation.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result       = st.session_state.get("result")
process_cols = st.session_state.get("process_cols", process_cols)

if not result:
    st.info("サイドバーで工程列を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI サマリー（4列）───────────────────────────────────────────
max_abs_r = result["max_abs_r"]
top_pair  = result["top_pair"]
top_r     = result["top_r"]
verdict   = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "強い相関あり", "warning": "中程度の相関", "alert": "相関なし"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("有効サンプル数", f"{result['n_samples']}件")
c2.metric("工程数", f"{result['n_processes']}工程")
c3.metric(
    "最強相関ペア",
    f"{top_pair[0]} × {top_pair[1]}",
    delta=f"r={top_r:.3f}",
)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">max |r|={max_abs_r:.3f}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.heatmap_chart(result["corr_df"], result["pvalue_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.scatter_chart(
            df[process_cols],
            top_pair[0], top_pair[1],
            top_r, result["top_pvalue"],
        ),
        use_container_width=True,
    )

# ── 相関行列テーブル（p値付き）───────────────────────────────────
st.subheader("相関行列詳細（* p < 0.05）")
corr_display = result["corr_df"].copy()
pval_display = result["pvalue_df"]

rows = []
for i, col1 in enumerate(process_cols):
    row = {"工程": col1}
    for col2 in process_cols:
        r_val = corr_display.loc[col1, col2]
        p_val = pval_display.loc[col1, col2]
        cell = f"{r_val:.3f}"
        if col1 != col2 and p_val < 0.05:
            cell += "*"
        row[col2] = cell
    rows.append(row)

st.dataframe(pd.DataFrame(rows).set_index("工程"), use_container_width=True)

# ── DB 書き込み（失敗してもアプリは継続）────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "process_correlation",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "process_correlation",
        datetime.now().strftime("%Y-%m"),
        "max_r", max_abs_r, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")
```

- [ ] **Step 2: STATUS.md を production-ready に更新**

`02_manufacturing/15_process_correlation/STATUS.md`:
```markdown
# C-67 工程間品質相関分析

- name: 工程間品質相関分析
- industry: 製造
- department: 品質
- status: production-ready
```

- [ ] **Step 3: syntax チェック**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "
import ast
with open('02_manufacturing/15_process_correlation/app.py', encoding='utf-8') as f:
    ast.parse(f.read())
print('app.py: syntax OK')
"
```

期待: `app.py: syntax OK`

- [ ] **Step 4: 全テスト確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/15_process_correlation/tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/15_process_correlation/app.py \
        02_manufacturing/15_process_correlation/STATUS.md
git commit -m "feat(C-67): app.py + STATUS.md production-ready（ヒートマップ + 散布図 + multiselect）"
```

---

### Task 5: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`
- Modify: `catalog.yml`

- [ ] **Step 1: dashboard.py を Read して CARDS リストの末尾を確認**

`02_manufacturing/09_unified_dashboard/dashboard.py` を Read し、現在の末尾カード（`corrective_action`）を確認する。

- [ ] **Step 2: CARDS リストに process_correlation カードを追加**

`corrective_action` カードの直後に追加:

```python
    {"system_id": "process_correlation", "metric": "max_r",
     "title": "工程間最強相関（r）", "fmt": lambda v: f"{v:.3f}"},
```

- [ ] **Step 3: catalog.yml を Read して末尾を確認**

`catalog.yml` を Read し、C-70 エントリの直後に追記:

```yaml
- id: "C-67"
  name: "工程間品質相関分析 — Pearson 相関行列 × ヒートマップ"
  industry: "製造"
  department: "品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/15_process_correlation"
  demo: "streamlit run 02_manufacturing/15_process_correlation/app.py"
  description: |
    複数工程の測定値（Wide形式CSV）をアップロードし、Pearson相関行列を自動計算。
    工程間の品質影響関係をヒートマップで可視化し、最強相関ペアを散布図で詳細表示。
    max |r| ≥ 0.7 → "good"（強い相関あり）という verdict 設計で工程管理改善を支援。
```

- [ ] **Step 4: 全テスト確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/15_process_correlation/tests/ -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-67): C-63ダッシュボード + catalog.yml に C-67 追加"
```

---

## 完了チェックリスト

- [ ] `sample_data.py` — 5工程×50ロット、A-B強相関、seed=42
- [ ] `tests/test_analyze.py` — 8テスト all PASS
- [ ] `analyze.py` — Pearson 相関行列 + p値行列 + verdict（絶対値判定）
- [ ] `visualize.py` — heatmap_chart（テキスト付き）+ scatter_chart（回帰直線）
- [ ] `app.py` — multiselect 工程列選択、KPI 4列、2チャート、テーブル
- [ ] `STATUS.md` — production-ready
- [ ] `dashboard.py` — process_correlation カード追加
- [ ] `catalog.yml` — C-67 エントリ追加
