# SPC管理図（X-bar/R + 異常8ルール）設計仕様書

**作成日:** 2026-06-20
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質管理（QC）

---

## 1. 概要

工程測定データを CSV でアップロードし、X-bar 管理図・R 管理図を描画する。
UCL/LCL を自動計算し、Western Electric 異常8ルールを適用して管理逸脱ポイントを自動検出する。
分析結果は統合品質 DB（quality.db）に書き込み、C-63 横断ダッシュボードに SPC カードを追加する。

---

## 2. 入力データ仕様

### CSV フォーマット（ロング形式）

```csv
lot_no, process, value
L001,   溶接,   10.03
L001,   溶接,   10.07
L001,   溶接,    9.98
L002,   溶接,   10.01
...
```

- 1行 = 1測定値
- サブグループは `subgroup_col`（lot_no 等）の同一値で形成
- n が混在する場合は最頻サブグループサイズを採用し、UI に警告を表示
- 対応サブグループサイズ: n = 2〜10

---

## 3. ファイル構成

```text
02_manufacturing/10_spc_chart/
├── app.py          # Streamlit UI（左右分割レイアウト）
├── analyze.py      # X-bar/R 制御限界計算
├── rules.py        # 異常8ルール判定
├── visualize.py    # Plotly 管理図描画
├── sample_data.py  # デモ用サンプルCSV生成
├── STATUS.md
└── tests/
    ├── test_analyze.py   # 制御限界計算ユニットテスト
    └── test_rules.py     # 8ルール判定ユニットテスト
```

---

## 4. データフロー

```text
CSVアップロード
  └─ app.py: 列選択（process_col / value_col / subgroup_col）
       └─ analyze.py: サブグループ集約 → x̄, R → UCL/LCL
            └─ rules.py: 8ルール違反ポイント検出
                 ├─ visualize.py: X-bar + R 管理図（違反点を赤マーカー）
                 └─ _common/db_writer.py: write_upload + write_kpi
                      └─ C-63 dashboard.py: SPC カード表示
```

---

## 5. analyze.py — 制御限界計算

### 制御図定数テーブル（n=2〜10）

```python
CONSTANTS = {
    2:  {"A2": 1.880, "D3": 0,     "D4": 3.267, "d2": 1.128},
    3:  {"A2": 1.023, "D3": 0,     "D4": 2.575, "d2": 1.693},
    4:  {"A2": 0.729, "D3": 0,     "D4": 2.282, "d2": 2.059},
    5:  {"A2": 0.577, "D3": 0,     "D4": 2.115, "d2": 2.326},
    6:  {"A2": 0.483, "D3": 0,     "D4": 2.004, "d2": 2.534},
    7:  {"A2": 0.419, "D3": 0.076, "D4": 1.924, "d2": 2.704},
    8:  {"A2": 0.373, "D3": 0.136, "D4": 1.864, "d2": 2.847},
    9:  {"A2": 0.337, "D3": 0.184, "D4": 1.816, "d2": 2.970},
    10: {"A2": 0.308, "D3": 0.223, "D4": 1.777, "d2": 3.078},
}
```

### 計算式

**X-bar 管理図:**
- x̄̄ = mean(x̄ᵢ)
- R̄ = mean(Rᵢ)  ※ Rᵢ = max(subgroup_i) - min(subgroup_i)
- UCL = x̄̄ + A₂ × R̄
- LCL = x̄̄ - A₂ × R̄

**R 管理図:**
- UCL = D₄ × R̄
- LCL = D₃ × R̄

**8ルール用σ推定:**
- σ̂ = R̄ / d₂（Shewhart の推定量）

### run_analysis の出力形式

```python
{
    "n": int,                  # 代表サブグループサイズ
    "xbar_cl": float,
    "xbar_ucl": float,
    "xbar_lcl": float,
    "r_cl": float,
    "r_ucl": float,
    "r_lcl": float,
    "sigma": float,            # σ̂ = R̄ / d₂
    "subgroups": [
        {"label": str, "xbar": float, "r": float},
        ...
    ]
}
```

---

## 6. rules.py — 異常8ルール判定

### インターフェース

```python
def detect_violations(
    xbars: list[float],   # [s["xbar"] for s in result["subgroups"]]
    cl: float,            # result["xbar_cl"]
    sigma: float,         # result["sigma"]
) -> dict[int, list[int]]:
    """
    Returns: {rule_no: [violated_index, ...]}
    R管理図向けには rule1_r(rs, r_ucl) を別途提供
    """
```

### 8ルール定義

