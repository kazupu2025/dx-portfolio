# 是正処置（8D）効果検証 設計仕様書

**作成日:** 2026-06-21
**システムID:** C-70
**難易度:** ★★☆
**カテゴリ:** 製造業 / 品質管理（QA）

---

## 1. 概要

是正処置（8D）実施前後の品質データを CSV でアップロードし、
t検定 + Mann-Whitney U検定の両方を実行して統計的有意差を自動判定する。
C-66（4M変更有意差検定）と同じ統計エンジンを使用するが、
**verdict ロジックを反転**させる点が核心:
- C-66: 有意差あり = 悪化（alert）
- C-70: 有意差あり = 是正効果確認（good）

結果を quality.db に書き込み、C-63 統合ダッシュボードに連携する。

---

## 2. 入力データ仕様

### CSV フォーマット（Wide 形式 / group 列 + value 列）

```csv
group,measurement
before,12.3
before,11.8
before,13.1
after,8.2
after,7.9
after,8.6
```

- `group` 列: 是正前後を識別する文字列（例: "before"/"after"、"是正前"/"是正後"）
- `value` 列: 測定値（不良率%、不良件数、寸法値など）
- 最低構成: 各グループ n ≥ 3
- 推奨: 各グループ n ≥ 20

---

## 3. ファイル構成

```text
02_manufacturing/14_corrective_action/
├── app.py           # Streamlit UI + DB統合
├── analyze.py       # 検定ロジック（verdict ロジックを C-66 から反転）
├── visualize.py     # C-66 の hist_chart + box_chart をそのまま転用
├── sample_data.py   # デモCSV生成（是正前 n=30 / 是正後 n=30）
├── STATUS.md
└── tests/
    ├── __init__.py
    └── test_analyze.py   # 8テスト（TDD、verdict 反転を検証）
```

> **重要:** `visualize.py` は C-66 (`02_manufacturing/12_4m_change/visualize.py`) の
> `hist_chart` / `box_chart` をそのまま転用するため、新規ロジックなし。
> `app.py` 内で sys.path を通して直接 import する。

---

## 4. データフロー

```text
CSV（group列 + value列）
  └─ app.py: 列選択・before/afterラベル指定
       └─ analyze.py: run_analysis() → 検定結果 dict
            ├─ visualize（C-66 の hist_chart / box_chart を転用）
            └─ _common/db_writer.py: write_kpi("corrective_action", ..., "p_value", p, verdict)
                 └─ C-63 dashboard: corrective_action カード追加
```

---

## 5. analyze.py — 検定ロジック

### シグネチャ（C-66 と同一）

```python
def run_analysis(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    before_label: str,
    after_label: str,
) -> dict:
```

### 処理フロー（C-66 と同一）

1. `before_label` / `after_label` でグループ分離
2. n < 3 のグループがあれば ValueError
3. Shapiro-Wilk 正規性検定（scipy.stats.shapiro）
4. t検定（Welch、equal_var=False）+ Cohen's d
5. Mann-Whitney U検定（two-sided）+ rank-biserial r
6. 推奨検定選択（両方正規 → "t" / それ以外 → "mw"）
7. **verdict 判定（C-66 から反転）**

### verdict 基準（C-70 固有 — C-66 と逆）

| 条件 | verdict | 意味 |
|------|---------|------|
| p < 0.05 かつ効果量 ≥ 0.5 | `"good"` | 是正効果確認（統計的有意、大きな改善）|
| p < 0.05 かつ効果量 < 0.5 | `"warning"` | 軽微な効果（有意だが効果量小、継続監視）|
| p ≥ 0.05 | `"alert"` | 効果不明（有意差なし、是正処置の再検討）|

### 出力 dict（C-66 と同一 — 20キー）

