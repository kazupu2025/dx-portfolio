# DX ポートフォリオ

業務改善コンサルタント向け DX システムストック集。

**✅ Production-ready: 112 システム** | 対応業種: 20 | 最終更新: 2026-06-23

> 詳細は [PORTFOLIO.md](PORTFOLIO.md) を参照。

## コンセプト

> **作るためのLLM（Claude Code）× 動かすためのPython**

各システムは Claude Code が Python コードを生成・修正し、完成後は LLM なしで動作する。
顧客ごとのカスタマイズ・保守更新には再びエージェントが活躍する。

## ディレクトリ構造

```
dx-portfolio/
├── README.md          このファイル
├── PORTFOLIO.md       全システム状態ダッシュボード
├── ROADMAP.md         優先度付きユースケース一覧
├── _template/         新システム作成時の雛形
├── _common/           全システム共通ライブラリ
├── 01_retail/         小売業
├── 02_manufacturing/  製造業
├── 03_healthcare/     医療・介護
├── 04_finance/        金融・保険
├── 05_logistics/      物流・倉庫
├── 06_restaurant/     飲食業
├── 07_realestate/     不動産
├── 08_hr/             人事・採用（業種横断）
├── 09_education/      教育・研修
└── 10_service/        サービス業・その他
```

## 新システムの追加手順

```
1. _template/ を対象フォルダにコピー
   例: cp -r _template/ 02_manufacturing/01_quality_inspection/

2. STATUS.md を編集（name / industry / status: idea）

3. Claude Code で「クレンジングして」と伝えると
   cleaner エージェントが cleanse.py を生成

4. 完成したら STATUS.md を production-ready に更新

5. PORTFOLIO.md のダッシュボードを更新
```

## 各システムの共通構造

```
{system}/
├── .claude/agents/     エージェント定義（cleaner / validator / reporter）
├── output/             生成スクリプト群
├── tests/              pytest テスト
├── app.py              Streamlit Webアプリ
├── run_pipeline.py     CLIパイプライン実行
├── config.yml          設定（店舗数・列名等、変更不要箇所）
├── requirements.txt
└── STATUS.md           このシステムの現在状態
```

## システム状態の定義

| アイコン | 状態 | 意味 |
|---------|------|------|
| 💡 | Idea | ユースケース候補として登録済み |
| 📐 | Designing | 設計中・要件整理中 |
| 🔧 | PoC | 試作中・動作確認中 |
| 🧪 | Tested | テスト完了・品質確認済み |
| ✅ | Production-ready | 顧客に納品可能な状態 |
| 🚀 | Deployed | 実際の顧客環境で稼働中 |

## 優先度の考え方

```
高価値 × 低難易度 → 優先度A（すぐ作る）
高価値 × 高難易度 → 優先度B（計画的に）
低価値 × 低難易度 → 優先度C（余裕があれば）
低価値 × 高難易度 → 対象外
```

詳細は [ROADMAP.md](ROADMAP.md) を参照。
