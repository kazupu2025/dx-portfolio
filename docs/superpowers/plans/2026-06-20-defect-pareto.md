# 不良モード別パレート × 時系列複合分析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 月次集計済み不良モード別件数 CSV からパレート分析 + 時系列推移を可視化し、vital few 自動特定と verdict を DB 書き込み・C-63 ダッシュボードに連携する。

**Architecture:** analyze.py（純粋関数）→ visualize.py（Plotly 2チャート）→ app.py（Streamlit UI + DB統合）の3層分離。TDD: test_analyze.py を先に書いて FAIL 確認後、analyze.py を実装して PASS。

**Tech Stack:** Python 3.11+, Streamlit, Plotly (make_subplots / secondary_y), pandas, numpy, scipy（使用なし / 純集計のみ）, pytest

---

## File Map

| ファイル | 操作 | 役割 |
|---------|------|------|
| `02_manufacturing/13_defect_pareto/sample_data.py` | 新規 | デモCSV生成（5モード×12ヶ月） |
| `02_manufacturing/13_defect_pareto/tests/__init__.py` | 新規 | pytest パッケージ宣言 |
| `02_manufacturing/13_defect_pareto/tests/test_analyze.py` | 新規 | 8テスト（TDD） |
| `02_manufacturing/13_defect_pareto/analyze.py` | 新規 | 集計・パレート・verdict ロジック |
| `02_manufacturing/13_defect_pareto/visualize.py` | 新規 | pareto_chart / trend_chart |
| `02_manufacturing/13_defect_pareto/app.py` | 新規 | Streamlit UI + DB統合 |
| `02_manufacturing/13_defect_pareto/STATUS.md` | 新規 | production-ready |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | 修正 | CARDS に defect_pareto 追加 |
| `catalog.yml` | 修正 | C-69 エントリ追加 |

---

### Task 1: scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/13_defect_pareto/sample_data.py`
- Create: `02_manufacturing/13_defect_pareto/STATUS.md`
- Create: `02_manufacturing/13_defect_pareto/tests/__init__.py`

- [ ] **Step 1: ディレクトリを作成し STATUS.md を書く**

```bash
mkdir -p dx-portfolio/02_manufacturing/13_defect_pareto/tests
```

`02_manufacturing/13_defect_pareto/STATUS.md`:
```markdown
# C-69 不良モード別パレート × 時系列複合分析

- name: 不良モード別パレート × 時系列複合分析
- industry: 製造
- department: 生産・品質
- status: in-progress
```

- [ ] **Step 2: tests/__init__.py を作成**

`02_manufacturing/13_defect_pareto/tests/__init__.py` (空ファイル):
```python
```

- [ ] **Step 3: sample_data.py を作成**

`02_manufacturing/13_defect_pareto/sample_data.py`:
```python
"""不良モード別パレート × 時系列 デモ用サンプルデータ生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_csv(path: str | None = None) -> pd.DataFrame:
    """
    5不良モード × 12ヶ月（2024-01〜2024-12）= 60行のサンプルデータを生成する。

    設定:
    - バリ: 全体の約50%（vital few に確実に入る）
    - 寸法不良: 約25%
    - 表面傷: 約15%
    - 欠け: 約7%
    - 異物混入: 約3%
    直近月（2024-12）: 前月比 +25% → verdict = "alert" が期待される
    """
    rng = np.random.default_rng(42)
    modes = ["バリ", "寸法不良", "表面傷", "欠け", "異物混入"]
    base_counts = [50, 25, 15, 7, 3]
    months = [f"2024-{m:02d}" for m in range(1, 13)]

    rows = []
    for i, month in enumerate(months):
        scale = 1.25 if i == 11 else 1.0
        for mode, base in zip(modes, base_counts):
            count = max(1, int(base * scale + rng.integers(-3, 4)))
            rows.append({"year_month": month, "defect_mode": mode, "count": count})

    df = pd.DataFrame(rows)
    if path:
        df.to_csv(path, index=False, encoding="utf-8-sig")
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "sample_defect_pareto.csv"
    generate_sample_csv(str(out))
    print(f"Generated: {out}")
```

- [ ] **Step 4: 動作確認**

