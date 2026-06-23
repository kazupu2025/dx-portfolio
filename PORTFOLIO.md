# DX ポートフォリオ ダッシュボード

> 最終更新: 2026-06-23  |  総システム数: 107  |  Production-ready: 104

---

## 状態サマリー

| 状態 | 件数 |
|------|------|
| ✅ Production-ready | 104 |
| 💡 Idea | 3 |
| **合計** | **107** |

---

## 業種別 内訳

| 業種 | 件数 |
|------|------|
| 製造 | 40 |
| 製造業 | 10 |
| 小売 | 6 |
| 医療・介護 | 6 |
| 金融・保険 | 5 |
| 物流・倉庫 | 5 |
| 飲食 | 5 |
| 不動産 | 5 |
| 人事・採用 | 4 |
| サービス | 4 |
| 教育・研修 | 3 |
| IT・SaaS | 2 |
| 飲食・外食 | 1 |
| 建設・ゼネコン | 1 |
| ホテル・観光 | 1 |
| 農業・食品加工 | 1 |
| 自動車・整備業 | 1 |
| 教育 | 1 |
| 物流 | 1 |
| 建設 | 1 |
| 農業 | 1 |

---

## 難易度別 内訳（製造 C-74〜C-94）

| 難易度 | 件数 | 特徴 |
|--------|------|------|
| ★★★ | 20 | config 調整のみで転用可 |
| ★★☆ | 18 | 統計分析ロジック実装 |
| ★☆☆ | 5 | ML・CRUD・グラフ構造 |

---

## 全システム一覧

