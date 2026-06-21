# 協力会社別受入不良率月報 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 協力会社（仕入先）ごとの月次受入検査データを CSV でアップロードし、不良率を自動計算して月次トレンドと協力会社別ランキングを可視化する月報ツールを実装する。

**Architecture:** CSV（supplier/month/incoming_qty/defect_qty）→ analyze.py（加重平均不良率 + verdict）→ visualize.py（月次トレンド棒グラフ + 協力会社別横棒）→ app.py（Streamlit UI + DB）の一方向依存。C-68/C-71/C-72 と同一パターン。

**Tech Stack:** Python 3.x, Streamlit, Plotly, pandas

---

## ファイルマップ

| ファイル | 役割 |
|---------|------|
| `02_manufacturing/19_supplier_defect_rate/sample_data.py` | 5協力会社 × 6ヶ月デモデータ生成 |
| `02_manufacturing/19_supplier_defect_rate/analyze.py` | 不良率計算 + verdict（純粋関数）|
| `02_manufacturing/19_supplier_defect_rate/visualize.py` | Plotly 月次トレンド + 協力会社別横棒 |
| `02_manufacturing/19_supplier_defect_rate/app.py` | Streamlit UI + DB 書き込み |
| `02_manufacturing/19_supplier_defect_rate/STATUS.md` | production-ready |
| `02_manufacturing/19_supplier_defect_rate/tests/__init__.py` | 空（パッケージマーカー）|
| `02_manufacturing/19_supplier_defect_rate/tests/test_analyze.py` | 8テスト TDD |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | CARDS に supplier_defect_rate 追加（修正）|
| `catalog.yml` | C-73 エントリ追加（修正）|

---

### Task 1: scaffold + sample_data.py

**Files:**
- Create: `02_manufacturing/19_supplier_defect_rate/sample_data.py`
- Create: `02_manufacturing/19_supplier_defect_rate/tests/__init__.py`
- Create: `02_manufacturing/19_supplier_defect_rate/STATUS.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p "02_manufacturing/19_supplier_defect_rate/tests"
```

- [ ] **Step 2: `tests/__init__.py` を作成（空ファイル）**

`02_manufacturing/19_supplier_defect_rate/tests/__init__.py` — 空ファイル。

- [ ] **Step 3: `sample_data.py` を作成**

```python
"""5協力会社（A社〜E社）× 6ヶ月（2024-01〜2024-06）受入不良率デモデータ生成。"""
from __future__ import annotations
import pandas as pd


def generate_sample_csv() -> pd.DataFrame:
    rows = []
    # A社: 不良率 ≈ 0.8%（優良）
    for month, qty, defects in [
        ("2024-01", 500, 4), ("2024-02", 520, 4), ("2024-03", 510, 5),
        ("2024-04", 530, 4), ("2024-05", 500, 4), ("2024-06", 515, 4),
    ]:
        rows.append({"supplier": "A社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # B社: 不良率 ≈ 4.5%（要改善）
    for month, qty, defects in [
        ("2024-01", 300, 14), ("2024-02", 280, 13), ("2024-03", 310, 14),
        ("2024-04", 290, 13), ("2024-05", 300, 13), ("2024-06", 305, 14),
    ]:
        rows.append({"supplier": "B社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # C社: 不良率 ≈ 1.5%（要注意）
    for month, qty, defects in [
        ("2024-01", 800, 12), ("2024-02", 820, 13), ("2024-03", 810, 12),
        ("2024-04", 830, 12), ("2024-05", 800, 12), ("2024-06", 815, 12),
    ]:
        rows.append({"supplier": "C社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # D社: 不良率 ≈ 0.5%（最優良）
    for month, qty, defects in [
        ("2024-01", 600, 3), ("2024-02", 610, 3), ("2024-03", 605, 3),
        ("2024-04", 620, 3), ("2024-05", 600, 3), ("2024-06", 610, 3),
    ]:
        rows.append({"supplier": "D社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    # E社: 不良率 ≈ 2.8%（要注意）
    for month, qty, defects in [
        ("2024-01", 400, 11), ("2024-02", 410, 12), ("2024-03", 400, 11),
        ("2024-04", 420, 12), ("2024-05", 400, 11), ("2024-06", 410, 11),
    ]:
        rows.append({"supplier": "E社", "month": month,
                     "incoming_qty": qty, "defect_qty": defects})
    return pd.DataFrame(rows)
    # 期待 avg ≈ 2.0% → verdict = "warning"
    # worst: B社 / best: D社


if __name__ == "__main__":
    df = generate_sample_csv()
    df.to_csv("sample_supplier_defect_rate.csv", index=False)
    print(df.to_string())
```