| Rule | 名称 | 判定条件 |
|------|------|---------|
| 1 | 3σ超過 | \|xᵢ - CL\| > 3σ |
| 2 | 2of3 | 連続3点中2点が同側2σ外 |
| 3 | 4of5 | 連続5点中4点が同側1σ外 |
| 4 | 8点片側 | 連続8点が中心線の同側 |
| 5 | 6点トレンド | 連続6点が単調増加 or 単調減少 |
| 6 | 14点交互 | 連続14点が交互に上下 |
| 7 | 15点1σ内 | 連続15点が±1σ内（ハガーリング） |
| 8 | 8点1σ外両側 | 連続8点が全て±1σ外（混合パターン） |

R 管理図: `rule1_r(rs, r_ucl) -> list[int]` のみ適用（UCL 超過検出）。

---

## 7. visualize.py — Plotly 管理図描画

### xbar_chart(result, violations) → go.Figure

- UCL / CL / LCL を水平点線で描画（UCL/LCL は赤、CL は navy 破線）
- 違反ポイントは赤マーカー（● ）、正常ポイントは navy（● ）
- ゾーン線（±1σ, ±2σ）をオプションで表示

### r_chart(result, violations_r) → go.Figure

- UCL / CL / LCL を水平点線で描画
- Rule 1 違反のみ赤マーカー

---

## 8. app.py — UI レイアウト

```text
┌─────────────────────────────────────────────────────┐
│  [Sidebar]              │  [Main]                   │
│  📂 CSV アップロード      │  X-bar 管理図（大）        │
│  工程列       [▾]        │  ─────────────────────    │
│  測定値列     [▾]        │  R 管理図（中）            │
│  サブグループ列 [▾]       │  ─────────────────────    │
│  [▶ 分析実行]            │  [違反ポイント一覧テーブル] │
└─────────────────────────────────────────────────────┘
```

- カラーテーマ: navy=#1e3a5f, alert=#dc2626, bg=#f5f7fa, フォント BIZ UDGothic
- サンプルデータボタンで `sample_data.py` 生成の CSV を自動ロード

---

## 9. DB 統合

### db_writer 呼び出し（app.py 分析実行後）

```python
init_db()
uid = write_upload("spc", uploaded.name, len(df))
# violations = {rule_no: [idx, ...]} — 複数ルールで同一点が重複する場合は1点として数える
all_violated = set(idx for indices in violations.values() for idx in indices)
violation_pct = len(all_violated) / len(result["subgroups"]) * 100
verdict = "good" if violation_pct < 5 else "warning" if violation_pct < 10 else "alert"
write_kpi(uid, "spc", datetime.now().strftime("%Y-%m"),
          "out_of_control_pct", violation_pct, verdict)
```

### C-63 ダッシュボード — CARDS 追加

`02_manufacturing/09_unified_dashboard/dashboard.py` の CARDS に追加:

```python
{"system_id": "spc", "metric": "out_of_control_pct",
 "title": "SPC 管理逸脱率", "fmt": lambda v: f"{v:.1f}%"}
```

verdict カラー: good（<5%）/ warning（<10%）/ alert（≥10%）

---

## 10. テスト方針

### test_analyze.py（最低6テスト）

| テスト名 | 内容 |
|---------|------|
| test_subgroup_stats | x̄ と R が正しく計算されること |
| test_xbar_ucl_lcl | n=5 の A₂ を使って UCL/LCL が正しいこと |
| test_r_ucl_lcl | D₃/D₄ による R 管理図制御限界 |
| test_sigma_estimate | σ̂ = R̄/d₂ |
| test_variable_n_uses_mode | n が混在する場合は最頻値を採用 |
| test_single_subgroup_raises | サブグループ数 <2 で ValueError |

### test_rules.py（最低8テスト、各ルール1本）

| テスト名 | 内容 |
|---------|------|
| test_rule1_detects_3sigma | 3σ超過点を検出 |
| test_rule2_detects_2of3 | 3点中2点が2σ外（同側） |
| test_rule3_detects_4of5 | 5点中4点が1σ外（同側） |
| test_rule4_detects_8_same_side | 連続8点が同側 |
| test_rule5_detects_trend | 連続6点単調増加 |
| test_rule6_detects_alternating | 連続14点交互 |
| test_rule7_detects_hugging | 連続15点±1σ内 |
| test_rule8_detects_mixture | 連続8点±1σ外両側 |

---

## 11. スコープ外（将来対応）

- X-bar/s 管理図（n>10 の大サブグループ向け）
- I-MR 管理図（n=1 の個別値向け）
- Phase II 管理（既知の管理限界を外部入力）
- C-61 ポータルとの統合

---

## 12. カラーテーマ（C-61/C-62/C-63 統一）

| 用途 | カラーコード |
|------|------------|
| ヘッダー背景 | `#1e3a5f` |
| good | `#16a34a` / `#dcfce7` |
| warning | `#d97706` / `#fff7ed` |
| alert | `#dc2626` / `#fef2f2` |
| ページ背景 | `#f5f7fa` |
| フォント | BIZ UDGothic |
