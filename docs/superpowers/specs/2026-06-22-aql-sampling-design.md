# AQL/受入サンプリング計画最適化 設計仕様書

**作成日:** 2026-06-22
**システムID:** C-72
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質保証（QA）

---

## 1. 概要

ロットサイズ・AQL 水準・検査水準を入力し、JIS Z 9015-1（ISO 2859-1）テーブルから
サンプルサイズ n と合格判定数 Ac を自動算出する。
OC 曲線（生産者リスク α × 消費者リスク β 可視化）でサンプリング計画の特性を確認し、
実際の検査結果を入力することでロット合否判定と DB 連携を行う。

---

## 2. 入力仕様

### Mode 1（計画設計）— パラメータ入力

| パラメータ | 型 | 選択肢 / 範囲 |
|-----------|-----|--------------|
| ロットサイズ N | int | 2〜500,000 |
| AQL 水準 | float | 0.065 / 0.10 / 0.15 / 0.25 / 0.40 / 0.65 / 1.0 / 1.5 / 2.5 / 4.0 / 6.5 |
| 検査水準 | int | 1（水準I）/ 2（水準II）/ 3（水準III） |

デフォルト値: N=500, AQL=1.0, 検査水準=2（水準II）

### Mode 2（ロット判定）— オプション

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| 不良数 d | int | 実際の検査で見つかった不良品数 |

---

## 3. ファイル構成

```text
02_manufacturing/18_aql_sampling/
├── app.py           # Streamlit UI（2モード）
├── analyze.py       # サンプリング計画計算 + OC 曲線（純粋関数）
├── visualize.py     # Plotly OC 曲線
├── tables.py        # JIS Z 9015-1 テーブル定数
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD）
```

sample_data.py は不要（パラメータ入力型のため UI デフォルト値で代替）。

---

## 4. データフロー

```text
パラメータ（N, AQL, 検査水準）
  └─ app.py
       └─ analyze.py: run_plan() → n/Ac/Re + OC 曲線データ
            ├─ visualize.py: oc_chart() → OC 曲線 Plotly Figure
            └─ [Mode 2] judge_lot(d, Ac) → accept/reject + verdict
                  └─ _common/db_writer.py: write_kpi("aql_sampling", ..., "acceptance", 1.0|0.0, verdict)
                        └─ C-63 dashboard: aql_sampling カード追加
```

---

## 5. tables.py — JIS Z 9015-1 テーブル定数

### サンプルサイズコード表

ロットサイズ範囲 × 検査水準（1/2/3）→ サンプルサイズコード（A〜R）

```python
# (lot_min, lot_max): {inspection_level: code}
SAMPLE_SIZE_CODE_TABLE = [
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
```

### n/Ac/Re テーブル

サンプルサイズコード × AQL → (n, Ac, Re)

```python
# (code, aql): (n, Ac, Re)
# Ac=None は矢印（↓ 次のコードを使用）を表す
AQL_TABLE: dict[tuple[str, float], tuple[int, int | None, int | None]] = {
    ("A", 0.65): (2,  0, 1),
    ("A", 1.0):  (2,  0, 1),
    ("A", 1.5):  (2,  0, 1),
    ("B", 0.65): (3,  0, 1),
    ("B", 1.0):  (3,  0, 1),
    ("C", 0.65): (5,  0, 1),
    ("C", 1.0):  (5,  0, 1),
    ("D", 0.65): (8,  0, 1),
    ("D", 1.0):  (8,  0, 1),
    ("E", 0.65): (13, 0, 1),
    ("E", 1.0):  (13, 0, 1),
    ("F", 0.65): (20, 0, 1),
    ("F", 1.0):  (20, 0, 1),
    ("G", 0.65): (32, 0, 1),
    ("G", 1.0):  (32, 0, 1),
    ("H", 0.65): (50, 1, 2),
    ("H", 1.0):  (50, 1, 2),
    ("J", 0.65): (80, 1, 2),
    ("J", 1.0):  (80, 2, 3),
    ("K", 0.65): (125, 2, 3),
    ("K", 1.0):  (125, 3, 4),
    # 省略部分は実装時に完全版を記載
    # AQL 2.5, 4.0, 6.5 も同様のパターンで追加
}
```

テーブルが未定義の組み合わせ（AQL が小さすぎてコードに対応なし等）は
`ValueError("この AQL 水準はロットサイズに対して適用できません")` を raise する。

---

## 6. analyze.py — 計算ロジック

### シグネチャ

```python
def get_sampling_plan(lot_size: int, aql: float, inspection_level: int = 2) -> dict:
    """JIS テーブルからサンプリング計画を引き当てる。"""
    # → {"code": str, "n": int, "ac": int, "re": int}

def oc_curve(n: int, ac: int, p_values: list[float]) -> list[float]:
    """二項分布累積でOC曲線の Pa 値列を計算する。"""
    # Pa(p) = Σ(k=0→Ac) C(n,k) * p^k * (1-p)^(n-k)
    # → list[float]（Pa 値列、len == len(p_values)）

def judge_lot(defects: int, ac: int) -> dict:
    """実際の不良数と Ac を比較してロット合否を判定する。"""
    # → {"result": "accept"|"reject", "verdict": "good"|"alert"}

def run_plan(lot_size: int, aql: float, inspection_level: int = 2) -> dict:
    """計画設計の全出力をまとめて返す。"""
    # → {
    #     "code":   str,        # サンプルサイズコード
    #     "n":      int,        # 抜取数
    #     "ac":     int,        # 合格判定数
    #     "re":     int,        # 不合格判定数
    #     "oc_p":   list[float], # OC曲線 x軸（0.0〜0.15, 100点）
    #     "oc_pa":  list[float], # OC曲線 y軸（Pa値列）
    #     "alpha":  float,       # 生産者リスク（1 - Pa at p=AQL/100）
    #     "rql":    float,       # 消費者リスク点 p（Pa ≤ 0.10 となる最小 p）
    #     "beta":   float,       # 消費者リスク（Pa at p=RQL）
    # }
```