```bash
cd dx-portfolio
python 02_manufacturing/13_defect_pareto/sample_data.py
```

期待出力: `Generated: ...sample_defect_pareto.csv`

- [ ] **Step 5: コミット**

```bash
git add dx-portfolio/02_manufacturing/13_defect_pareto/
git commit -m "feat(C-69): scaffold + sample_data.py（5モード×12ヶ月）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/13_defect_pareto/tests/test_analyze.py`
- Create: `02_manufacturing/13_defect_pareto/analyze.py`

- [ ] **Step 1: テストを書く（実装前）**

`02_manufacturing/13_defect_pareto/tests/test_analyze.py`:
```python
"""analyze.run_analysis の集計・パレートロジック ユニットテスト。"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze


def _make_df(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["year_month", "defect_mode", "count"])


def _sample_df() -> pd.DataFrame:
    """5モード × 2ヶ月（バリが最多）"""
    return _make_df([
        ("2024-01", "バリ",     50),
        ("2024-01", "寸法不良", 20),
        ("2024-01", "表面傷",   15),
        ("2024-01", "欠け",     10),
        ("2024-01", "異物混入",  5),
        ("2024-02", "バリ",     45),
        ("2024-02", "寸法不良", 22),
        ("2024-02", "表面傷",   14),
        ("2024-02", "欠け",      9),
        ("2024-02", "異物混入",  4),
    ])


def _alert_df() -> pd.DataFrame:
    """直近月が前月比 +30% → alert"""
    return _make_df([
        ("2024-01", "バリ",     40),
        ("2024-01", "寸法不良", 20),
        ("2024-02", "バリ",     55),
        ("2024-02", "寸法不良", 27),
    ])


def _good_df() -> pd.DataFrame:
    """直近月が前月比 -20% → good"""
    return _make_df([
        ("2024-01", "バリ",     50),
        ("2024-01", "寸法不良", 20),
        ("2024-02", "バリ",     37),
        ("2024-02", "寸法不良", 16),
    ])


def _warning_df() -> pd.DataFrame:
    """直近月が前月と同数 → warning"""
    return _make_df([
        ("2024-01", "バリ",     50),
        ("2024-01", "寸法不良", 20),
        ("2024-02", "バリ",     50),
        ("2024-02", "寸法不良", 20),
    ])


def test_pareto_sorted_descending():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    counts = result["pareto_df"]["count"].tolist()
    assert counts == sorted(counts, reverse=True), "pareto_df は件数降順であること"


def test_cumulative_pct_reaches_100():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    last = result["pareto_df"]["cumulative_pct"].iloc[-1]
    assert abs(last - 100.0) < 1e-6, f"累積%の最終値が 100.0 であること: {last}"


def test_vital_few_contains_top_mode():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    assert result["top_mode"] in result["vital_few"]
    assert result["vital_few"][0] == result["top_mode"], "vital_few の先頭が top_mode であること"


def test_vital_few_threshold():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    pareto_df = result["pareto_df"]
    vital_few = result["vital_few"]
    last_vital = vital_few[-1]
    cum_at_last = pareto_df.loc[
        pareto_df["defect_mode"] == last_vital, "cumulative_pct"
    ].iloc[0]
    assert cum_at_last >= 80.0, f"vital_few の累積% が 80% 以上であること: {cum_at_last}"


def test_verdict_good():
    result = analyze.run_analysis(_good_df(), "year_month", "defect_mode", "count")
    assert result["verdict"] == "good", f"前月比 -20% は 'good' であること: {result['verdict']}"


def test_verdict_warning():
    result = analyze.run_analysis(_warning_df(), "year_month", "defect_mode", "count")
    assert result["verdict"] == "warning", f"前月と同数は 'warning' であること: {result['verdict']}"


def test_verdict_alert():
    result = analyze.run_analysis(_alert_df(), "year_month", "defect_mode", "count")
    assert result["verdict"] == "alert", f"前月比 +30% は 'alert' であること: {result['verdict']}"


def test_output_keys():
    result = analyze.run_analysis(_sample_df(), "year_month", "defect_mode", "count")
    required = {
        "pareto_df", "trend_df", "top_mode", "top_mode_pct",
        "total_count", "vital_few", "latest_month",
        "latest_total", "prev_total", "verdict",
    }
    missing = required - set(result.keys())
    assert not missing, f"出力 dict にキーが不足: {missing}"
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
cd dx-portfolio
python -m pytest 02_manufacturing/13_defect_pareto/tests/test_analyze.py -v 2>&1 | head -20
```

