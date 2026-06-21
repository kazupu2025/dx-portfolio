# 品質コストROI分析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 月次 PAF コスト CSV から ROI を計算し、Streamlit で可視化して C-63 ダッシュボードに連携する C-71 システムを構築する。

**Architecture:** `analyze.py`（純粋関数）→ `visualize.py`（Plotly）→ `app.py`（Streamlit + DB統合）の3層構成。n≥2 で月次 ROI、n==1 で failure_ratio フォールバックの 2 モード設計。

**Tech Stack:** Python 3.10+, pandas, numpy, scipy, plotly, streamlit, pytest

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `02_manufacturing/16_quality_cost_roi/sample_data.py` | 12ヶ月デモCSV生成 |
| `02_manufacturing/16_quality_cost_roi/analyze.py` | ROI計算ロジック（純粋関数） |
| `02_manufacturing/16_quality_cost_roi/visualize.py` | Plotly 積み上げ棒グラフ + ROI折れ線グラフ |
| `02_manufacturing/16_quality_cost_roi/app.py` | Streamlit UI + DB統合 |
| `02_manufacturing/16_quality_cost_roi/STATUS.md` | システム状態 |
| `02_manufacturing/16_quality_cost_roi/tests/__init__.py` | テストパッケージ |
| `02_manufacturing/16_quality_cost_roi/tests/test_analyze.py` | 8テスト（TDD） |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | quality_cost_roi カード追加 |
| `catalog.yml` | C-71 エントリ追加 |

---

## Task 1: Scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/16_quality_cost_roi/sample_data.py`
- Create: `02_manufacturing/16_quality_cost_roi/tests/__init__.py`
- Create: `02_manufacturing/16_quality_cost_roi/STATUS.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
mkdir -p 02_manufacturing/16_quality_cost_roi/tests
```

- [ ] **Step 2: tests/__init__.py を作成（空ファイル）**

```bash
touch 02_manufacturing/16_quality_cost_roi/tests/__init__.py
```

- [ ] **Step 3: sample_data.py を作成**

`02_manufacturing/16_quality_cost_roi/sample_data.py`:

```python
"""12ヶ月（2024-01〜2024-12）品質コストデモCSV生成。"""
from __future__ import annotations
import numpy as np
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 12
    months = [f"2024-{m:02d}" for m in range(1, n + 1)]
    prevention = np.linspace(500_000, 700_000, n) + rng.normal(0, 10_000, n)
    appraisal  = np.linspace(300_000, 250_000, n) + rng.normal(0, 8_000, n)
    failure    = np.linspace(1_500_000, 600_000, n) + rng.normal(0, 30_000, n)
    return pd.DataFrame({
        "month":            months,
        "prevention_cost":  prevention.round(0).astype(int),
        "appraisal_cost":   appraisal.round(0).astype(int),
        "failure_cost":     failure.round(0).astype(int),
    })


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_quality_cost.csv", index=False)
    print(df.to_string())
```

- [ ] **Step 4: STATUS.md を作成**

`02_manufacturing/16_quality_cost_roi/STATUS.md`:

```markdown
# C-71 品質コストROI分析

- name: 品質コストROI分析
- industry: 製造
- department: 品質
- status: in-progress
```

- [ ] **Step 5: syntax チェック**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
python -c "import ast; ast.parse(open('02_manufacturing/16_quality_cost_roi/sample_data.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/16_quality_cost_roi/
git commit -m "feat(C-71): scaffold + sample_data.py（12ヶ月 PAF コストデモ）"
```

---

## Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/16_quality_cost_roi/tests/test_analyze.py`
- Create: `02_manufacturing/16_quality_cost_roi/analyze.py`

### Step 2-1: 失敗テストを書く

`02_manufacturing/16_quality_cost_roi/tests/test_analyze.py`:

```python
"""C-71 analyze.py TDD — 8テスト。"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(months, prevention, appraisal, failure):
    return pd.DataFrame({
        "month":            months,
        "prevention_cost":  prevention,
        "appraisal_cost":   appraisal,
        "failure_cost":     failure,
    })


def test_verdict_good():
    # delta=900, invest=500 → ROI=1.8 > 1.0
    df = _make_df(["2024-01", "2024-02"], [300, 300], [200, 200], [1000, 100])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert abs(result["latest_roi"] - 1.8) < 0.01


def test_verdict_warning():
    # delta=200, invest=500 → ROI=0.4
    df = _make_df(["2024-01", "2024-02"], [300, 300], [200, 200], [1000, 800])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 0 < result["latest_roi"] <= 1.0


def test_verdict_alert():
    # failure 増加 → ROI < 0
    df = _make_df(["2024-01", "2024-02"], [300, 300], [200, 200], [800, 1000])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["latest_roi"] < 0


def test_single_row_good():
    # failure_ratio = 200/1000 = 0.2 < 0.3
    df = _make_df(["2024-01"], [500], [300], [200])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["latest_roi"] is None
    assert abs(result["failure_ratio"] - 0.2) < 0.01


def test_single_row_alert():
    # failure_ratio = 600/900 ≈ 0.667 ≥ 0.5
    df = _make_df(["2024-01"], [200], [100], [600])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["latest_roi"] is None


def test_roi_series_length():
    df = _make_df(
        ["2024-01", "2024-02", "2024-03"],
        [300, 300, 300],
        [200, 200, 200],
        [1000, 800, 600],
    )
    result = analyze.run_analysis(df)
    assert len(result["roi_series"]) == 2


def test_output_keys():
    df = _make_df(["2024-01", "2024-02"], [300, 300], [200, 200], [1000, 800])
    result = analyze.run_analysis(df)
    expected = {
        "roi_series", "latest_roi", "failure_ratio",
        "total_prevention", "total_appraisal", "total_failure",
        "n_months", "verdict",
    }
    assert expected == set(result.keys())


def test_missing_column_raises():
    df = pd.DataFrame({"month": ["2024-01"], "prevention_cost": [300]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
```

- [ ] **Step 2-2: テストが失敗することを確認**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
python -m pytest 02_manufacturing/16_quality_cost_roi/tests/test_analyze.py -v 2>&1 | head -20
```

Expected: `ImportError` または `ModuleNotFoundError`（analyze.py がまだない）

- [ ] **Step 2-3: analyze.py を実装**

`02_manufacturing/16_quality_cost_roi/analyze.py`:

```python
"""品質コストROI分析 — PAFモデル月次ROI計算ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["month", "prevention_cost", "appraisal_cost", "failure_cost"]


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["prevention_cost", "appraisal_cost", "failure_cost"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["prevention_cost", "appraisal_cost", "failure_cost"])
    data = data.sort_values("month").reset_index(drop=True)

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    n = len(data)
    total_prevention = float(data["prevention_cost"].sum())
    total_appraisal  = float(data["appraisal_cost"].sum())
    total_failure    = float(data["failure_cost"].sum())

    latest_failure = float(data["failure_cost"].iloc[-1])
    latest_prev    = float(data["prevention_cost"].iloc[-1])
    latest_appr    = float(data["appraisal_cost"].iloc[-1])
    total_qc       = latest_prev + latest_appr + latest_failure
    failure_ratio  = latest_failure / total_qc if total_qc > 0 else 0.0

    roi_series: list[float] = []
    latest_roi: float | None = None

    if n >= 2:
        for i in range(1, n):
            delta  = float(data["failure_cost"].iloc[i - 1]) - float(data["failure_cost"].iloc[i])
            invest = float(data["prevention_cost"].iloc[i]) + float(data["appraisal_cost"].iloc[i])
            roi_series.append(delta / invest if invest > 0 else 0.0)
        latest_roi = roi_series[-1]
        if latest_roi > 1.0:
            verdict = "good"
        elif latest_roi > 0.0:
            verdict = "warning"
        else:
            verdict = "alert"
    else:
        if failure_ratio < 0.3:
            verdict = "good"
        elif failure_ratio < 0.5:
            verdict = "warning"
        else:
            verdict = "alert"

    return {
        "roi_series":       roi_series,
        "latest_roi":       latest_roi,
        "failure_ratio":    failure_ratio,
        "total_prevention": total_prevention,
        "total_appraisal":  total_appraisal,
        "total_failure":    total_failure,
        "n_months":         n,
        "verdict":          verdict,
    }
```

- [ ] **Step 2-4: テストが全て通ることを確認**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
python -m pytest 02_manufacturing/16_quality_cost_roi/tests/test_analyze.py -v
```

Expected: `8 passed`

- [ ] **Step 2-5: コミット**

```bash
git add 02_manufacturing/16_quality_cost_roi/analyze.py \
        02_manufacturing/16_quality_cost_roi/tests/test_analyze.py
git commit -m "feat(C-71): analyze.py TDD — 8テスト all PASS（PAF ROI計算 + verdict）"
```

---

## Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/16_quality_cost_roi/visualize.py`

- [ ] **Step 3-1: visualize.py を作成**

`02_manufacturing/16_quality_cost_roi/visualize.py`:

```python
"""品質コストROI分析 — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_AMBER = "#d97706"
_BG    = "#f5f7fa"


