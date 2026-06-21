# AQL/受入サンプリング計画最適化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** JIS Z 9015-1 テーブルから n/Ac を自動算出し、OC 曲線で生産者・消費者リスクを可視化する受入サンプリング計画ツールを実装する。

**Architecture:** パラメータ入力型（CSV なし）。`tables.py`（JIS 定数）→ `analyze.py`（計算ロジック）→ `visualize.py`（OC 曲線）→ `app.py`（Streamlit UI）の一方向依存。ロット判定時のみ `_common/db_writer.py` に書き込む。

**Tech Stack:** Python 3.x, Streamlit, Plotly, scipy.stats.binom, numpy

---

## ファイルマップ

| ファイル | 役割 |
|---------|------|
| `02_manufacturing/18_aql_sampling/tables.py` | JIS Z 9015-1 定数（サンプルサイズコード表 + AQL テーブル） |
| `02_manufacturing/18_aql_sampling/analyze.py` | get_sampling_plan / oc_curve / judge_lot / run_plan |
| `02_manufacturing/18_aql_sampling/visualize.py` | oc_chart（OC 曲線 Plotly Figure）|
| `02_manufacturing/18_aql_sampling/app.py` | Streamlit UI（計画設計 + ロット判定 + DB 書き込み）|
| `02_manufacturing/18_aql_sampling/STATUS.md` | production-ready |
| `02_manufacturing/18_aql_sampling/tests/__init__.py` | 空（パッケージマーカー）|
| `02_manufacturing/18_aql_sampling/tests/test_analyze.py` | 8テスト TDD |
| `02_manufacturing/09_unified_dashboard/dashboard.py` | CARDS に aql_sampling 追加（修正）|
| `catalog.yml` | C-72 エントリ追加（修正）|

---

### Task 1: scaffold + tables.py

**Files:**
- Create: `02_manufacturing/18_aql_sampling/tables.py`
- Create: `02_manufacturing/18_aql_sampling/tests/__init__.py`
- Create: `02_manufacturing/18_aql_sampling/STATUS.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p "02_manufacturing/18_aql_sampling/tests"
```

- [ ] **Step 2: `tests/__init__.py` を作成（空ファイル）**

`02_manufacturing/18_aql_sampling/tests/__init__.py` — 空ファイル。

- [ ] **Step 3: `tables.py` を作成**

