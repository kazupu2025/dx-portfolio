# C-108 AI外観検査自動判定

Deep Learning なしで PIL + numpy のルールベース画像解析により外観検査を実現する自動判定システム。

## 機能

### 検査対象（4つの不良タイプ）

1. **輝度（明るさの偏り）**
   - 暗すぎる → 汚れ・変色検出
   - 明るすぎる → 過露光・反射検出

2. **エッジ密度（輪郭の多さ）**
   - エッジ過多 → 傷・亀裂検出

3. **暗領域率**
   - 暗領域過多 → 穴・欠損検出

4. **色分散**
   - 色分散過大 → 色ムラ検出

## ファイル構成

```
54_visual_inspection/
├── inspector.py          # コア検査ロジック
├── app.py               # Streamlit UI
├── requirements.txt     # 依存パッケージ
├── STATUS.md            # ステータス定義
├── README.md            # このファイル
└── tests/
    └── test_analyze.py  # ユニットテスト（8テスト）
```

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

### テストの実行

```bash
python -m pytest tests/ -v
```

### Streamlit アプリの実行

```bash
streamlit run app.py
```

## API リファレンス

### `inspect(img_bytes: bytes) -> dict`

画像バイト列を入力して、検査結果を返します。

**入力:**
- `img_bytes` (bytes): PNG/JPG/BMP 画像データ

**出力:**
```python
{
    "verdict": "合格" | "不合格（要確認）",
    "defects": [list of defect strings],
    "defect_score": float (0.0-1.0),
    "brightness": float,
    "edge_density": float,
    "dark_ratio": float,
    "color_variance": float,
    "scores": {
        "brightness": float,
        "edge": float,
        "dark": float,
        "color": float
    }
}
```

### `extract_features(img_bytes: bytes) -> dict`

画像から特徴量を抽出します。

**出力:**
```python
{
    "brightness": float,       # 平均輝度 (0.0-1.0)
    "edge_density": float,     # エッジ密度
    "dark_ratio": float,       # 暗領域割合
    "color_variance": float    # 色成分の標準偏差
}
```

### `classify(features: dict) -> dict`

特徴量から不良判定を実施します。

**出力:**
```python
{
    "verdict": "合格" | "不合格（要確認）",
    "defects": [list of defect strings],
    "defect_score": float (0.0-1.0),
    "scores": {
        "brightness": float,
        "edge": float,
        "dark": float,
        "color": float
    }
}
```

## テスト

8つのテストケースで以下を検証：

1. `test_extract_features_returns_dict` - 特徴量辞書の型チェック
2. `test_feature_keys` - 必要なキーの存在確認
3. `test_bright_image` - 明るい画像の検出
4. `test_dark_image_detected` - 暗い画像の検査結果（不合格判定）
5. `test_clean_image_passes` - 正常画像の検査結果（合格判定）
6. `test_inspect_has_verdict` - 判定結果の存在確認
7. `test_defect_score_range` - 不良スコアの範囲チェック（0.0-1.0）
8. `test_edge_detection` - エッジ検出の精度確認

全テスト実行:
```bash
pytest tests/test_analyze.py -v
```

## 設定

`inspector.py` の `THRESHOLDS` で検査閾値を調整可能：

```python
THRESHOLDS = {
    "brightness_low": 0.25,      # 暗さの閾値（汚れ検出）
    "brightness_high": 0.95,     # 明るさの閾値（過露光検出）
    "edge_density_high": 0.15,   # エッジ密度の閾値（傷検出）
    "dark_ratio_high": 0.20,     # 暗領域率の閾値（欠損検出）
    "color_variance_high": 60,   # 色分散の閾値（色ムラ検出）
}
```

## 実装詳細

### 特徴量抽出

1. 画像を RGB に変換し 256×256 にリサイズ
2. 輝度：RGB の平均値を 0-1 にスケール
3. エッジ密度：Sobel フィルタで輪郭を検出
4. 暗領域率：輝度 < 0.2 のピクセル割合
5. 色分散：RGB 値の標準偏差

### 分類ロジック

4つの検査項目を独立で実施し、各項目の異常度を 0-1 にスケール。
最終不良スコアは 4 項目の平均。

不良スコア > 0 であれば不合格判定。

## パフォーマンス

- 処理時間：画像 1 枚あたり約 100-200ms（CPU 依存）
- メモリ：ピーク約 50MB
- Deep Learning モデル不要で高速検査を実現

## ライセンス

このシステムは DX ポートフォリオの一部です。