def cost_bar_chart(df: pd.DataFrame) -> go.Figure:
    months = df["month"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months, y=df["prevention_cost"],
        name="予防コスト", marker_color=_GREEN,
    ))
    fig.add_trace(go.Bar(
        x=months, y=df["appraisal_cost"],
        name="評価コスト", marker_color=_NAVY,
    ))
    fig.add_trace(go.Bar(
        x=months, y=df["failure_cost"],
        name="失敗コスト", marker_color=_RED,
    ))
    fig.update_layout(
        barmode="stack",
        title="月別 品質コスト構成（PAF）",
        xaxis_title="月",
        yaxis_title="金額（円）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def roi_line_chart(df: pd.DataFrame, roi_series: list[float]) -> go.Figure:
    months = df["month"].tolist()[1:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=roi_series,
        mode="lines+markers",
        name="ROI",
        line=dict(color=_AMBER, width=2),
        marker=dict(size=7),
    ))
    fig.add_hline(
        y=1.0,
        line_dash="dash",
        line_color=_NAVY,
        annotation_text="ROI=1.0（損益分岐点）",
        annotation_position="top right",
    )
    fig.update_layout(
        title="月次 ROI 推移",
        xaxis_title="月",
        yaxis_title="ROI",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
    )
    return fig
```

- [ ] **Step 3-2: syntax チェック**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
python -c "import ast; ast.parse(open('02_manufacturing/16_quality_cost_roi/visualize.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 3-3: コミット**

```bash
git add 02_manufacturing/16_quality_cost_roi/visualize.py
git commit -m "feat(C-71): visualize.py — cost_bar_chart（PAF積み上げ）+ roi_line_chart（損益分岐線付き）"
```

---

## Task 4: app.py + STATUS.md

**Files:**
- Create: `02_manufacturing/16_quality_cost_roi/app.py`
- Modify: `02_manufacturing/16_quality_cost_roi/STATUS.md`

- [ ] **Step 4-1: app.py を作成**

`02_manufacturing/16_quality_cost_roi/app.py`:

```python
"""品質コストROI分析 — PAFモデル × 月次改善効果測定。"""
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

st.set_page_config(page_title="品質コストROI分析", page_icon="💹", layout="wide")

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
    "💹 品質コストROI分析 — PAFモデル × 月次改善効果測定</h3>"
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
    run_btn = False
    if df is not None:
        run_btn = st.button("▶ 分析実行", type="primary", use_container_width=True)

# ── Main area ──────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    try:
        result = analyze.run_analysis(df)
        st.session_state.update({
            "result":        result,
            "uploaded_name": uploaded.name if uploaded else "sample_quality_cost.csv",
            "row_count":     len(df),
        })
    except ValueError as e:
        st.error(str(e))
        st.stop()

result = st.session_state.get("result")
if not result:
    st.info("「▶ 分析実行」を押してください。")
    st.stop()

# ── KPI 4列 ────────────────────────────────────────────────────────
latest_roi    = result["latest_roi"]
failure_ratio = result["failure_ratio"]
verdict       = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "投資回収済み", "warning": "改善中", "alert": "要投資見直し"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