期待: `ModuleNotFoundError: No module named 'analyze'` (analyze.py がまだない)

- [ ] **Step 3: analyze.py を実装**

`02_manufacturing/13_defect_pareto/analyze.py`:
```python
"""不良モード別パレート × 時系列複合分析ロジック（純粋関数モジュール）。"""
from __future__ import annotations
import pandas as pd


def run_analysis(
    df: pd.DataFrame,
    date_col: str,
    mode_col: str,
    count_col: str,
) -> dict:
    """
    月次集計済み不良モードデータをパレート分析・時系列推移・verdict に変換する。

    Parameters
    ----------
    df : pd.DataFrame
        月次集計済み不良モードデータ（year_month, defect_mode, count）
    date_col : str
        年月列名
    mode_col : str
        不良モード列名
    count_col : str
        件数列名

    Returns
    -------
    dict
        pareto_df, trend_df, top_mode, top_mode_pct, total_count,
        vital_few, latest_month, latest_total, prev_total, verdict
    """
    df = df.copy()
    df[count_col] = pd.to_numeric(df[count_col], errors="coerce")
    df = df.dropna(subset=[count_col])
    df[count_col] = df[count_col].astype(int)

    n_modes  = df[mode_col].nunique()
    n_months = df[date_col].nunique()
    if n_modes < 2:
        raise ValueError(f"不良モードは最低 2 種類必要です。検出: {n_modes}")
    if n_months < 2:
        raise ValueError(f"月数は最低 2 ヶ月必要です。検出: {n_months}")

    # ── パレート集計（全期間合計）────────────────────────────────
    mode_totals = df.groupby(mode_col)[count_col].sum().sort_values(ascending=False)
    total_count = int(mode_totals.sum())
    top_mode    = str(mode_totals.index[0])
    top_mode_pct = float(mode_totals.iloc[0] / total_count * 100)

    cum_counts = mode_totals.cumsum()
    cum_pct    = cum_counts / total_count * 100

    pareto_df = pd.DataFrame({
        mode_col:        mode_totals.index.tolist(),
        "count":         mode_totals.values.tolist(),
        "cumulative_pct": cum_pct.values.tolist(),
    }).reset_index(drop=True)

    # ── vital few（累積 80% 以内のモード、最低 1 件）────────────
    vital_few: list[str] = []
    for _, row in pareto_df.iterrows():
        vital_few.append(str(row[mode_col]))
        if row["cumulative_pct"] >= 80.0:
            break

    # ── 月別推移ピボット（列順: パレート降順）───────────────────
    trend_df = df.pivot_table(
        index=date_col, columns=mode_col,
        values=count_col, aggfunc="sum", fill_value=0,
    )
    col_order = [c for c in mode_totals.index if c in trend_df.columns]
    trend_df  = trend_df[col_order]
    trend_df  = trend_df.reindex(sorted(trend_df.index.tolist()))

    # ── verdict（直近月 vs 前月 合計件数比較）────────────────────
    sorted_months = sorted(df[date_col].unique().tolist())
    month_totals  = df.groupby(date_col)[count_col].sum()

    latest_month = sorted_months[-1]
    latest_total = int(month_totals.get(latest_month, 0))

    if len(sorted_months) >= 2:
        prev_month = sorted_months[-2]
        prev_total = int(month_totals.get(prev_month, 0))
    else:
        prev_total = latest_total

    if prev_total == 0:
        verdict = "warning"
    elif latest_total < prev_total * 0.9:
        verdict = "good"
    elif latest_total <= prev_total * 1.1:
        verdict = "warning"
    else:
        verdict = "alert"

    return {
        "pareto_df":    pareto_df,
        "trend_df":     trend_df,
        "top_mode":     top_mode,
        "top_mode_pct": top_mode_pct,
        "total_count":  total_count,
        "vital_few":    vital_few,
        "latest_month": latest_month,
        "latest_total": latest_total,
        "prev_total":   prev_total,
        "verdict":      verdict,
    }
```