```python
"""JIS Z 9015-1（ISO 2859-1）サンプリング定数テーブル。"""
from __future__ import annotations

# ── サンプルサイズコード表 ────────────────────────────────────────────
# 各エントリ: ((lot_min, lot_max), {inspection_level: code})
# inspection_level: 1=水準I / 2=水準II / 3=水準III
SAMPLE_SIZE_CODE_TABLE: list[tuple[tuple[int, int], dict[int, str]]] = [
    ((2,       8),      {1: "A", 2: "A", 3: "B"}),
    ((9,       15),     {1: "A", 2: "B", 3: "C"}),
    ((16,      25),     {1: "B", 2: "C", 3: "D"}),
    ((26,      50),     {1: "C", 2: "D", 3: "E"}),
    ((51,      90),     {1: "C", 2: "E", 3: "F"}),
    ((91,      150),    {1: "D", 2: "F", 3: "G"}),
    ((151,     280),    {1: "E", 2: "G", 3: "H"}),
    ((281,     500),    {1: "F", 2: "H", 3: "J"}),
    ((501,     1200),   {1: "G", 2: "J", 3: "K"}),
    ((1201,    3200),   {1: "H", 2: "K", 3: "L"}),
    ((3201,    10000),  {1: "J", 2: "L", 3: "M"}),
    ((10001,   35000),  {1: "K", 2: "M", 3: "N"}),
    ((35001,   150000), {1: "L", 2: "N", 3: "P"}),
    ((150001,  500000), {1: "M", 2: "P", 3: "Q"}),
]

# ── AQL テーブル（普通検査・単回サンプリング）────────────────────────────
# キー: (code, aql)  値: (n, Ac, Re)
# JIS Z 9015-1 Table 2-A より抜粋（AQL 0.65〜6.5、コード A〜L）
AQL_TABLE: dict[tuple[str, float], tuple[int, int, int]] = {
    # ── AQL 0.65 ──
    ("C", 0.65): (5,   0,  1),
    ("D", 0.65): (8,   0,  1),
    ("E", 0.65): (13,  0,  1),
    ("F", 0.65): (20,  0,  1),
    ("G", 0.65): (32,  0,  1),
    ("H", 0.65): (50,  1,  2),
    ("J", 0.65): (80,  1,  2),
    ("K", 0.65): (125, 2,  3),
    ("L", 0.65): (200, 3,  4),
    # ── AQL 1.0 ──
    ("C", 1.0):  (5,   0,  1),
    ("D", 1.0):  (8,   0,  1),
    ("E", 1.0):  (13,  0,  1),
    ("F", 1.0):  (20,  0,  1),
    ("G", 1.0):  (32,  1,  2),
    ("H", 1.0):  (50,  1,  2),
    ("J", 1.0):  (80,  2,  3),
    ("K", 1.0):  (125, 3,  4),
    ("L", 1.0):  (200, 5,  6),
    # ── AQL 1.5 ──
    ("C", 1.5):  (5,   0,  1),
    ("D", 1.5):  (8,   0,  1),
    ("E", 1.5):  (13,  0,  1),
    ("F", 1.5):  (20,  1,  2),
    ("G", 1.5):  (32,  1,  2),
    ("H", 1.5):  (50,  2,  3),
    ("J", 1.5):  (80,  3,  4),
    ("K", 1.5):  (125, 5,  6),
    ("L", 1.5):  (200, 7,  8),
    # ── AQL 2.5 ──
    ("C", 2.5):  (5,   0,  1),
    ("D", 2.5):  (8,   0,  1),
    ("E", 2.5):  (13,  1,  2),
    ("F", 2.5):  (20,  1,  2),
    ("G", 2.5):  (32,  2,  3),
    ("H", 2.5):  (50,  3,  4),
    ("J", 2.5):  (80,  5,  6),
    ("K", 2.5):  (125, 7,  8),
    ("L", 2.5):  (200, 10, 11),
    # ── AQL 4.0 ──
    ("C", 4.0):  (5,   0,  1),
    ("D", 4.0):  (8,   1,  2),
    ("E", 4.0):  (13,  1,  2),
    ("F", 4.0):  (20,  2,  3),
    ("G", 4.0):  (32,  3,  4),
    ("H", 4.0):  (50,  5,  6),
    ("J", 4.0):  (80,  7,  8),
    ("K", 4.0):  (125, 10, 11),
    ("L", 4.0):  (200, 14, 15),
    # ── AQL 6.5 ──
    ("B", 6.5):  (3,   0,  1),
    ("C", 6.5):  (5,   0,  1),
    ("D", 6.5):  (8,   1,  2),
    ("E", 6.5):  (13,  2,  3),
    ("F", 6.5):  (20,  3,  4),
    ("G", 6.5):  (32,  5,  6),
    ("H", 6.5):  (50,  7,  8),
    ("J", 6.5):  (80,  10, 11),
    ("K", 6.5):  (125, 14, 15),
    ("L", 6.5):  (200, 21, 22),
}

VALID_AQL: list[float] = [0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.0, 1.5, 2.5, 4.0, 6.5]
```

- [ ] **Step 4: `STATUS.md` を作成**

```markdown
# C-72 AQL/受入サンプリング計画最適化

- name: AQL/受入サンプリング計画最適化
- industry: 製造
- department: 品質保証
- status: in-progress
```

