# 仕入先品質複合スコアリング Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 仕入先ごとの品質指標（不良率・納期遵守率・価格偏差）を重み付き合成スコアに変換してランク付けする C-68 システムを構築する。

**Architecture:** `analyze.py`（純粋関数・固定重み）→ `visualize.py`（Plotly）→ `app.py`（Streamlit + DB統合）の3層構成。合成スコア ≥ 80 → "good" のシンプルな verdict 設計。

**Tech Stack:** Python 3.10+, pandas, plotly, streamlit, pytest

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `02_manufacturing/17_supplier_scoring/sample_data.py` | 5仕入先デモCSV生成 |
| `02_manufacturing/17_supplier_scoring/analyze.py` | 重み付きスコア計算ロジック |
| `02_manufacturing/17_supplier_scoring/visualize.py` | 合成スコア横棒 + 指標内訳グラフ |
| `02_manufacturing/17_supplier_scoring/app.py` | Streamlit UI + DB統合 |
| `02_manufacturing/17_supplier_scoring/STATUS.md` | システム状態 |
| `02_manufacturing/17_supplier_scoring/tests/__init__.py` | テストパッケージ |
| `02_manufacturing/17_supplier_scoring/tests/test_analyze.py` | 8テスト（TDD） |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | supplier_scoring カード追加 |
| `catalog.yml` | C-68 エントリ追加 |

---

## Task 1: Scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/17_supplier_scoring/sample_data.py`
- Create: `02_manufacturing/17_supplier_scoring/tests/__init__.py`
- Create: `02_manufacturing/17_supplier_scoring/STATUS.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
mkdir -p 02_manufacturing/17_supplier_scoring/tests
```

- [ ] **Step 2: tests/__init__.py を作成（空ファイル）**

`02_manufacturing/17_supplier_scoring/tests/__init__.py`: 空ファイル（0バイト）

- [ ] **Step 3: sample_data.py を作成**

`02_manufacturing/17_supplier_scoring/sample_data.py`:

```python
"""5仕入先（SUP-A〜SUP-E）品質指標デモCSV生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    return pd.DataFrame({
        "supplier_id":    ["SUP-A", "SUP-B", "SUP-C", "SUP-D", "SUP-E"],
        "defect_rate":    [1.2,     3.5,     0.8,     5.0,     2.1],
        "delivery_rate":  [95.0,    88.0,    98.0,    82.0,    91.0],
        "price_variance": [3.0,     8.0,     1.5,     12.0,    4.5],
    })
    # 期待スコア（参考）:
    # SUP-A: composite≈89.5 → good
    # SUP-B: composite≈70.9 → warning
    # SUP-C: composite≈93.9 → good
    # SUP-D: composite≈57.6 → alert
    # SUP-E: composite≈82.3 → good
    # avg≈78.8 → warning（全体verdict）


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_supplier_scoring.csv", index=False)
    print(df.to_string())
```

- [ ] **Step 4: STATUS.md を作成**

`02_manufacturing/17_supplier_scoring/STATUS.md`:

```markdown
# C-68 仕入先品質複合スコアリング

- name: 仕入先品質複合スコアリング
- industry: 製造
- department: 購買・品質
- status: in-progress
```

- [ ] **Step 5: syntax チェック**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/17_supplier_scoring/sample_data.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/17_supplier_scoring/
git commit -m "feat(C-68): scaffold + sample_data.py（5仕入先 PAQ スコアリングデモ）"
```

---

## Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/17_supplier_scoring/tests/test_analyze.py`
- Create: `02_manufacturing/17_supplier_scoring/analyze.py`

- [ ] **Step 2-1: 失敗テストを書く**

`02_manufacturing/17_supplier_scoring/tests/test_analyze.py`:

```python
"""C-68 analyze.py TDD — 8テスト。"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(ids, defect, delivery, price):
    return pd.DataFrame({
        "supplier_id":    ids,
        "defect_rate":    defect,
        "delivery_rate":  delivery,
        "price_variance": price,
    })


def test_verdict_good():
    # composite = 95*0.5 + 98*0.3 + 95*0.2 = 47.5+29.4+19 = 95.9 ≥ 80
    df = _make_df(["A"], [0.5], [98.0], [1.0])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_score"] >= 80


def test_verdict_warning():
    # composite = 70*0.5 + 85*0.3 + 70*0.2 = 35+25.5+14 = 74.5
    df = _make_df(["A"], [3.0], [85.0], [6.0])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 60 <= result["avg_score"] < 80


def test_verdict_alert():
    # composite = 30*0.5 + 75*0.3 + 25*0.2 = 15+22.5+5 = 42.5 < 60
    df = _make_df(["A"], [7.0], [75.0], [15.0])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_score"] < 60


def test_score_defect_conversion():
    assert analyze._score_defect(1.0) == 90.0
    assert analyze._score_defect(15.0) == 0.0   # clamped at 0


def test_score_delivery_conversion():
    assert analyze._score_delivery(95.0) == 95.0
    assert analyze._score_delivery(110.0) == 100.0  # clamped at 100


def test_score_price_conversion():
    assert analyze._score_price(10.0) == 50.0   # 100 - 10*5
    assert analyze._score_price(25.0) == 0.0    # clamped at 0


def test_output_keys():
    df = _make_df(["A", "B"], [1.0, 3.0], [95.0, 85.0], [2.0, 6.0])
    result = analyze.run_analysis(df)
    expected = {
        "scored_df", "avg_score", "best_supplier",
        "worst_supplier", "n_suppliers", "verdict",
    }
    assert expected == set(result.keys())


def test_missing_column_raises():
    df = pd.DataFrame({"supplier_id": ["A"], "defect_rate": [1.0]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
```