- [ ] **Step 4: `STATUS.md` を作成**

```markdown
# C-73 協力会社別受入不良率月報

- name: 協力会社別受入不良率月報
- industry: 製造
- department: 品質保証
- status: in-progress
```

- [ ] **Step 5: syntax チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/19_supplier_defect_rate/sample_data.py', encoding='utf-8').read()); print('OK')"
```

期待出力: `OK`

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/19_supplier_defect_rate/
git commit -m "feat(C-73): scaffold + sample_data.py（5協力会社 × 6ヶ月 受入不良率デモ）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/19_supplier_defect_rate/tests/test_analyze.py`
- Create: `02_manufacturing/19_supplier_defect_rate/analyze.py`

- [ ] **Step 1: `test_analyze.py` を作成（RED フェーズ）**

```python
"""C-73 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def _make_df(suppliers, months, incoming, defects):
    return pd.DataFrame({
        "supplier":    suppliers,
        "month":       months,
        "incoming_qty": incoming,
        "defect_qty":  defects,
    })


def test_verdict_good():
    # avg = 5/500 * 100 = 1.0% → good（境界値）
    df = _make_df(["A"], ["2024-01"], [500], [5])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "good"
    assert result["avg_defect_rate"] == pytest.approx(1.0)


def test_verdict_warning():
    # avg = 10/500 * 100 = 2.0% → warning
    df = _make_df(["A"], ["2024-01"], [500], [10])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "warning"
    assert 1.0 < result["avg_defect_rate"] <= 3.0


def test_verdict_alert():
    # avg = 20/500 * 100 = 4.0% → alert
    df = _make_df(["A"], ["2024-01"], [500], [20])
    result = analyze.run_analysis(df)
    assert result["verdict"] == "alert"
    assert result["avg_defect_rate"] > 3.0


def test_defect_rate_calculation():
    df = _make_df(["A"], ["2024-01"], [200], [4])
    result = analyze.run_analysis(df)
    assert result["result_df"]["defect_rate"].iloc[0] == pytest.approx(2.0)


def test_weighted_average():
    # A社: 100件 × 10% = 10不良, B社: 900件 × 1% = 9不良
    # 加重平均: 19/1000 * 100 = 1.9%（単純平均 5.5% とは異なる）
    df = _make_df(
        ["A", "B"], ["2024-01", "2024-01"],
        [100, 900], [10, 9],
    )
    result = analyze.run_analysis(df)
    assert result["avg_defect_rate"] == pytest.approx(1.9)


def test_worst_supplier():
    df = _make_df(
        ["A", "B", "C"], ["2024-01", "2024-01", "2024-01"],
        [500, 300, 800], [5, 15, 4],
    )
    result = analyze.run_analysis(df)
    # B社: 15/300 = 5.0%、A社: 1.0%、C社: 0.5%
    assert result["worst_supplier"] == "B"


def test_output_keys():
    df = _make_df(["A", "B"], ["2024-01", "2024-01"], [500, 300], [5, 9])
    result = analyze.run_analysis(df)
    expected = {"result_df", "avg_defect_rate", "worst_supplier",
                "best_supplier", "n_suppliers", "verdict"}
    assert set(result.keys()) == expected


def test_missing_column_raises():
    df = pd.DataFrame({"supplier": ["A"], "month": ["2024-01"]})
    with pytest.raises(ValueError):
        analyze.run_analysis(df)
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
python -m pytest 02_manufacturing/19_supplier_defect_rate/tests/test_analyze.py -v 2>&1 | head -10
```