- [ ] **Step 5: syntax チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/18_aql_sampling/tables.py', encoding='utf-8').read()); print('OK')"
```

期待出力: `OK`

- [ ] **Step 6: コミット**

```bash
git add 02_manufacturing/18_aql_sampling/
git commit -m "feat(C-72): scaffold + tables.py（JIS Z 9015-1 サンプルサイズコード + AQL テーブル）"
```

---

### Task 2: TDD — test_analyze.py + analyze.py

**Files:**
- Create: `02_manufacturing/18_aql_sampling/tests/test_analyze.py`
- Create: `02_manufacturing/18_aql_sampling/analyze.py`

- [ ] **Step 1: `test_analyze.py` を作成（RED フェーズ）**

```python
"""C-72 analyze.py TDD — 8テスト。"""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import analyze  # noqa: E402


def test_lot_size_to_code():
    plan = analyze.get_sampling_plan(500, 1.0, 2)
    assert plan["code"] == "H"


def test_get_sampling_plan():
    result = analyze.get_sampling_plan(500, 1.0, 2)
    assert result["n"]  == 50
    assert result["ac"] == 1
    assert result["re"] == 2


def test_oc_curve_at_zero():
    pa = analyze.oc_curve(50, 1, [0.0])
    assert pa[0] == pytest.approx(1.0)


def test_oc_curve_at_one():
    # p=1.0, Ac=0 → Pa = 0.0（不良率100%でAc=0なら必ず不合格）
    pa = analyze.oc_curve(50, 0, [1.0])
    assert pa[0] == pytest.approx(0.0)


def test_judge_accept():
    result = analyze.judge_lot(1, 2)
    assert result["result"]  == "accept"
    assert result["verdict"] == "good"


def test_judge_reject():
    result = analyze.judge_lot(3, 2)
    assert result["result"]  == "reject"
    assert result["verdict"] == "alert"


def test_run_plan_keys():
    result = analyze.run_plan(500, 1.0, 2)
    expected = {"code", "n", "ac", "re", "oc_p", "oc_pa", "alpha", "rql", "beta"}
    assert set(result.keys()) == expected


def test_invalid_lot_size():
    with pytest.raises(ValueError):
        analyze.get_sampling_plan(1, 1.0, 2)
```

- [ ] **Step 2: テストが FAIL することを確認**

```bash
python -m pytest 02_manufacturing/18_aql_sampling/tests/test_analyze.py -v
```

期待: `ImportError` または `ModuleNotFoundError`（analyze.py がまだ存在しないため）

- [ ] **Step 3: `analyze.py` を作成（GREEN フェーズ）**

```python
"""AQL 受入サンプリング計画 — JIS Z 9015-1 テーブル引き当て + OC 曲線計算。"""
from __future__ import annotations

import numpy as np
from scipy.stats import binom

from tables import AQL_TABLE, SAMPLE_SIZE_CODE_TABLE, VALID_AQL


def get_sampling_plan(lot_size: int, aql: float, inspection_level: int = 2) -> dict:
    """JIS Z 9015-1 テーブルからサンプリング計画を引き当てる。"""
    if lot_size < 2:
        raise ValueError("ロットサイズは 2 以上で入力してください。")
    if aql not in VALID_AQL:
        raise ValueError(f"AQL は {VALID_AQL} のいずれかを指定してください。")
    if inspection_level not in (1, 2, 3):
        raise ValueError("検査水準は 1・2・3 のいずれかを指定してください。")

    code: str | None = None
    for (lo, hi), level_map in SAMPLE_SIZE_CODE_TABLE:
        if lo <= lot_size <= hi:
            code = level_map[inspection_level]
            break
    if code is None:
        raise ValueError(f"ロットサイズ {lot_size} はテーブル範囲外です（上限: 500,000）。")

    key = (code, aql)
    if key not in AQL_TABLE:
        raise ValueError(
            f"コード '{code}'、AQL {aql}% の組み合わせはテーブルに定義されていません。"
            " AQL 水準またはロットサイズを変更してください。"
        )

    n, ac, re = AQL_TABLE[key]
    return {"code": code, "n": n, "ac": ac, "re": re}