- [ ] **Step 4: テストが PASS することを確認**

```bash
cd dx-portfolio
python -m pytest 02_manufacturing/13_defect_pareto/tests/test_analyze.py -v
```

期待: `8 passed` （全テスト PASS）

- [ ] **Step 5: コミット**

```bash
git add dx-portfolio/02_manufacturing/13_defect_pareto/tests/test_analyze.py \
        dx-portfolio/02_manufacturing/13_defect_pareto/analyze.py
git commit -m "feat(C-69): analyze.py TDD — 8テスト all PASS"
```

---

### Task 3: visualize.py — パレート図 + 月次推移グラフ

**Files:**
- Create: `02_manufacturing/13_defect_pareto/visualize.py`

- [ ] **Step 1: visualize.py を作成**

`02_manufacturing/13_defect_pareto/visualize.py`:
```python
"""不良モード別パレート × 時系列複合分析 Plotly 描画モジュール。"""
from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

_NAVY    = "#1e3a5f"
_ALERT   = "#dc2626"
_GREEN   = "#16a34a"
_WARNING = "#d97706"
_BG      = "#f5f7fa"
_FONT    = "BIZ UDGothic"
_COLORS  = [_NAVY, _ALERT, _GREEN, _WARNING, "#7c3aed"]


def pareto_chart(
    pareto_df: pd.DataFrame,
    mode_col: str,
    vital_few: list[str],
) -> go.Figure:
    """
    パレート図: 降順棒グラフ + 累積% 折れ線（secondary_y）+ 80% 閾値線。
    vital few のモードは alert 色（それ以外は navy）。

    Note: make_subplots の secondary_y に add_hline は使えない。
    80% ラインは Scatter トレースとして secondary_y に追加する。
    """
    modes     = pareto_df[mode_col].tolist()
    counts    = pareto_df["count"].tolist()
    cum_pct   = pareto_df["cumulative_pct"].tolist()
    bar_colors = [_ALERT if m in vital_few else _NAVY for m in modes]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=modes, y=counts, marker_color=bar_colors,
            name="件数", text=counts, textposition="outside",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=modes, y=cum_pct, mode="lines+markers",
            line=dict(color=_WARNING, width=2),
            marker=dict(size=7, color=_WARNING),
            name="累積%",
        ),
        secondary_y=True,
    )
    # 80% 閾値線（secondary_y Scatter として追加）
    fig.add_trace(
        go.Scatter(
            x=modes, y=[80.0] * len(modes),
            mode="lines",
            line=dict(color=_ALERT, width=1.2, dash="dash"),
            name="80%閾値", showlegend=False,
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=dict(text="不良モード別パレート図", font=dict(size=14, color=_NAVY)),
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG, paper_bgcolor=_BG,
        height=350, margin=dict(l=60, r=90, t=40, b=40),
        legend=dict(orientation="h", y=1.12),
        showlegend=True,
    )
    fig.update_yaxes(title_text="件数", secondary_y=False)
    fig.update_yaxes(title_text="累積 (%)", secondary_y=True, range=[0, 110])
    return fig


def trend_chart(trend_df: pd.DataFrame) -> go.Figure:
    """月別不良モード推移折れ線グラフ（最大5モード、パレート降順）。"""
    fig  = go.Figure()
    cols = trend_df.columns.tolist()[:5]

    for i, col in enumerate(cols):
        fig.add_trace(go.Scatter(
            x=trend_df.index.tolist(),
            y=trend_df[col].tolist(),
            mode="lines+markers",
            name=str(col),
            line=dict(color=_COLORS[i % len(_COLORS)], width=2),
            marker=dict(size=7),
        ))

    fig.update_layout(
        title=dict(text="不良モード別 月次推移", font=dict(size=14, color=_NAVY)),
        xaxis_title="年月", yaxis_title="件数",
        font=dict(family=_FONT, size=12),
        plot_bgcolor=_BG, paper_bgcolor=_BG,
        height=300, margin=dict(l=60, r=90, t=40, b=40),
        legend=dict(orientation="h", y=1.15),
    )
    return fig
```

- [ ] **Step 2: チャート動作確認（Python スクリプト）**