```python
{
    # 記述統計
    "n_before": int,
    "n_after": int,
    "mean_before": float,
    "mean_after": float,
    "std_before": float,
    "std_after": float,
    # 正規性検定
    "shapiro_before_p": float,
    "shapiro_after_p": float,
    "normal_before": bool,
    "normal_after": bool,
    # t検定
    "t_stat": float,
    "t_pvalue": float,
    "cohens_d": float,
    # Mann-Whitney U検定
    "mw_stat": float,
    "mw_pvalue": float,
    "rank_biserial_r": float,
    # 推奨・総合
    "recommended": str,    # "t" または "mw"
    "p_value": float,      # 推奨検定の p 値
    "effect_size": float,  # 推奨検定の効果量（絶対値）
    "verdict": str,        # "good" | "warning" | "alert"
}
```

---

## 6. visualize.py — Plotly チャート

C-66 の `02_manufacturing/12_4m_change/visualize.py` をそのまま転用する。
新規ファイルとして作成せず、`app.py` 内で以下のように import する:

```python
_C66 = Path(__file__).parent.parent / "12_4m_change"
if str(_C66) not in sys.path:
    sys.path.insert(0, str(_C66))
import visualize
```

使用する関数:
- `hist_chart(before_arr, after_arr, before_label, after_label)` — ヒストグラム重ね
- `box_chart(before_arr, after_arr, before_label, after_label)` — 箱ひげ図

---

## 7. sample_data.py — デモ用サンプルデータ

```python
"""
是正前: μ=12.0（不良率%）、σ=2.0、n=30 → 高い不良率
是正後: μ=8.0、σ=1.5、n=30 → 是正効果で改善
→ p < 0.05、効果量大 → verdict = "good" が期待される
"""
rng = np.random.default_rng(42)
```

列構成: `group`, `measurement`（C-66 と同一）

---

## 8. app.py — UI レイアウト

C-66 の `app.py` と同一構造。変更点は以下のみ:

### タイトル
```
📊 是正処置（8D）効果検証 — 変化点有意差検定（t検定/Mann-Whitney）
```

### verdict ラベル（C-66 から変更）

```python
_LABEL = {"good": "是正効果確認", "warning": "軽微な効果", "alert": "効果不明"}
```

| verdict | ラベル | 色 |
|---------|--------|-----|
| good | 是正効果確認 | #16a34a |
| warning | 軽微な効果 | #d97706 |
| alert | 効果不明 | #dc2626 |

### 状態管理（C-66 と同一）
- `st.session_state["df"]` / `st.session_state["result"]`

### DB 書き込み
```python
write_kpi(uid, "corrective_action", datetime.now().strftime("%Y-%m"), "p_value", p_val, verdict)
```

---

## 9. DB 統合

```python
init_db()
uid = write_upload("corrective_action", filename, row_count)
write_kpi(uid, "corrective_action", datetime.now().strftime("%Y-%m"), "p_value", p_val, verdict)
```

### C-63 ダッシュボード — CARDS 追加

```python
{"system_id": "corrective_action", "metric": "p_value",
 "title": "是正処置効果（p値）", "fmt": lambda v: f"{v:.4f}"}
```

---

## 10. テスト方針（test_analyze.py）

8テスト（C-66 の verdict ロジック反転を確認）:

| テスト名 | 内容 | C-66 との違い |
|---------|------|-------------|
| test_no_significant_diff | p ≥ 0.05 → `"alert"` | C-66 は `"good"` |
| test_significant_large_effect | p < 0.05 + 効果量 ≥ 0.5 → `"good"` | C-66 は `"alert"` |
| test_significant_small_effect | p < 0.05 + 効果量 < 0.5 → `"warning"` | 同じ |
| test_normality_selects_ttest | 両グループ正規 → `recommended="t"` | 同じ |
| test_nonnormal_selects_mannwhitney | 非正規 → `recommended="mw"` | 同じ |
| test_cohens_d_formula | Cohen's d = |mean_after - mean_before| / pooled_std | 同じ |
| test_output_keys | 全20キーが揃う | 同じ |
| test_insufficient_data_raises | n < 3 で ValueError | 同じ |

---

## 11. catalog.yml エントリ

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

---

## 12. スコープ外（将来対応）

- 是正処置番号（8D番号）の管理・紐付け
- 複数是正処置の一覧比較
- 是正前後の時系列推移グラフ
- 対応のある t検定（同一個体の前後測定）