def oc_curve(n: int, ac: int, p_values: list[float]) -> list[float]:
    """二項分布累積で OC 曲線の Pa 値列を計算する。"""
    return [float(binom.cdf(ac, n, p)) for p in p_values]


def judge_lot(defects: int, ac: int) -> dict:
    """実際の不良数と Ac を比較してロット合否を判定する。"""
    if defects <= ac:
        return {"result": "accept", "verdict": "good"}
    return {"result": "reject", "verdict": "alert"}


def run_plan(lot_size: int, aql: float, inspection_level: int = 2) -> dict:
    """計画設計の全出力をまとめて返す。"""
    plan = get_sampling_plan(lot_size, aql, inspection_level)
    n, ac = plan["n"], plan["ac"]

    oc_p_arr = np.linspace(0.0, 0.20, 200)
    oc_pa_arr = oc_curve(n, ac, list(oc_p_arr))

    alpha = 1.0 - float(binom.cdf(ac, n, aql / 100.0))

    rql_idx = next(
        (i for i, pa in enumerate(oc_pa_arr) if pa <= 0.10),
        len(oc_pa_arr) - 1,
    )
    rql  = float(oc_p_arr[rql_idx])
    beta = oc_pa_arr[rql_idx]

    return {
        "code":  plan["code"],
        "n":     n,
        "ac":    ac,
        "re":    plan["re"],
        "oc_p":  list(oc_p_arr),
        "oc_pa": oc_pa_arr,
        "alpha": alpha,
        "rql":   rql,
        "beta":  beta,
    }
```

- [ ] **Step 4: 全テストが PASS することを確認**

```bash
python -m pytest 02_manufacturing/18_aql_sampling/tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
git add 02_manufacturing/18_aql_sampling/analyze.py \
        02_manufacturing/18_aql_sampling/tests/test_analyze.py
git commit -m "feat(C-72): analyze.py TDD — 8テスト all PASS（JIS テーブル引き当て + OC 曲線 + ロット判定）"
```

---

### Task 3: visualize.py

**Files:**
- Create: `02_manufacturing/18_aql_sampling/visualize.py`

- [ ] **Step 1: `visualize.py` を作成**

```python
"""AQL 受入サンプリング計画 — Plotly OC 曲線チャート。"""
from __future__ import annotations

import plotly.graph_objects as go

_NAVY  = "#1e3a5f"
_GREEN = "#16a34a"
_RED   = "#dc2626"
_BG    = "#f5f7fa"


def oc_chart(
    oc_p: list[float],
    oc_pa: list[float],
    aql: float,
    alpha: float,
    rql: float,
    beta: float,
) -> go.Figure:
    """OC 曲線（Pa vs 不良率 p）を生産者・消費者リスクマーカー付きで描画する。"""
    p_pct  = [p * 100 for p in oc_p]
    rql_pct = rql * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=p_pct,
        y=list(oc_pa),
        mode="lines",
        line=dict(color=_NAVY, width=2),
        name="合格確率 Pa",
    ))

    fig.add_vline(
        x=aql,
        line_dash="dash",
        line_color=_GREEN,
        annotation_text=f"AQL={aql}%  α={alpha:.1%}",
        annotation_position="top right",
        annotation_font_color=_GREEN,
    )
    fig.add_vline(
        x=rql_pct,
        line_dash="dot",
        line_color=_RED,
        annotation_text=f"RQL={rql_pct:.1f}%  β={beta:.1%}",
        annotation_position="top left",
        annotation_font_color=_RED,
    )

    fig.update_layout(
        title="OC 曲線（Operating Characteristic Curve）",
        xaxis=dict(title="不良率 p（%）", range=[0, 20]),
        yaxis=dict(title="合格確率 Pa", range=[0, 1.05]),
        height=380,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        showlegend=False,
    )
    return fig