期待: `ModuleNotFoundError` または `ImportError`

- [ ] **Step 3: `analyze.py` を作成（GREEN フェーズ）**

```python
"""協力会社別受入不良率月報 — 不良率計算 + verdict ロジック。"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLS = ["supplier", "month", "incoming_qty", "defect_qty"]


def _verdict(avg: float) -> str:
    if avg <= 1.0:
        return "good"
    elif avg <= 3.0:
        return "warning"
    return "alert"


def run_analysis(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    data = df.copy()
    for col in ["incoming_qty", "defect_qty"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["incoming_qty", "defect_qty"])
    data = data[data["incoming_qty"] > 0].copy()

    if len(data) < 1:
        raise ValueError("有効なデータがありません。")

    data["defect_rate"] = data["defect_qty"] / data["incoming_qty"] * 100.0

    total_incoming = data["incoming_qty"].sum()
    total_defect   = data["defect_qty"].sum()
    avg_defect_rate = float(total_defect / total_incoming * 100.0)

    supplier_stats = data.groupby("supplier")[["defect_qty", "incoming_qty"]].sum()
    supplier_rates = supplier_stats["defect_qty"] / supplier_stats["incoming_qty"] * 100.0
    worst_supplier = str(supplier_rates.idxmax())
    best_supplier  = str(supplier_rates.idxmin())

    return {
        "result_df":       data,
        "avg_defect_rate": avg_defect_rate,
        "worst_supplier":  worst_supplier,
        "best_supplier":   best_supplier,
        "n_suppliers":     int(data["supplier"].nunique()),
        "verdict":         _verdict(avg_defect_rate),
    }
```

- [ ] **Step 4: 全テストが PASS することを確認**

```bash
python -m pytest 02_manufacturing/19_supplier_defect_rate/tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
git add 02_manufacturing/19_supplier_defect_rate/analyze.py \
        02_manufacturing/19_supplier_defect_rate/tests/test_analyze.py
git commit -m "feat(C-73): analyze.py TDD — 8テスト all PASS（加重平均不良率 + verdict）"
```

---

### Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/19_supplier_defect_rate/visualize.py`

- [ ] **Step 1: `visualize.py` を作成**