### バリデーション

```python
VALID_AQL = [0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.0, 1.5, 2.5, 4.0, 6.5]

if lot_size < 2:
    raise ValueError("ロットサイズは 2 以上で入力してください。")
if aql not in VALID_AQL:
    raise ValueError(f"AQL は {VALID_AQL} のいずれかを指定してください。")
if inspection_level not in (1, 2, 3):
    raise ValueError("検査水準は 1・2・3 のいずれかを指定してください。")
```

### RQL の求め方

```python
# OC 曲線上で Pa <= 0.10 となる最初の p を RQL とする
rql = next((p for p, pa in zip(oc_p, oc_pa) if pa <= 0.10), oc_p[-1])
beta = oc_pa[oc_p.index(rql)]  # RQL 点での Pa（≒ 0.10）
```

---

## 7. visualize.py — OC 曲線

```python
def oc_chart(oc_p, oc_pa, aql, alpha, rql, beta) -> go.Figure:
```

- 折れ線: Pa vs p（navy `#1e3a5f`、`mode="lines"`）
- AQL マーカー: `add_vline(x=aql/100, line_color="#16a34a", line_dash="dash")`
  - annotation: `f"AQL={aql}%  α={alpha:.1%}"`
- RQL マーカー: `add_vline(x=rql, line_color="#dc2626", line_dash="dot")`
  - annotation: `f"RQL={rql*100:.1f}%  β={beta:.1%}"`
- x 軸: "不良率 p（%）"、`tickformat=".1%"`
- y 軸: "合格確率 Pa"、range=[0, 1.05]
- 高さ: 380px、BG: `#f5f7fa`

---

## 8. app.py — UI レイアウト

```text
┌─────────────────┬──────────────────────────────────────────┐
│ ⚙ 計画設計       │ KPI（4列）                               │
│  ロットサイズ N  │  コード | 抜取数 n | 合格判定数 Ac | Re   │
│  AQL%           │                                          │
│  検査水準 I/II/III│  OC 曲線（α・β マーカー付き）             │
│  [▶ 計画作成]   │                                          │
│ ─────────────── │                                          │
│ ロット判定（任意）│                                          │
│  不良数 d        │                                          │
│  [▶ 判定 + 記録]│  合否カード（合格/不合格 色付き）           │
└─────────────────┴──────────────────────────────────────────┘
```

### KPI 4列（計画設計後に表示）

| 列 | 表示内容 |
|----|---------|
| c1 | サンプルサイズコード（`{code}`）|
| c2 | 抜取数（`{n} 個`）|
| c3 | 合格判定数（`Ac={ac}`）|
| c4 | 不合格判定数（`Re={re}`）|

### verdict ラベル（ロット判定時）

```python
_LABEL = {"good": "合格", "alert": "不合格"}
_COLOR = {"good": "#16a34a", "alert": "#dc2626"}
```

### 状態管理

- `st.session_state["plan"]` — run_plan() の結果を保持
- ロット判定は plan が存在するときのみ表示

### エラーハンドリング

- ValueError（テーブル未定義・バリデーション）→ `st.error()` + `st.stop()`
- DB 書き込み失敗 → `except Exception: st.caption(...)` でアプリ継続

---

## 9. DB 統合

```python
init_db()
uid = write_upload("aql_sampling", f"lot_N{lot_size}_AQL{aql}", 1)
write_kpi(
    uid, "aql_sampling",
    datetime.now().strftime("%Y-%m"),
    "acceptance",
    1.0 if result == "accept" else 0.0,
    verdict,  # "good" or "alert"
)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "aql_sampling", "metric": "acceptance",
 "title": "直近ロット合否", "fmt": lambda v: "合格" if v >= 1.0 else "不合格"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（TDD）:

| テスト名 | 内容 |
|---------|------|
| `test_lot_size_to_code` | N=500, 水準II → コード "H" |
| `test_get_sampling_plan` | N=500, AQL=1.0, 水準II → n=50, Ac=1, Re=2 |
| `test_oc_curve_at_zero` | p=0.0 → Pa=1.0 |
| `test_oc_curve_at_one` | p=1.0, Ac=0 → Pa=0.0 |
| `test_judge_accept` | d=1, Ac=2 → result="accept", verdict="good" |
| `test_judge_reject` | d=3, Ac=2 → result="reject", verdict="alert" |
| `test_run_plan_keys` | 全9キーが揃っていること |
| `test_invalid_lot_size` | lot_size=1 → ValueError |

---

## 11. catalog.yml エントリ

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

---

## 12. スコープ外（将来対応）

- 飛び矢印処理（JIS テーブルで「↑」「↓」が発生する AQL/コードの組み合わせ）
- 計量型サンプリング（JIS Z 9015-2）
- ダブルサンプリング・多次サンプリング
- 検査水準 S-1〜S-4（特殊検査水準）