```

- [ ] **Step 2: syntax + import チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/18_aql_sampling/visualize.py', encoding='utf-8').read()); print('syntax OK')"
```

```bash
cd 02_manufacturing/18_aql_sampling && python -c "import visualize; print('import OK')"
```

期待: `syntax OK` → `import OK`

- [ ] **Step 3: コミット**

```bash
git add 02_manufacturing/18_aql_sampling/visualize.py
git commit -m "feat(C-72): visualize.py — OC 曲線（α/β マーカー付き）"
```

---

### Task 4: app.py + STATUS.md（production-ready）

**Files:**
- Create: `02_manufacturing/18_aql_sampling/app.py`
- Modify: `02_manufacturing/18_aql_sampling/STATUS.md`

- [ ] **Step 1: `app.py` を作成**

```python
"""AQL/受入サンプリング計画最適化 — JIS Z 9015-1 × OC 曲線 × ロット合否判定。"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import analyze
import visualize
from tables import VALID_AQL

st.set_page_config(page_title="AQL 受入サンプリング計画", page_icon="📋", layout="wide")

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
    "📋 AQL/受入サンプリング計画最適化 — JIS Z 9015-1 × OC 曲線</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙ 計画設計")
    lot_size = st.number_input(
        "ロットサイズ N", min_value=2, max_value=500000, value=500, step=1,
    )
    aql = st.selectbox(
        "AQL 水準（%）",
        options=VALID_AQL,
        index=VALID_AQL.index(1.0),
        format_func=lambda v: f"{v}%",
    )
    inspection_level = st.radio(
        "検査水準",
        options=[1, 2, 3],
        index=1,
        format_func=lambda v: f"水準 {'I' if v == 1 else 'II' if v == 2 else 'III'}",
        horizontal=True,
    )
    run_btn = st.button("▶ 計画作成", type="primary", use_container_width=True)

    st.divider()
    st.header("🔍 ロット判定（任意）")
    st.caption("計画作成後に不良数を入力")
    defects = st.number_input("実際の不良数 d", min_value=0, value=0, step=1)
    judge_btn = st.button("▶ 判定 + 記録", use_container_width=True)

# ── 計画作成 ──────────────────────────────────────────────────────
if run_btn:
    try:
        result = analyze.run_plan(lot_size, aql, inspection_level)
        st.session_state["plan"]   = result
        st.session_state["params"] = {"lot_size": lot_size, "aql": aql,
                                      "inspection_level": inspection_level}
        st.session_state.pop("judgment", None)
    except ValueError as e:
        st.error(str(e))
        st.stop()

plan = st.session_state.get("plan")
if not plan:
    st.info("サイドバーの「▶ 計画作成」をクリックしてサンプリング計画を生成してください。")
    st.stop()

# ── KPI 4列 ───────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("サンプルサイズコード", plan["code"])
c2.metric("抜取数", f"{plan['n']} 個")
c3.metric("合格判定数", f"Ac = {plan['ac']}")
c4.metric("不合格判定数", f"Re = {plan['re']}")

# ── OC 曲線 ───────────────────────────────────────────────────────
params = st.session_state["params"]
fig = visualize.oc_chart(
    plan["oc_p"], plan["oc_pa"],
    params["aql"], plan["alpha"],
    plan["rql"],   plan["beta"],
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    f"生産者リスク α={plan['alpha']:.1%}（AQL={params['aql']}% 時の不合格確率）　"
    f"消費者リスク β={plan['beta']:.1%}（RQL={plan['rql']*100:.1f}% 時の合格確率）"
)

# ── ロット判定 ────────────────────────────────────────────────────
if judge_btn:
    judgment = analyze.judge_lot(int(defects), plan["ac"])
    st.session_state["judgment"] = judgment

    _COLOR = {"good": "#16a34a", "alert": "#dc2626"}
    _LABEL = {"good": "合格", "alert": "不合格"}
    v = judgment["verdict"]
    st.markdown(
        f'<div style="background:{_COLOR[v]}22;border-left:4px solid {_COLOR[v]};'
        f'padding:12px 16px;border-radius:4px;margin-top:12px">'
        f'<b style="color:{_COLOR[v]};font-size:20px">'
        f'{_LABEL[v]}（不良数 {defects} 個 / Ac={plan["ac"]}）</b>'
        f'</div>',
        unsafe_allow_html=True,
    )

    try:
        from _common.db_writer import init_db, write_upload, write_kpi
        init_db()
        uid = write_upload(
            "aql_sampling",
            f"lot_N{params['lot_size']}_AQL{params['aql']}",
            1,
        )
        write_kpi(
            uid, "aql_sampling",
            datetime.now().strftime("%Y-%m"),
            "acceptance",
            1.0 if judgment["result"] == "accept" else 0.0,
            judgment["verdict"],
        )
    except Exception as _e:
        st.caption(f"⚠ DB書き込みスキップ: {_e}")
```