```python
"""協力会社別受入不良率月報 — Plotly チャート。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_NAVY   = "#1e3a5f"
_GREEN  = "#16a34a"
_AMBER  = "#d97706"
_RED    = "#dc2626"
_BG     = "#f5f7fa"

_PALETTE = [
    "#1e3a5f", "#16a34a", "#d97706", "#dc2626",
    "#7c3aed", "#0891b2", "#be185d", "#65a30d",
]

_VERDICT_COLOR = {"good": _GREEN, "warning": _AMBER, "alert": _RED}


def defect_rate_chart(result_df: pd.DataFrame) -> go.Figure:
    """協力会社 × 月ごとの不良率グループ棒グラフ。"""
    suppliers = sorted(result_df["supplier"].unique())
    months    = sorted(result_df["month"].unique())

    fig = go.Figure()
    for i, sup in enumerate(suppliers):
        sub = result_df[result_df["supplier"] == sup]
        month_rate = {row["month"]: row["defect_rate"]
                      for _, row in sub.iterrows()}
        rates = [month_rate.get(m, None) for m in months]
        fig.add_trace(go.Bar(
            x=months, y=rates,
            name=sup,
            marker_color=_PALETTE[i % len(_PALETTE)],
        ))

    fig.add_hline(y=3.0, line_dash="dash", line_color=_RED,
                  annotation_text="3.0%（alert）", annotation_position="right")
    fig.add_hline(y=1.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="1.0%（good）", annotation_position="right")
    fig.update_layout(
        barmode="group",
        title="協力会社別 月次不良率推移",
        xaxis_title="年月",
        yaxis_title="不良率（%）",
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        legend=dict(orientation="h", y=-0.25),
    )
    return fig


def supplier_bar_chart(result_df: pd.DataFrame) -> go.Figure:
    """協力会社別 加重平均不良率横棒グラフ（verdict 色分け）。"""
    supplier_stats = result_df.groupby("supplier")[
        ["defect_qty", "incoming_qty"]
    ].sum()
    supplier_rates = (
        supplier_stats["defect_qty"] / supplier_stats["incoming_qty"] * 100.0
    ).sort_values(ascending=True)

    colors = [
        _GREEN if v <= 1.0 else _AMBER if v <= 3.0 else _RED
        for v in supplier_rates
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=supplier_rates.values,
        y=supplier_rates.index,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.2f}%" for v in supplier_rates.values],
        textposition="outside",
    ))
    fig.add_vline(x=1.0, line_dash="dash", line_color=_GREEN,
                  annotation_text="1.0%", annotation_position="top")
    fig.add_vline(x=3.0, line_dash="dash", line_color=_RED,
                  annotation_text="3.0%", annotation_position="top")
    fig.update_layout(
        title="協力会社別 平均不良率",
        xaxis=dict(title="平均不良率（%）", range=[0, None]),
        yaxis_title="協力会社",
        height=320,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
```

- [ ] **Step 2: syntax + import チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/19_supplier_defect_rate/visualize.py', encoding='utf-8').read()); print('syntax OK')"
```

```bash
cd 02_manufacturing/19_supplier_defect_rate && python -c "import visualize; print('import OK')"
```

期待: `syntax OK` → `import OK`

- [ ] **Step 3: コミット**

```bash
git add 02_manufacturing/19_supplier_defect_rate/visualize.py
git commit -m "feat(C-73): visualize.py — 月次トレンド棒グラフ + 協力会社別横棒（verdict 色分け）"
```

---

### Task 4: app.py + STATUS.md（production-ready）

**Files:**
- Create: `02_manufacturing/19_supplier_defect_rate/app.py`
- Modify: `02_manufacturing/19_supplier_defect_rate/STATUS.md`

- [ ] **Step 1: `app.py` を作成**

```python
"""協力会社別受入不良率月報 — 月次受入検査 × 不良率自動計算 × 協力会社ランク。"""
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

st.set_page_config(page_title="協力会社別受入不良率月報", page_icon="🏭", layout="wide")

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
    "🏭 協力会社別受入不良率月報 — 月次受入検査 × 不良率自動計算</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 設定")
    st.caption("CSV 列: supplier / month / incoming_qty / defect_qty")
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

# ── Main ──────────────────────────────────────────────────────────
if df is None:
    st.info("サイドバーから CSV をアップロードするか、「サンプルデータを使用」をクリックしてください。")
    st.stop()