```bash
cd dx-portfolio
python -c "
import sys; sys.path.insert(0, '02_manufacturing/13_defect_pareto')
from sample_data import generate_sample_csv
from analyze import run_analysis
from visualize import pareto_chart, trend_chart
df = generate_sample_csv()
r = run_analysis(df, 'year_month', 'defect_mode', 'count')
fig1 = pareto_chart(r['pareto_df'], 'defect_mode', r['vital_few'])
fig2 = trend_chart(r['trend_df'])
print('pareto_chart OK:', fig1.layout.title.text)
print('trend_chart  OK:', fig2.layout.title.text)
print('vital_few:', r['vital_few'])
print('verdict:', r['verdict'])
"
```

期待出力:
```
pareto_chart OK: 不良モード別パレート図
trend_chart  OK: 不良モード別 月次推移
vital_few: ['バリ']
verdict: alert
```

- [ ] **Step 3: コミット**

```bash
git add dx-portfolio/02_manufacturing/13_defect_pareto/visualize.py
git commit -m "feat(C-69): visualize.py — pareto_chart + trend_chart"
```

---

### Task 4: app.py + STATUS.md 更新

**Files:**
- Create: `02_manufacturing/13_defect_pareto/app.py`
- Modify: `02_manufacturing/13_defect_pareto/STATUS.md`

- [ ] **Step 1: app.py を作成**

`02_manufacturing/13_defect_pareto/app.py`:
```python
"""不良モード別パレート × 時系列複合分析。"""
from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import analyze
import visualize
from sample_data import generate_sample_csv

st.set_page_config(page_title="不良モード別パレート分析", page_icon="📊", layout="wide")

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
    '📊 不良モード別パレート × 時系列複合分析</h3>'
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

    date_col = mode_col = count_col = None
    run_btn = False

    if df is not None:
        cols      = df.columns.tolist()
        date_col  = st.selectbox("年月列",       cols, key="date_col")
        mode_col  = st.selectbox("不良モード列", cols, index=min(1, len(cols) - 1), key="mode_col")
        count_col = st.selectbox("件数列",       cols, index=min(2, len(cols) - 1), key="count_col")
        run_btn   = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    if not all([date_col, mode_col, count_col]):
        st.error("列をすべて選択してください。")
        st.stop()
    try:
        result = analyze.run_analysis(df, date_col, mode_col, count_col)
        st.session_state.update({
            "result":        result,
            "date_col":      date_col,
            "mode_col":      mode_col,
            "count_col":     count_col,
            "uploaded_name": uploaded.name if uploaded else "sample_defect_pareto.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result    = st.session_state.get("result")
date_col  = st.session_state.get("date_col",  date_col)
mode_col  = st.session_state.get("mode_col",  mode_col)
count_col = st.session_state.get("count_col", count_col)

if not result:
    st.info("サイドバーで設定を選択し、「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI サマリー（4列）───────────────────────────────────────────
verdict = result["verdict"]
_COLOR  = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL  = {"good": "改善中",  "warning": "横ばい",  "alert": "悪化"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("全期間合計件数", f"{result['total_count']:,}件")
c2.metric("最多不良モード", f"{result['top_mode']}（{result['top_mode_pct']:.1f}%）")
c3.metric("vital few",     f"{len(result['vital_few'])}モードで80%超")
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">'
    f'{result["latest_month"]}：{result["latest_total"]}件 '
    f'（前月 {result["prev_total"]}件）</span></div>',
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(
        visualize.pareto_chart(result["pareto_df"], mode_col, result["vital_few"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.trend_chart(result["trend_df"]),
        use_container_width=True,
    )

# ── パレートデータテーブル ─────────────────────────────────────────
st.subheader("パレート集計テーブル")
display_df = result["pareto_df"].copy()
display_df["cumulative_pct"] = display_df["cumulative_pct"].map(lambda x: f"{x:.1f}%")
display_df["vital_few"] = display_df[mode_col].apply(
    lambda m: "★" if m in result["vital_few"] else ""
)
st.dataframe(display_df, hide_index=True, use_container_width=True)

# ── DB 書き込み（失敗してもアプリは継続）────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "defect_pareto",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "defect_pareto",
        result["latest_month"],
        "top_mode_pct", result["top_mode_pct"], verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")
```