| ID | 業種 | システム名 | 難易度 | 優先度 | パス |
|----|------|-----------|--------|--------|------|
| A-01 | 小売 | 売上データ分析パイプライン |  | A | `01_retail/01_sales_analysis` |
| A-02 | 飲食 | 飲食×日次売上・廃棄ロス集計レポート |  | A | `06_restaurant/01_daily_sales` |
| A-03 | 物流・倉庫 | 在庫データクレンジング・欠品検知 |  | A | `05_logistics/01_inventory` |
| A-04 | 金融・保険 | 経費精算データ集計・月次レポート |  | A | `04_finance/01_expense` |
| A-05 | 人事・採用 | 勤怠データ集計・残業アラートレポート |  | A | `08_hr/01_attendance` |
| A-06 | 製造 | 品質検査データ異常値検出レポート |  | A | `02_manufacturing/01_quality_inspection` |
| A-07 | 医療・介護 | 患者来院データ・ピーク時間可視化 |  | A | `03_healthcare/01_patient_visit` |
| A-08 | 不動産 | 物件問い合わせ・成約率分析レポート |  | A | `07_realestate/01_inquiry` |
| B-09 | 製造 | 製造×設備稼働ログ異常予兆検知 |  | B | `02_manufacturing/02_equipment_log` |
| B-10 | 小売 | 発注最適化・需要予測パイプライン |  | B | `01_retail/02_ordering` |
| B-11 | 金融・保険 | 与信スコアリングデータ整備 |  | B | `04_finance/02_credit_scoring` |
| B-12 | 教育・研修 | 受講生成績・退学リスクスコア |  | B | `09_education/01_dropout_risk` |
| B-13 | 飲食 | 原価管理・食材ロス分析 |  | B | `06_restaurant/02_cost_management` |
| B-14 | 不動産 | 賃貸物件管理・空室率レポート |  | B | `07_realestate/02_rental_management` |
| B-15 | サービス | 問い合わせログ分類・対応時間分析 |  | B | `10_service/01_inquiry_log` |
| C-100 | 製造業 | 4M変更台帳 集計・変更種別推移レポート | ★★★ | A | `02_manufacturing/46_4m_change_ledger/` |
| C-101 | 製造業 | 出荷検査合否率・保留件数 週次レポート | ★★★ | A | `02_manufacturing/47_shipping_inspection/` |
| C-102 | 製造業 | 工程別不良コード頻度・月次トレンド | ★★★ | A | `02_manufacturing/48_defect_code_trend/` |
| C-103 | 製造業 | 検査員別 検査数・不良検出率・精度レポート | ★★★ | A | `02_manufacturing/49_inspector_accuracy/` |
| C-104 | 製造業 | なぜなぜ分析 原因カテゴリ別集計・再発率トレンド | ★★★ | A | `02_manufacturing/50_5why_recurrence/` |
| C-16 | 医療・介護 | シフト希望・配置分析パイプライン |  | C | `03_healthcare/02_shift_optimization` |
| C-17 | 物流・倉庫 | 配送コスト分析パイプライン |  | C | `05_logistics/02_delivery_cost` |
| C-18 | 製造 | 原価差異分析パイプライン |  | C | `02_manufacturing/03_cost_variance` |
| C-19 | 小売 | 月次収益・予実差異レポート |  | C | `01_retail/03_monthly_pnl` |
| C-20 | 飲食 | アルバイトシフト・人件費集計パイプライン |  | C | `06_restaurant/03_labor_cost` |
| C-21 | サービス | サービス別売上・原価分析パイプライン |  | C | `10_service/02_revenue_cost` |
| C-22 | 物流・倉庫 | ドライバー勤怠・拘束時間管理パイプライン |  | C | `05_logistics/03_driver_attendance` |
| C-23 | 不動産 | 不動産 管理費・修繕費コスト分析パイプライン |  | C | `07_realestate/03_maintenance_cost` |
| C-24 | 教育・研修 | 講師稼働・コマ数管理パイプライン |  | C | `09_education/02_instructor_workload` |
| C-25 | 製造 | 生産計画 vs 実績 差異分析パイプライン |  | C | `02_manufacturing/04_production_variance` |
| C-26 | 金融・保険 | 請求書突合・差異検出パイプライン |  | C | `04_finance/03_invoice_reconciliation` |
| C-27 | 小売 | 顧客購買履歴 RFM 分析パイプライン |  | C | `01_retail/04_rfm_analysis` |
| C-28 | 製造 | 原材料コスト変動レポートパイプライン |  | C | `02_manufacturing/05_material_cost` |
| C-29 | 医療・介護 | 薬品在庫管理・発注アラートパイプライン |  | C | `03_healthcare/03_medicine_inventory` |
| C-30 | 人事・採用 | 人件費推移・予実差異レポートパイプライン |  | C | `08_hr/02_labor_cost` |
| C-31 | 金融・保険 | 契約更新アラート・期限管理パイプライン |  | C | `04_finance/04_contract_renewal` |
| C-32 | 物流・倉庫 | 配送ルート効率化レポートパイプライン |  | C | `05_logistics/04_route_efficiency` |
| C-33 | 人事・採用 | 採用歩留まり率分析パイプライン |  | C | `08_hr/03_recruitment_funnel` |
| C-34 | 小売 | 返品・クレームデータ集計レポート |  | C | `01_retail/05_returns_claims` |
| C-35 | 製造 | 作業員別生産性レポート |  | C | `02_manufacturing/06_worker_productivity` |
| C-36 | サービス | 顧客満足度スコア集計・トレンド分析 |  | C | `10_service/03_customer_satisfaction` |
| C-37 | 医療・介護 | 来院スループット分析パイプライン |  | C | `03_healthcare/04_reception_throughput` |
| C-38 | 飲食 | 予約キャンセル集計・傾向分析パイプライン |  | C | `06_restaurant/03_reservation_cancel` |
| C-39 | 不動産 | 入居者対応履歴・クレーム集計パイプライン |  | C | `07_realestate/04_tenant_claims` |
| C-40 | 飲食・外食 | アルバイトシフト管理・人件費集計パイプライン |  | C | `06_restaurant/04_shift_labor` |
| C-41 | 人事・採用 | 採用チャネル別コスト分析パイプライン |  | C | `08_hr/04_recruitment_cost` |
| C-42 | 教育・研修 | 受講率・修了率レポートパイプライン |  | C | `09_education/03_completion_rate` |
| C-43 | 小売 | シフト充足率・人件費最適化レポート |  | C | `01_retail/06_shift_optimization` |
| C-44 | 物流・倉庫 | 荷役作業員KPI集計パイプライン |  | C | `11_logistics/01_worker_kpi` |
| C-45 | サービス | サービス別売上・原価レポートパイプライン |  | C | `10_service/04_service_revenue` |
| C-46 | 建設・ゼネコン | 工程進捗・作業員稼働KPI集計パイプライン |  | C | `12_construction/01_progress_kpi` |
| C-47 | ホテル・観光 | 宿泊予約・稼働率分析パイプライン |  | C | `13_hotel/01_occupancy_rate` |
| C-48 | IT・SaaS | サブスクリプション解約率（チャーン）分析パイプライン |  | C | `14_it_saas/01_churn_analysis` |
| C-49 | 農業・食品加工 | 作物収量・品質検査レポートパイプライン |  | C | `15_agriculture/01_yield_quality` |
| C-50 | 自動車・整備業 | 車両整備依頼・完了率分析パイプライン |  | C | `16_automotive/01_repair_analysis` |
| C-51 | 医療・介護 | 診療報酬・請求分析パイプライン |  | C | `03_healthcare/05_billing_analysis` |
| C-52 | 金融・保険 | 保険問い合わせ・対応履歴分析パイプライン |  | C | `04_finance/04_inquiry_analysis` |
| C-53 | 不動産 | 物件内見予約・成約率分析パイプライン |  | C | `07_realestate/05_viewing_conversion` |
| C-54 | 飲食 | 店舗別損益・原価率管理パイプライン |  | C | `06_restaurant/05_pl_management` |
| C-55 | 教育 | 生徒入学申込・入学率分析パイプライン |  | C | `15_education/02_enrollment_analysis` |
| C-56 | 物流 | 配送コスト・利益率管理パイプライン |  | C | `09_logistics/05_cost_margin` |
| C-57 | 医療・介護 | 医療スタッフ勤怠・稼働率分析パイプライン |  | C | `03_healthcare/06_staff_attendance` |
| C-58 | 建設 | 工事原価・予算実績管理パイプライン |  | C | `11_construction/05_cost_budget` |
| C-59 | 農業 | 農場スタッフ勤怠・作業効率分析パイプライン |  | C | `12_agriculture/02_staff_efficiency` |
| C-60 | IT・SaaS | CSチケット分析パイプライン |  | C | `14_it_saas/02_support_ticket` |
| C-61 | 製造 | 製造業品質管理ポータル（統合） |  | C | `02_manufacturing/07_quality_portal` |
| C-62 | 製造 | 工程能力指数（Cp/Cpk）分析システム | ★★☆ | B | `02_manufacturing/08_cp_cpk` |
| C-63 | 製造 | 統合品質ダッシュボード（横断KPI） | ★★☆ | B | `02_manufacturing/09_unified_dashboard` |
| C-64 | 製造 | SPC管理図（X-bar/R + 異常8ルール） | ★★☆ | B | `02_manufacturing/10_spc_chart` |
| C-65 | 製造 | ゲージR&R（MSA）— 2要因ANOVA 測定システム分析 | ★★☆ | B | `02_manufacturing/11_gauge_rr` |
| C-66 | 製造 | 4M変更前後品質比較 — 変化点有意差検定（t検定/Mann-Whitney） | ★★☆ | B | `02_manufacturing/12_4m_change` |
| C-67 | 製造 | 工程間品質相関分析 — Pearson 相関行列 × ヒートマップ | ★★☆ | B | `02_manufacturing/15_process_correlation` |
| C-68 | 製造 | 仕入先品質複合スコアリング — 重み付き合成スコア × 仕入先ランク | ★★☆ | B | `02_manufacturing/17_supplier_scoring` |
| C-69 | 製造 | 不良モード別パレート × 時系列複合分析 | ★★☆ | B | `02_manufacturing/13_defect_pareto` |
| C-70 | 製造 | 是正処置（8D）効果検証 — 統計的有意差検定（t検定/Mann-Whitney） | ★★☆ | B | `02_manufacturing/14_corrective_action` |
| C-71 | 製造 | 品質コストROI分析 — PAFモデル × 月次改善効果測定 | ★★☆ | B | `02_manufacturing/16_quality_cost_roi` |
| C-72 | 製造 | AQL/受入サンプリング計画最適化 — OC曲線・抜取方式設計 | ★★☆ | B | `02_manufacturing/18_aql_sampling` |
| C-73 | 製造 | 協力会社別受入不良率月報 | ★★★ | B | `02_manufacturing/19_supplier_defect_rate` |
| C-74 | 製造 | 顧客クレーム件数・原因分類 月次集計 | ★★★ | A | `02_manufacturing/20_customer_claim_monthly` |
| C-75 | 製造 | 品質コスト明細集計（4分類） | ★★★ | A | `02_manufacturing/21_quality_cost` |
| C-76 | 製造 | CAPA完了率・期限遵守率レポート | ★★★ | A | `02_manufacturing/22_capa_report` |
| C-77 | 製造 | 特採件数・理由別集計・月次推移 | ★★★ | A | `02_manufacturing/23_tokusai_monthly` |
| C-78 | 製造 | 4M変更台帳 集計・変更種別推移 | ★★★ | A | `02_manufacturing/24_4m_change` |
| C-79 | 製造 | 出荷検査合否率・保留件数レポート | ★★★ | A | `02_manufacturing/25_shipping_inspection` |
| C-80 | 製造 | 工程別不良コード頻度・月次トレンド | ★★★ | A | `02_manufacturing/26_process_defect` |
| C-81 | 製造 | 検査員別 検査数・不良検出率・精度レポート | ★★★ | A | `02_manufacturing/27_inspector_performance` |
| C-82 | 製造 | なぜなぜ分析 原因カテゴリ別集計・再発率トレンド | ★★★ | A | `02_manufacturing/28_5why_analysis` |
| C-83 | 製造 | 4M変更前後品質比較（t検定/Mann-Whitney） | ★★☆ | A | `02_manufacturing/29_4m_change_comparison` |
| C-84 | 製造 | 工程間品質相関分析（前工程パラメータ × 後工程不良率） | ★★☆ | A | `02_manufacturing/30_process_correlation` |
| C-85 | 製造 | 仕入先品質複合スコアリング（受入不良率 × Cpk × クレーム件数） | ★★☆ | A | `02_manufacturing/31_supplier_scoring` |
| C-86 | 製造 | 不良モード別パレート × 時系列複合分析 | ★★☆ | A | `02_manufacturing/32_defect_pareto` |
| C-87 | 製造 | 是正処置（8D）効果検証 — 統計的有意差検定 | ★★☆ | A | `02_manufacturing/33_8d_effectiveness` |
| C-88 | 製造 | 品質コストROI分析（予防投資額 vs 失敗コスト削減額） | ★★☆ | A | `02_manufacturing/34_quality_roi` |
| C-89 | 製造 | AQL/受入サンプリング計画最適化（OC曲線） | ★★☆ | A | `02_manufacturing/35_aql_sampling` |
| C-90 | 製造 | 品質予測モデル（工程パラメータ → 合否予測） | ★☆☆ | A | `02_manufacturing/36_quality_prediction` |
| C-91 | 製造 | FMEA RPN動的更新システム | ★☆☆ | A | `02_manufacturing/37_fmea_rpn` |
| C-92 | 製造 | LLM不良原因自動分類 | ★☆☆ | A | `02_manufacturing/38_defect_classifier` |
| C-93 | 製造 | サプライヤー品質認定・改善追跡システム | ★☆☆ | A | `02_manufacturing/39_supplier_certification` |
| C-94 | 製造 | ロット完全トレーサビリティ | ★☆☆ | A | `02_manufacturing/40_lot_traceability` |
| C-95 | 製造業 | 協力会社別受入不良率月報 | ★★★ | A | `02_manufacturing/41_incoming_defect_rate/` |
| C-96 | 製造業 | 顧客クレーム件数・原因分類 月次集計 | ★★★ | A | `02_manufacturing/42_customer_claims/` |
| C-97 | 製造業 | 品質コスト明細集計（予防/評価/内部失敗/外部失敗） | ★★★ | A | `02_manufacturing/43_quality_cost_detail/` |
| C-98 | 製造業 | CAPA完了率・期限遵守率レポート | ★★★ | A | `02_manufacturing/44_capa_management/` |
| C-99 | 製造業 | 特採件数・理由別集計・月次推移 | ★★★ | A | `02_manufacturing/45_special_acceptance/` |

---

## 💡 Idea（未着手）

| 業種 | システム名 |
|------|-----------|
| 飲食 | アルバイトシフト管理・人件費集計 |
| 人事・採用 | 研修効果測定レポート |
| 教育・研修 | 出席率・成績推移レポート |