if run_btn:
    try:
        result = analyze.run_analysis(df)
        st.session_state.update({
            "result":        result,
            "uploaded_name": uploaded.name if uploaded else "sample_supplier_defect_rate.csv",
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
avg   = result["avg_defect_rate"]
best  = result["best_supplier"]
verdict = result["verdict"]

_COLOR = {"good": "#16a34a", "warning": "#d97706", "alert": "#dc2626"}
_LABEL = {"good": "品質良好", "warning": "要注意", "alert": "要改善"}
v_color = _COLOR[verdict]
v_label = _LABEL[verdict]

c1, c2, c3, c4 = st.columns(4)
c1.metric("協力会社数", f"{result['n_suppliers']}社")
c2.metric("平均不良率", f"{avg:.2f}%")
c3.metric("最良協力会社", best)
c4.markdown(
    f'<div style="background:{v_color}22;border-left:4px solid {v_color};'
    f'padding:8px 12px;border-radius:4px;margin-top:4px">'
    f'<b style="color:{v_color};font-size:16px">{v_label}</b><br>'
    f'<span style="font-size:12px;color:#64748b">avg={avg:.2f}%</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── チャート ──────────────────────────────────────────────────────
col_l, col_r = st.columns([2, 1])
with col_l:
    st.plotly_chart(
        visualize.defect_rate_chart(result["result_df"]),
        use_container_width=True,
    )
with col_r:
    st.plotly_chart(
        visualize.supplier_bar_chart(result["result_df"]),
        use_container_width=True,
    )

# ── テーブル ──────────────────────────────────────────────────────
st.subheader("受入検査データ詳細")
display_df = result["result_df"][
    ["supplier", "month", "incoming_qty", "defect_qty", "defect_rate"]
].sort_values(["month", "supplier"]).reset_index(drop=True)
st.dataframe(display_df, use_container_width=True)

# ── DB 書き込み ────────────────────────────────────────────────────
try:
    from _common.db_writer import init_db, write_upload, write_kpi
    init_db()
    uid = write_upload(
        "supplier_defect_rate",
        st.session_state.get("uploaded_name"),
        st.session_state.get("row_count"),
    )
    write_kpi(
        uid, "supplier_defect_rate",
        datetime.now().strftime("%Y-%m"),
        "defect_rate", avg, verdict,
    )
except Exception as _e:
    st.caption(f"⚠ DB書き込みスキップ: {_e}")
```

- [ ] **Step 2: `STATUS.md` を production-ready に更新**

```markdown
# C-73 協力会社別受入不良率月報

- name: 協力会社別受入不良率月報
- industry: 製造
- department: 品質保証
- status: production-ready
```

- [ ] **Step 3: syntax チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/19_supplier_defect_rate/app.py', encoding='utf-8').read()); print('OK')"
```

期待: `OK`

- [ ] **Step 4: 全テスト確認**

```bash
python -m pytest 02_manufacturing/19_supplier_defect_rate/tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
git add 02_manufacturing/19_supplier_defect_rate/app.py \
        02_manufacturing/19_supplier_defect_rate/STATUS.md
git commit -m "feat(C-73): app.py + STATUS.md production-ready（月次トレンド + 協力会社ランク + DB 書き込み）"
```

---

### Task 5: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`（CARDS に追加）
- Modify: `catalog.yml`（C-73 エントリ追加）

- [ ] **Step 1: `dashboard.py` の CARDS リスト末尾に追加**

`02_manufacturing/09_unified_dashboard/dashboard.py` を Read して CARDS リストの末尾を確認し、
以下のエントリを末尾に追加する:

```python
    {"system_id": "supplier_defect_rate", "metric": "defect_rate",
     "title": "受入不良率（平均）", "fmt": lambda v: f"{v:.2f}%"},
```

- [ ] **Step 2: `catalog.yml` の末尾に C-73 エントリを追記**

```yaml
- id: "C-73"
  name: "協力会社別受入不良率月報"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★★"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/19_supplier_defect_rate"
  demo: "streamlit run 02_manufacturing/19_supplier_defect_rate/app.py"
  description: |
    協力会社（仕入先）ごとの月次受入検査データ（受入数・不良数）を CSV でアップロードし、
    不良率を自動計算。平均不良率 ≤ 1.0% → "good" の明快な verdict 設計。
    月次トレンドグラフと協力会社別平均横棒グラフで改善ポイントを可視化。
```

- [ ] **Step 3: 全テスト確認**

```bash
python -m pytest 02_manufacturing/19_supplier_defect_rate/tests/ -v
```

期待: `8 passed`

- [ ] **Step 4: コミット**

```bash
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-73): C-63ダッシュボード + catalog.yml に C-73 追加"
```