- [ ] **Step 2-2: テストが失敗することを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/17_supplier_scoring/tests/test_analyze.py -v 2>&1 | head -15
```

Expected: `ImportError` または `ModuleNotFoundError`（analyze.py がまだない）

- [ ] **Step 2-3: analyze.py を実装**

`02_manufacturing/17_supplier_scoring/analyze.py`:

```python
"""仕入先品質複合スコアリング — 重み付き合成スコア計算ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["supplier_id", "defect_rate", "delivery_rate", "price_variance"]
WEIGHTS = {"defect_rate": 0.5, "delivery_rate": 0.3, "price_variance": 0.2}


def _score_defect(v: float) -> float:
    return max(0.0, 100.0 - v * 10.0)


def _score_delivery(v: float) -> float:
    return float(min(100.0, v))


def _score_price(v: float) -> float:
    return max(0.0, 100.0 - v * 5.0)


def _verdict(score: float) -> str:
    if score >= 80:
        return "good"
    elif score >= 60:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["defect_rate", "delivery_rate", "price_variance"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["defect_rate", "delivery_rate", "price_variance"])

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    data = data.copy()
    data["defect_score"]    = data["defect_rate"].apply(_score_defect)
    data["delivery_score"]  = data["delivery_rate"].apply(_score_delivery)
    data["price_score"]     = data["price_variance"].apply(_score_price)
    data["composite_score"] = (
        data["defect_score"]   * WEIGHTS["defect_rate"]
        + data["delivery_score"] * WEIGHTS["delivery_rate"]
        + data["price_score"]    * WEIGHTS["price_variance"]
    )
    data["verdict"] = data["composite_score"].apply(_verdict)

    avg_score      = float(data["composite_score"].mean())
    best_supplier  = str(data.loc[data["composite_score"].idxmax(), "supplier_id"])
    worst_supplier = str(data.loc[data["composite_score"].idxmin(), "supplier_id"])

    return {
        "scored_df":      data,
        "avg_score":      avg_score,
        "best_supplier":  best_supplier,
        "worst_supplier": worst_supplier,
        "n_suppliers":    len(data),
        "verdict":        _verdict(avg_score),
    }
```

- [ ] **Step 2-4: テストが全て通ることを確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/17_supplier_scoring/tests/test_analyze.py -v
```

Expected: `8 passed`

- [ ] **Step 2-5: コミット**

```bash
git add 02_manufacturing/17_supplier_scoring/analyze.py \
        02_manufacturing/17_supplier_scoring/tests/test_analyze.py
git commit -m "feat(C-68): analyze.py TDD — 8テスト all PASS（重み付き合成スコア + verdict）"
```

---

## Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/17_supplier_scoring/visualize.py`

- [ ] **Step 3-1: visualize.py を作成**

`02_manufacturing/17_supplier_scoring/visualize.py`:

```python
"""仕入先品質複合スコアリング — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_AMBER = "#d97706"
_RED   = "#dc2626"
_BG    = "#f5f7fa"

_VERDICT_COLOR = {"good": _GREEN, "warning": _AMBER, "alert": _RED}