sorted_df     = df.sort_values("month").reset_index(drop=True)
latest_failure = float(sorted_df["failure_cost"].iloc[-1])
first_failure  = float(sorted_df["failure_cost"].iloc[0])
delta_failure  = first_failure - latest_failure  # 正=改善

c1, c2, c3, c4 = st.columns(4)
c1.metric("最新月 failure コスト", f"¥{latest_failure:,.0f}")
if latest_roi is not None:
    c2.metric("最新月 ROI", f"{latest_roi:.2f}x")
else:
    c2.metric("failure 比率（1行）", f"{failure_ratio:.1%}")
c3.metric(
    "failure 削減額（初月比）",
    f"¥{abs(delta_failure):,.0f}",
    delta=f"{'改善' if delta_failure >= 0 else '悪化'} ¥{abs(delta_failure):,.0f}",
)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">'
    + (f"ROI={latest_roi:.2f}x" if latest_roi is not None else f"ratio={failure_ratio:.1%}")
    + "</span></div>",
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.cost_bar_chart(sorted_df), use_container_width=True)
with col_r:
    if latest_roi is not None:
        st.plotly_chart(
            visualize.roi_line_chart(sorted_df, result["roi_series"]),
            use_container_width=True,
        )
    else:
        st.info("ROI 推移グラフには 2 ヶ月以上のデータが必要です。")

# ── DB 書き込み ────────────────────────────────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "quality_cost_roi",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    value = latest_roi if latest_roi is not None else failure_ratio
    write_kpi(
        uid, "quality_cost_roi",
        datetime.now().strftime("%Y-%m"),
        "roi", value, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")
```

- [ ] **Step 4-2: STATUS.md を production-ready に更新**

`02_manufacturing/16_quality_cost_roi/STATUS.md`:

```markdown
# C-71 品質コストROI分析

- name: 品質コストROI分析
- industry: 製造
- department: 品質
- status: production-ready
```

- [ ] **Step 4-3: syntax チェック**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
python -c "import ast; ast.parse(open('02_manufacturing/16_quality_cost_roi/app.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 4-4: 全テスト確認**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
python -m pytest 02_manufacturing/16_quality_cost_roi/tests/test_analyze.py -v
```

Expected: `8 passed`

- [ ] **Step 4-5: コミット**

```bash
git add 02_manufacturing/16_quality_cost_roi/app.py \
        02_manufacturing/16_quality_cost_roi/STATUS.md
git commit -m "feat(C-71): app.py + STATUS.md production-ready（PAF積み上げ棒 + ROI折れ線 + フォールバック対応）"
```

---

## Task 5: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`
- Modify: `catalog.yml`

- [ ] **Step 5-1: dashboard.py の CARDS リストに quality_cost_roi カードを追加**

`02_manufacturing/09_unified_dashboard/dashboard.py` の CARDS リスト末尾（最後の `}` の後）に追加:

```python
    {"system_id": "quality_cost_roi", "metric": "roi",
     "title": "品質コストROI", "fmt": lambda v: f"{v:.2f}x"},
```

- [ ] **Step 5-2: catalog.yml に C-71 エントリを追加**

`catalog.yml` の末尾に追記:

```yaml
- id: "C-71"
  name: "品質コストROI分析 — PAFモデル × 月次改善効果測定"
  industry: "製造"
  department: "品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/16_quality_cost_roi"
  demo: "streamlit run 02_manufacturing/16_quality_cost_roi/app.py"
  description: |
    月次の品質コスト（予防・評価・失敗）CSVをアップロードし、PAFモデルに基づくROIを自動計算。
    前月比 failure コスト削減額 / 投資額 > 1.0 → "good"（投資回収済み）という明快な verdict 設計。
    1行データ時は failure_ratio フォールバックで必ず verdict を返す堅牢な実装。
```

- [ ] **Step 5-3: 全テスト確認**

```bash
cd c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio
python -m pytest 02_manufacturing/16_quality_cost_roi/tests/ -v
```

Expected: `8 passed`

- [ ] **Step 5-4: コミット**

```bash
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-71): C-63ダッシュボード + catalog.yml に C-71 追加"
```