- [ ] **Step 2: STATUS.md を production-ready に更新**

`02_manufacturing/13_defect_pareto/STATUS.md`:
```markdown
# C-69 不良モード別パレート × 時系列複合分析

- name: 不良モード別パレート × 時系列複合分析
- industry: 製造
- department: 生産・品質
- status: production-ready
```

- [ ] **Step 3: Streamlit を起動して動作確認**

```bash
cd dx-portfolio
.venv\Scripts\streamlit run 02_manufacturing/13_defect_pareto/app.py
```

確認事項:
1. 「サンプルデータを使用」ボタン → DataFrame が読み込まれること
2. 「▶ 分析実行」ボタン → KPI 4列に `合計件数 / バリ（xx%）/ 1モードで80%超 / 悪化（alert）` が表示されること
3. パレート図: 棒グラフ（バリが alert 色）+ 累積% 折れ線 + 80% 閾値破線が表示されること
4. 月次推移グラフ: 5モードの折れ線が表示されること
5. パレート集計テーブル: `vital_few 列に ★` が表示されること

- [ ] **Step 4: コミット**

```bash
git add dx-portfolio/02_manufacturing/13_defect_pareto/app.py \
        dx-portfolio/02_manufacturing/13_defect_pareto/STATUS.md
git commit -m "feat(C-69): app.py + STATUS.md 更新 production-ready"
```

---

### Task 5: ダッシュボード連携 + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`
- Modify: `catalog.yml`

- [ ] **Step 1: dashboard.py の CARDS リストに defect_pareto を追加**

`02_manufacturing/09_unified_dashboard/dashboard.py` の CARDS リストを確認し、
既存の最後のカード（C-66 の `4m_change` カード）の直後に以下を追加する:

```python
{"system_id": "defect_pareto", "metric": "top_mode_pct",
 "title": "最多不良モード構成比", "fmt": lambda v: f"{v:.1f}%"},
```

追加後の CARDS リスト末尾はこのようになる:
```python
    {"system_id": "4m_change", "metric": "p_value",
     "title": "4M変更有意差（p値）", "fmt": lambda v: f"{v:.4f}"},
    {"system_id": "defect_pareto", "metric": "top_mode_pct",
     "title": "最多不良モード構成比", "fmt": lambda v: f"{v:.1f}%"},
]
```

- [ ] **Step 2: catalog.yml に C-69 エントリを追加**

`catalog.yml` を開き、C-66 エントリの直後（または ★★☆ セクションの末尾）に以下を追記する:

```yaml
- id: "C-69"
  name: "不良モード別パレート × 時系列複合分析"
  industry: "製造"
  department: "生産・品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/13_defect_pareto"
  demo: "streamlit run 02_manufacturing/13_defect_pareto/app.py"
  description: |
    月次集計済みの不良モード別件数データをパレート分析と時系列推移グラフで可視化。
    累積80%以内の"vital few"（支配的不良モード群）を自動特定し、
    直近月の悪化傾向を verdict（good/warning/alert）で通知する。
```

- [ ] **Step 3: 全テストが PASS することを再確認**

```bash
cd dx-portfolio
python -m pytest 02_manufacturing/13_defect_pareto/tests/ -v
```

期待: `8 passed`

- [ ] **Step 4: コミット**

```bash
git add dx-portfolio/02_manufacturing/09_unified_dashboard/dashboard.py \
        dx-portfolio/catalog.yml
git commit -m "feat(C-69): C-63ダッシュボード + catalog.yml に C-69 追加"
```

---

## 完了チェックリスト

- [ ] `02_manufacturing/13_defect_pareto/sample_data.py` — 5モード×12ヶ月 CSV 生成
- [ ] `tests/test_analyze.py` — 8テスト all PASS
- [ ] `analyze.py` — pareto_df / trend_df / vital_few / verdict
- [ ] `visualize.py` — pareto_chart（secondary_y + 80%閾値線）/ trend_chart
- [ ] `app.py` — サンプルデータ動作 + チャート表示 + DB書き込みスキップで継続
- [ ] `STATUS.md` — production-ready
- [ ] `dashboard.py` — defect_pareto カード追加
- [ ] `catalog.yml` — C-69 エントリ追加