def score_bar_chart(scored_df: pd.DataFrame) -> go.Figure:
    df = scored_df.sort_values("composite_score", ascending=True)
    colors = [_VERDICT_COLOR.get(v, _AMBER) for v in df["verdict"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["composite_score"],
        y=df["supplier_id"],
        orientation="h",
        marker_color=colors,
        name="合成スコア",
        text=df["composite_score"].round(1),
        textposition="outside",
    ))
    fig.add_vline(x=80, line_dash="dash", line_color=_NAVY,
                  annotation_text="80（good）", annotation_position="top")
    fig.add_vline(x=60, line_dash="dot", line_color=_AMBER,
                  annotation_text="60（warning）", annotation_position="bottom")
    fig.update_layout(
        title="仕入先別 合成スコア",
        xaxis=dict(title="合成スコア", range=[0, 110]),
        yaxis_title="仕入先",
        height=350,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig


def breakdown_chart(scored_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scored_df["supplier_id"], y=scored_df["defect_score"],
        name="不良スコア", marker_color=_RED,
    ))
    fig.add_trace(go.Bar(
        x=scored_df["supplier_id"], y=scored_df["delivery_score"],
        name="納期スコア", marker_color=_GREEN,
    ))
    fig.add_trace(go.Bar(
        x=scored_df["supplier_id"], y=scored_df["price_score"],
        name="価格スコア", marker_color=_NAVY,
    ))
    fig.update_layout(
        barmode="group",
        title="指標別スコア内訳",
        xaxis_title="仕入先",
        yaxis=dict(title="スコア（0〜100）", range=[0, 110]),
        height=350,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig
```

- [ ] **Step 3-2: syntax チェック**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/17_supplier_scoring/visualize.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 3-3: コミット**

```bash
git add 02_manufacturing/17_supplier_scoring/visualize.py
git commit -m "feat(C-68): visualize.py — score_bar_chart（verdict色分け）+ breakdown_chart（指標内訳）"
```

---

## Task 4: app.py + STATUS.md

**Files:**
- Create: `02_manufacturing/17_supplier_scoring/app.py`
- Modify: `02_manufacturing/17_supplier_scoring/STATUS.md`

- [ ] **Step 4-1: app.py を作成**

`02_manufacturing/17_supplier_scoring/app.py`:

```python
"""仕入先品質複合スコアリング — 重み付き合成スコア × 仕入先ランク。"""
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

st.set_page_config(page_title="仕入先品質複合スコアリング", page_icon="🏭", layout="wide")

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
    "🏭 仕入先品質複合スコアリング — 重み付き合成スコア × 仕入先ランク</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 設定")
    st.caption("重み: 不良率 50% / 納期 30% / 価格偏差 20%")
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
            "uploaded_name": uploaded.name if uploaded else "sample_supplier_scoring.csv",
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
avg_score      = result["avg_score"]
best_supplier  = result["best_supplier"]
verdict        = result["verdict"]
scored_df      = result["scored_df"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "優良仕入先多数", "warning": "改善余地あり", "alert": "取引見直し検討"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

best_score = float(scored_df.loc[scored_df["supplier_id"] == best_supplier, "composite_score"].iloc[0])

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

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.plotly_chart(visualize.score_bar_chart(scored_df), use_container_width=True)
with col_r:
    st.plotly_chart(visualize.breakdown_chart(scored_df), use_container_width=True)

# ── テーブル ──────────────────────────────────────────────────────
st.subheader("仕入先別スコア詳細")
display_cols = [
    "supplier_id", "defect_rate", "delivery_rate", "price_variance",
    "composite_score", "verdict",
]
st.dataframe(
    scored_df[display_cols].sort_values("composite_score", ascending=False).reset_index(drop=True),
    use_container_width=True,
)

# ── DB 書き込み ────────────────────────────────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "supplier_scoring",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "supplier_scoring",
        datetime.now().strftime("%Y-%m"),
        "avg_score", avg_score, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")
```

- [ ] **Step 4-2: STATUS.md を production-ready に更新**

`02_manufacturing/17_supplier_scoring/STATUS.md`:

```markdown
# C-68 仕入先品質複合スコアリング

- name: 仕入先品質複合スコアリング
- industry: 製造
- department: 購買・品質
- status: production-ready
```

- [ ] **Step 4-3: syntax チェック**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -c "import ast; ast.parse(open('02_manufacturing/17_supplier_scoring/app.py', encoding='utf-8').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 4-4: 全テスト確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/17_supplier_scoring/tests/test_analyze.py -v
```

Expected: `8 passed`

- [ ] **Step 4-5: コミット**

```bash
git add 02_manufacturing/17_supplier_scoring/app.py \
        02_manufacturing/17_supplier_scoring/STATUS.md
git commit -m "feat(C-68): app.py + STATUS.md production-ready（合成スコア棒グラフ + 指標内訳 + テーブル）"
```

---

## Task 5: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`
- Modify: `catalog.yml`

- [ ] **Step 5-1: dashboard.py の CARDS リストに supplier_scoring カードを追加**

`02_manufacturing/09_unified_dashboard/dashboard.py` の CARDS リスト末尾に追加:

```python
    {"system_id": "supplier_scoring", "metric": "avg_score",
     "title": "仕入先平均スコア", "fmt": lambda v: f"{v:.1f}点"},
```

- [ ] **Step 5-2: catalog.yml に C-68 エントリを追加**

`catalog.yml` の末尾に追記:

```yaml
- id: "C-68"
  name: "仕入先品質複合スコアリング — 重み付き合成スコア × 仕入先ランク"
  industry: "製造"
  department: "購買・品質"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/17_supplier_scoring"
  demo: "streamlit run 02_manufacturing/17_supplier_scoring/app.py"
  description: |
    仕入先ごとの品質指標（不良率・納期遵守率・価格偏差）を重み付き合成スコアに変換してランク付け。
    固定重み（不良率50%・納期30%・価格20%）でシンプルに計算し、スコア≥80→"good"で優良判定。
    横棒グラフで仕入先ランキング、指標別内訳グラフで改善ポイントを可視化。
```

- [ ] **Step 5-3: 全テスト確認**

```bash
cd "c:\Users\realp\Desktop\claude_code_TRY\dx-portfolio"
python -m pytest 02_manufacturing/17_supplier_scoring/tests/ -v
```

Expected: `8 passed`

- [ ] **Step 5-4: コミット**

```bash
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-68): C-63ダッシュボード + catalog.yml に C-68 追加"
```