- [ ] **Step 2: `STATUS.md` を production-ready に更新**

```markdown
# C-72 AQL/受入サンプリング計画最適化

- name: AQL/受入サンプリング計画最適化
- industry: 製造
- department: 品質保証
- status: production-ready
```

- [ ] **Step 3: syntax チェック**

```bash
python -c "import ast; ast.parse(open('02_manufacturing/18_aql_sampling/app.py', encoding='utf-8').read()); print('OK')"
```

期待: `OK`

- [ ] **Step 4: 全テスト確認**

```bash
python -m pytest 02_manufacturing/18_aql_sampling/tests/test_analyze.py -v
```

期待: `8 passed`

- [ ] **Step 5: コミット**

```bash
git add 02_manufacturing/18_aql_sampling/app.py \
        02_manufacturing/18_aql_sampling/STATUS.md
git commit -m "feat(C-72): app.py + STATUS.md production-ready（計画設計 + OC 曲線 + ロット判定 + DB 書き込み）"
```

---

### Task 5: dashboard.py + catalog.yml 更新

**Files:**
- Modify: `02_manufacturing/09_unified_dashboard/dashboard.py`（CARDS に追加）
- Modify: `catalog.yml`（C-72 エントリ追加）

- [ ] **Step 1: `dashboard.py` の CARDS リスト末尾に追加**

`02_manufacturing/09_unified_dashboard/dashboard.py` を Read して CARDS リストの末尾を確認し、
以下のエントリを末尾に追加する（既存の最後のエントリの後）:

```python
    {"system_id": "aql_sampling", "metric": "acceptance",
     "title": "直近ロット合否", "fmt": lambda v: "合格" if v >= 1.0 else "不合格"},
```

- [ ] **Step 2: `catalog.yml` の末尾に C-72 エントリを追記**

```yaml
- id: "C-72"
  name: "AQL/受入サンプリング計画最適化 — OC曲線・抜取方式設計"
  industry: "製造"
  department: "品質保証"
  difficulty: "★★☆"
  status: "production-ready"
  priority: "B"
  path: "02_manufacturing/18_aql_sampling"
  demo: "streamlit run 02_manufacturing/18_aql_sampling/app.py"
  description: |
    ロットサイズ・AQL 水準・検査水準を入力し、JIS Z 9015-1 テーブルから
    サンプルサイズ n と合格判定数 Ac を自動算出。
    OC 曲線で生産者リスク α と消費者リスク β を可視化し、
    実際の検査不良数を入力することでロット合否判定と DB 記録を行う。
```

- [ ] **Step 3: 全テスト確認**

```bash
python -m pytest 02_manufacturing/18_aql_sampling/tests/ -v
```

期待: `8 passed`

- [ ] **Step 4: コミット**

```bash
git add 02_manufacturing/09_unified_dashboard/dashboard.py catalog.yml
git commit -m "feat(C-72): C-63ダッシュボード + catalog.yml に C-72 追加"
```
