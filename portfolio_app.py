"""DX ポートフォリオ カタログ — 顧客向けシステム一覧。"""

import yaml
import streamlit as st
from pathlib import Path

# ── ページ設定（メインスクリプトでのみ有効） ────────────────────
st.set_page_config(
    page_title="DX ポートフォリオ | 業務改善システムストック集",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 定数 ────────────────────────────────────────────────────
_GITHUB_BASE = "https://github.com/kazupu2025/dx-portfolio/tree/main"

_INDUSTRY_COLOR = {
    "製造": "#1e3a5f",
    "小売": "#16a34a",
    "医療・介護": "#7c3aed",
    "金融・保険": "#d97706",
    "物流・倉庫": "#0891b2",
    "飲食": "#dc2626",
    "不動産": "#be185d",
    "人事・採用": "#065f46",
    "サービス": "#92400e",
    "教育・研修": "#1d4ed8",
    "IT・SaaS": "#6366f1",
    "建設・ゼネコン": "#78716c",
    "ホテル・観光": "#0e7490",
    "農業・食品加工": "#4d7c0f",
    "自動車・整備業": "#b45309",
}
_DEFAULT_COLOR = "#64748b"

_DIFF_COLOR = {
    "★★★": "#16a34a",
    "★★☆": "#d97706",
    "★☆☆": "#dc2626",
}

# ── デモページ定義（priority-A の実装済みツール）────────────────
# (tool_id, app_path, url_path, page_title)
_A_TOOL_DEFS = [
    ("A-01", "01_retail/01_sales_analysis/app.py",            "demo_retail",      "[A-01] 小売売上データ分析パイプライン"),
    ("A-02", "06_restaurant/01_daily_sales/app.py",           "demo_restaurant",  "[A-02] 飲食売上管理・P/L集計"),
    ("A-06", "02_manufacturing/01_quality_inspection/app.py", "demo_quality",     "[A-06] 品質検査異常値検出"),
    ("A-07", "03_healthcare/01_patient_visit/app.py",         "demo_healthcare",  "[A-07] 患者訪問・ピーク時間解析"),
    ("A-04", "04_finance/01_expense/app.py",                  "demo_finance",     "[A-04] 出張費集計・比較レポート"),
    ("A-03", "05_logistics/01_inventory/app.py",              "demo_logistics",   "[A-03] 在庫データ鮮度確認"),
    ("A-08", "07_realestate/01_inquiry/app.py",               "demo_realestate",  "[A-08] 問い合わせ・反響率分析"),
    ("A-05", "08_hr/01_attendance/app.py",                    "demo_hr",          "[A-05] 勤怠データ・ツールアラート"),
    ("C-110", "06_restaurant/03_shift_cost/app.py", "demo_shift_cost", "[C-110] シフト管理・人件費集計"),
    ("C-111", "08_hr/02_training_effectiveness/app.py", "demo_training", "[C-111] 研修効果測定レポート"),
    ("C-112", "09_education/02_attendance_grade/app.py", "demo_attendance", "[C-112] 出席率・成績推移"),
    ("C-113", "10_service/02_saas_metrics/app.py", "demo_saas", "[C-113] SaaSメトリクス（MRR/チャーン）"),
    ("C-115", "hotel/01_revpar/app.py", "demo_hotel", "[C-115] RevPAR・客室稼働率"),
    ("C-116", "construction/01_progress_cost/app.py", "demo_construction", "[C-116] 工程進捗・原価差異"),
    ("C-117", "agriculture/01_harvest_quality/app.py", "demo_agriculture", "[C-117] 収穫量・品質トレンド"),
    ("C-118", "automotive/01_service_inventory/app.py", "demo_automotive", "[C-118] 整備案件・部品在庫"),
    ("C-121", "construction/02_safety_hazard/app.py", "demo_safety", "[C-121] 安全管理・ヒヤリハット"),
    ("C-125", "automotive/02_inspection_reminder/app.py", "demo_inspection", "[C-125] 車検リマインダー管理"),
    ("C-97", "02_manufacturing/43_quality_cost_detail/app.py", "demo_quality_cost", "[C-97] 品質コスト明細（4分類）"),
    ("C-74", "02_manufacturing/20_customer_claim_monthly/app.py", "demo_claim_monthly", "[C-74] 顧客クレーム件数・月次集計"),
    ("C-75", "02_manufacturing/21_quality_cost/app.py", "demo_qual_cost", "[C-75] 品質コスト明細集計"),
    ("C-76", "02_manufacturing/22_capa_report/app.py", "demo_capa", "[C-76] CAPA完了率・期限遵守率"),
    ("C-77", "02_manufacturing/23_tokusai_monthly/app.py", "demo_tokusai", "[C-77] 特採件数・理由別集計"),
    ("C-95", "02_manufacturing/41_incoming_defect_rate/app.py", "demo_incoming", "[C-95] 協力会社別受入不良率"),
    ("C-96", "02_manufacturing/42_customer_claims/app.py", "demo_claims", "[C-96] 顧客クレーム月次集計"),
    ("C-98", "02_manufacturing/44_capa_management/app.py", "demo_capa_mgmt", "[C-98] CAPA管理・期限遵守"),
    ("C-99", "02_manufacturing/45_special_acceptance/app.py", "demo_special", "[C-99] 特採件数・月次推移"),
    ("C-100", "02_manufacturing/46_4m_change_ledger/app.py", "demo_4m_ledger", "[C-100] 4M変更台帳・推移"),
    ("C-101", "02_manufacturing/47_shipping_inspection/app.py", "demo_shipping", "[C-101] 出荷検査合否率"),
    ("C-102", "02_manufacturing/48_defect_code_trend/app.py", "demo_defect_trend", "[C-102] 工程別不良コードトレンド"),
    ("C-103", "02_manufacturing/49_inspector_accuracy/app.py", "demo_inspector", "[C-103] 検査員別精度レポート"),
    ("C-104", "02_manufacturing/50_5why_recurrence/app.py", "demo_5why", "[C-104] なぜなぜ分析・再発率"),
    ("C-106", "02_manufacturing/52_quality_feedback_loop/app.py", "demo_feedback", "[C-106] 市場品質フィードバック"),
    ("C-109", "02_manufacturing/55_multisite_quality/app.py", "demo_multisite", "[C-109] 多拠点品質比較"),
    ("C-114", "10_service/03_customer_success/app.py", "demo_cs", "[C-114] カスタマーサクセス指標"),
    ("B-13", "06_restaurant/02_cost_management/app.py",   "demo_cost_mgmt",  "[B-13] 飲食原価・食材ロス管理"),
    ("B-14", "07_realestate/02_rental_management/app.py", "demo_rental",     "[B-14] 賃貸物件管理・空室率"),
    ("B-09", "02_manufacturing/02_equipment_log/app.py",  "demo_equipment",  "[B-09] 設備稼働ログ異常予兆検知"),
    ("B-10", "01_retail/02_ordering/app.py",              "demo_ordering",   "[B-10] 発注最適化・需要予測"),
    ("B-11", "04_finance/02_credit_scoring/app.py",       "demo_credit",     "[B-11] 与信スコアリング管理"),
    ("B-12", "09_education/01_dropout_risk/app.py",       "demo_dropout",    "[B-12] 退学リスク早期警戒"),
    ("B-15", "10_service/01_inquiry_log/app.py",          "demo_inquiry_log","[B-15] 問い合わせログ分類・対応時間"),
    ("B-16", "03_healthcare/02_shift_optimization/app.py","demo_shift_opt",  "[B-16] 医療・介護 シフト希望・夜勤分析"),
    ("B-17", "05_logistics/02_delivery_cost/app.py",      "demo_delivery",   "[B-17] 物流 配送コスト・ルート効率分析"),
    ("B-18", "03_healthcare/03_medicine_inventory/app.py","demo_medicine",   "[B-18] 医療 薬品在庫管理・発注アラート"),
    ("B-19", "04_finance/03_invoice_reconciliation/app.py","demo_invoice",   "[B-19] 金融 請求書突合・差異検出"),
    ("B-20", "08_hr/03_recruitment_funnel/app.py",         "demo_recruit",   "[B-20] 人事 採用ファネル・歩留まり分析"),
    ("B-21", "07_realestate/03_maintenance_cost/app.py",   "demo_maint",     "[B-21] 不動産 管理費・修繕費分析"),
    ("B-22", "06_restaurant/05_pl_management/app.py",      "demo_pl_mgmt",   "[B-22] 飲食 店舗別損益・P/L管理"),
    ("B-23", "05_logistics/03_driver_attendance/app.py",   "demo_driver",    "[B-23] 物流 ドライバー勤怠・拘束時間管理"),
    ("B-24", "08_hr/02_labor_cost/app.py",                 "demo_labor",     "[B-24] 人事 人件費予実・超過部門アラート"),
    ("B-25", "09_education/03_completion_rate/app.py",     "demo_completion","[B-25] 教育 受講・修了率ダッシュボード"),
    ("B-26", "01_retail/03_monthly_pnl/app.py",            "demo_monthly_pnl","[B-26] 小売 月次収益・P/L管理"),
    ("B-27", "03_healthcare/04_reception_throughput/app.py","demo_reception", "[B-27] 医療 来院スループット・待ち時間管理"),
    ("B-28", "04_finance/04_contract_renewal/app.py",       "demo_contract",  "[B-28] 金融 契約更新アラート・期限管理"),
    ("B-29", "05_logistics/04_route_efficiency/app.py",    "demo_route",     "[B-29] 物流 配送ルート効率化・遅延分析"),
    ("B-30", "07_realestate/04_tenant_claims/app.py",      "demo_tenant",    "[B-30] 不動産 入居者クレーム管理"),
    ("B-31", "08_hr/04_recruitment_cost/app.py",           "demo_recruit_cost","[B-31] 人事 採用コスト・チャネル別ROI"),
    ("B-32", "01_retail/04_rfm_analysis/app.py",           "demo_rfm",         "[B-32] 小売 顧客RFM分析・セグメント"),
    ("B-33", "06_restaurant/03_reservation_cancel/app.py", "demo_reservation",  "[B-33] 飲食 予約キャンセル管理"),
    ("B-34", "09_education/02_instructor_workload/app.py", "demo_instructor",   "[B-34] 教育 講師稼働・負荷管理"),
    ("B-35", "06_restaurant/02_cost_management/app.py",   "demo_b35_cost",     "[B-35] 飲食 原価・食材ロス管理"),
    ("B-36", "05_logistics/02_delivery_cost/app.py",      "demo_delivery_cost","[B-36] 物流 配送コスト・ルート効率"),
    ("B-37", "07_realestate/02_rental_management/app.py", "demo_rental_mgmt",  "[B-37] 不動産 賃貸管理・空室率"),
    ("B-38", "08_hr/03_recruitment_funnel/app.py",        "demo_rec_funnel",   "[B-38] 人事 採用ファネル・歩留まり分析"),
    ("B-39", "03_healthcare/03_medicine_inventory/app.py","demo_b39_medicine", "[B-39] 医療 薬品在庫・発注アラート"),
    ("B-40", "10_service/01_inquiry_log/app.py",          "demo_inquiry",      "[B-40] サービス 問い合わせログ分析"),
    ("B-41", "04_finance/03_invoice_reconciliation/app.py","demo_invoice_rec",  "[B-41] 金融 請求書突合・差異検出"),
    ("B-42", "07_realestate/03_maintenance_cost/app.py",  "demo_maint_cost",   "[B-42] 不動産 管理費・修繕費分析"),
    ("B-43", "10_service/03_customer_satisfaction/app.py","demo_csat",         "[B-43] サービス 顧客満足度分析"),
    ("B-44", "01_retail/05_returns_claims/app.py",        "demo_returns",      "[B-44] 小売 返品・クレーム管理"),
    ("B-45", "03_healthcare/05_billing_analysis/app.py",  "demo_billing",      "[B-45] 医療 診療報酬・請求分析"),
    ("B-46", "04_finance/04_inquiry_analysis/app.py",     "demo_fin_inquiry",  "[B-46] 金融 問い合わせ・対応履歴分析"),
    ("B-47", "07_realestate/05_viewing_conversion/app.py","demo_viewing",      "[B-47] 不動産 内見・成約率分析"),
    ("B-48", "14_it_saas/01_churn_analysis/app.py",       "demo_churn",        "[B-48] IT・SaaS チャーン分析"),
    ("B-49", "06_restaurant/03_labor_cost/app.py",        "demo_labor_cost",   "[B-49] 飲食 シフト・人件費管理"),
    ("B-50", "03_healthcare/06_staff_attendance/app.py", "demo_staff_attend",  "[B-50] 医療 スタッフ勤怠・稼働率分析"),
    ("B-51", "14_it_saas/02_support_ticket/app.py",      "demo_support_tick",  "[B-51] IT・SaaS CSチケット分析"),
    ("B-52", "09_logistics/05_cost_margin/app.py",       "demo_log_cost_mgn",  "[B-52] 物流 配送コスト・利益率管理"),
    ("B-53", "13_hotel/01_occupancy_rate/app.py",        "demo_hotel_occ",     "[B-53] ホテル 稼働率・RevPAR分析"),
    ("B-54", "10_service/04_service_revenue/app.py",     "demo_svc_revenue",   "[B-54] サービス 売上・原価レポート"),
    ("B-55", "12_construction/01_progress_kpi/app.py",   "demo_const_prog",    "[B-55] 建設 工程進捗・稼働KPI"),
    ("B-56", "06_restaurant/04_shift_labor/app.py",      "demo_shift_labor",   "[B-56] 飲食 シフト・人件費管理"),
    ("B-57", "16_automotive/01_repair_analysis/app.py",  "demo_repair",        "[B-57] 自動車 整備依頼・完了率分析"),
    ("B-58", "15_education/02_enrollment_analysis/app.py","demo_enrollment",   "[B-58] 教育 入学申込・合格率分析"),
    ("B-59", "hotel/01_revpar/app.py",                   "demo_hotel_revpar",  "[B-59] ホテル RevPAR・客室稼働率"),
    ("B-60", "hotel/02_banquet_revenue/app.py",          "demo_hotel_banquet", "[B-60] ホテル 宴会・イベント収益"),
    ("B-61", "hotel/03_guest_satisfaction/app.py",       "demo_hotel_guest",   "[B-61] ホテル 顧客満足度分析"),
]

_demo_pages = {
    aid: st.Page(path, title=title, url_path=url_path)
    for aid, path, url_path, title in _A_TOOL_DEFS
}


# ── データ読み込み ────────────────────────────────────────────
@st.cache_data
def load_catalog():
    path = Path(__file__).parent / "catalog.yml"
    with open(path, encoding="utf-8") as f:
        items = yaml.safe_load(f)
    return [i for i in items if i.get("status") == "production-ready"]


# ── フィルタリング ────────────────────────────────────────────
def filter_items(items, industries, difficulties, priorities, keyword):
    result = items
    if industries:
        result = [i for i in result if i.get("industry") in industries]
    if difficulties:
        result = [i for i in result if i.get("difficulty") in difficulties]
    if priorities:
        result = [i for i in result if i.get("priority") in priorities]
    if keyword:
        kw = keyword.lower()
        result = [
            i for i in result
            if kw in (i.get("name", "")).lower()
            or kw in (i.get("description", "")).lower()
            or kw in (i.get("department", "")).lower()
            or kw in (i.get("industry", "")).lower()
        ]
    return result


# ── カード描画 ────────────────────────────────────────────────
def render_card(item):
    iid    = item.get("id", "")
    name   = item.get("name", "")
    ind    = item.get("industry", "")
    dept   = item.get("department", "")
    diff   = item.get("difficulty", "")
    pri    = item.get("priority", "")
    path   = item.get("path", "")
    desc   = item.get("description", "").strip().replace("\n", " ")
    demo   = item.get("demo", "")
    gh_url = f"{_GITHUB_BASE}/{path}" if path else ""

    desc_short = desc[:100] + "..." if len(desc) > 100 else desc

    ind_color  = _INDUSTRY_COLOR.get(ind, _DEFAULT_COLOR)
    diff_color = _DIFF_COLOR.get(diff, "#94a3b8")
    diff_html  = (
        f'<span style="background:{diff_color}22;color:{diff_color};'
        f'padding:2px 8px;border-radius:12px;font-size:12px">{diff}</span>'
        if diff else ""
    )

    # 優先度バッジ（white-space:nowrap で折り返し防止）
    if pri == "A":
        pri_badge = '<span style="background:#fef2f2;color:#dc2626;padding:1px 6px;border-radius:8px;font-size:11px;font-weight:bold;white-space:nowrap">優先度A</span>'
    elif pri == "B":
        pri_badge = '<span style="background:#fffbeb;color:#d97706;padding:1px 6px;border-radius:8px;font-size:11px;font-weight:bold;white-space:nowrap">優先度B</span>'
    else:
        pri_badge = f'<span style="background:#f8fafc;color:#64748b;padding:1px 6px;border-radius:8px;font-size:11px;white-space:nowrap">優先度{pri}</span>'

    # パスは先頭16文字に切り詰め（長いパスがバッジを押しつぶすのを防ぐ）
    path_short = path if len(path) <= 22 else path[:19] + "…"

    # st.container(border=True) でカード本体とアクションを1ブロックに統合
    with st.container(border=True):
        st.markdown(f"""
<div style="padding:4px 4px 8px 4px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
    <span style="background:{ind_color};color:white;padding:2px 8px;border-radius:12px;
                 font-size:11px;font-weight:bold;white-space:nowrap">{ind}</span>
    {diff_html}
  </div>
  <div style="font-size:11px;color:#64748b;margin-bottom:2px">{iid} · {dept}</div>
  <div style="font-size:15px;font-weight:bold;color:#1e293b;margin-bottom:8px">{name}</div>
  <div style="font-size:12px;color:#64748b;margin-bottom:12px;line-height:1.5">{desc_short}</div>
  <div style="font-size:11px;color:#94a3b8;border-top:1px solid #f1f5f9;padding-top:8px;
              display:flex;align-items:center;gap:6px;overflow:hidden">
    {pri_badge}
    <code style="font-size:10px;background:#f8fafc;padding:1px 4px;border-radius:3px;
                 color:#94a3b8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                 min-width:0">📁 {path_short}</code>
  </div>
</div>
""", unsafe_allow_html=True)

        # ── カスタマイズポイント（設定した場合のみ表示）────────
        customize_points = item.get("customize_points", [])
        if customize_points:
            with st.expander("⚙️ カスタマイズポイント", expanded=False):
                for pt in customize_points:
                    st.markdown(f"- {pt}")

        if iid in _demo_pages:
            # インタラクティブデモが使えるツール → デモボタン（全幅）+ コードリンク（全幅）
            # ※ネストされたst.columns()は3列グリッド内で幅が足りなくなるため縦積みにする
            st.page_link(_demo_pages[iid], label="🚀 デモを起動", use_container_width=True)
            if gh_url:
                st.link_button("📂 コードを見る →", gh_url, use_container_width=True)
        elif demo:
            # デモページ未作成のツール → 起動コマンド + GitHubリンク
            with st.expander("起動コマンド", expanded=False):
                st.code(demo, language="bash")
            if gh_url:
                st.link_button("📂 コードを見る →", gh_url, use_container_width=True)
        elif gh_url:
            st.link_button("📂 コードを見る →", gh_url, use_container_width=True)


# ── カタログページ本体 ────────────────────────────────────────
def _show_catalog():
    # グローバルCSS：ExpanderヘッダーとLinkButtonの折り返し防止
    st.markdown("""
<style>
/* Expander ヘッダーのラベルを1行に固定 */
[data-testid="stExpanderToggleIcon"] ~ div p,
details > summary p,
.streamlit-expanderHeader p {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
/* st.link_button / st.page_link の折り返し防止 */
[data-testid="stLinkButton"] p,
[data-testid="stPageLink"] p {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
</style>
""", unsafe_allow_html=True)

    # ヘッダーバー
    st.markdown("""
<div style="background:#1e3a5f;padding:20px 32px;border-radius:8px;margin-bottom:24px">
  <h1 style="color:white;margin:0;font-size:28px">📊 DX ポートフォリオ</h1>
  <p style="color:#93c5fd;margin:4px 0 0 0;font-size:15px">
    業務改善コンサルタント向け DX システムストック集
  </p>
</div>
""", unsafe_allow_html=True)

    # データ読み込み
    all_items = load_catalog()

    # ── KPI 4カード ───────────────────────────────────────────
    unique_industries = sorted({i.get("industry", "") for i in all_items if i.get("industry")})
    priority_a_count  = sum(1 for i in all_items if i.get("priority") == "A")
    ready_count       = len(all_items)
    demo_count        = len(_demo_pages)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("総システム数", f"{ready_count} 件")
    with k2:
        st.metric("対応業種数", f"{len(unique_industries)} 業種")
    with k3:
        st.metric("最高優先度 (A)", f"{priority_a_count} 件")
    with k4:
        st.metric("🚀 デモ体験可能", f"{demo_count} 件")

    st.markdown("---")

    # ── サイドバー（フィルター） ──────────────────────────────
    st.sidebar.header("🔍 フィルター")

    sel_industries = st.sidebar.multiselect(
        "業種",
        options=unique_industries,
        default=[],
    )

    unique_difficulties = [d for d in ["★★★", "★★☆", "★☆☆"]
                           if any(i.get("difficulty") == d for i in all_items)]
    sel_difficulties = st.sidebar.multiselect(
        "難易度（転用しやすさ）",
        options=unique_difficulties,
        default=[],
    )

    unique_priorities = sorted({i.get("priority", "") for i in all_items if i.get("priority") and i.get("priority") != "null"})
    sel_priorities = st.sidebar.multiselect(
        "優先度",
        options=unique_priorities,
        default=[],
    )

    keyword = st.sidebar.text_input(
        "キーワード検索",
        placeholder="例: 異常検知、在庫、FMEA...",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
**難易度の見方**
- ★★★ 転用しやすい
- ★★☆ 設計変更が必要
- ★☆☆ アーキテクチャから再設計

**🚀 デモ起動可能** = ブラウザ上でツールを体験できます
""")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗺️ 導入フロー")
    st.sidebar.markdown("""
**Step 1 🔍 ツールを探す**
業種・難易度・優先度でフィルタリング

**Step 2 🚀 デモで確認**
優先度Aのツールはブラウザ上で体験可能

**Step 3 📂 コードを取得**
「コードを見る →」からGitHubへアクセス
```
git clone https://github.com/kazupu2025/dx-portfolio.git
cd dx-portfolio/<ツールのpath>
```

**Step 4 ⚙️ カスタマイズ**
`config.yml` の閾値・列名・会社名を調整
CSVのカラム名をクライアント環境に合わせる

**Step 5 🚢 納品・デプロイ**
Streamlit Cloud / 社内サーバーへ展開
""")

    # ── フィルタリング ────────────────────────────────────────
    filtered = filter_items(all_items, sel_industries, sel_difficulties, sel_priorities, keyword)

    # 検索結果サマリー
    st.markdown(
        f'<div style="font-size:13px;color:#64748b;margin-bottom:16px">'
        f'<b>{len(filtered)}</b> 件ヒット（全 {len(all_items)} 件中）</div>',
        unsafe_allow_html=True,
    )

    # ── カード グリッド（3列） ────────────────────────────────
    if filtered:
        cols = st.columns(3)
        for idx, item in enumerate(filtered):
            with cols[idx % 3]:
                render_card(item)
    else:
        st.info("条件に一致するシステムが見つかりませんでした。フィルターを変更してください。")

    # ── テーブルビュー ────────────────────────────────────────
    import pandas as pd

    with st.expander("📋 一覧表示（テーブル形式）"):
        if filtered:
            df = pd.DataFrame(filtered)
            # YAML null → Python None → "None" 文字列を空欄に置換
            for col in ["difficulty", "department"]:
                if col in df.columns:
                    df[col] = df[col].where(df[col].notna(), "").replace("None", "")
            display_cols = [c for c in ["id", "name", "industry", "department", "difficulty", "priority", "path"] if c in df.columns]
            st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("表示するデータがありません。")

    # ── フッター ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        """
        > Claude Code × Python で構築 | 🚀 優先度Aのツールはブラウザ上でデモ体験可能
        >
        > 導入・カスタマイズのご相談: [realpooh0927@gmail.com](mailto:realpooh0927@gmail.com)
        """
    )


# ── ナビゲーション（セクション別グループ化） ─────────────────────
# ツールID → 表示セクション のマッピング
_SECTION_MAP: dict[str, str] = {
    "A-01": "🏪 小売",
    "A-02": "🍜 飲食",
    "A-03": "📦 物流・倉庫",
    "A-04": "💰 金融・保険",
    "A-05": "👥 人事・採用",
    "A-06": "🏭 製造",
    "A-07": "🏥 医療・介護",
    "A-08": "🏢 不動産",
    "C-110": "🍜 飲食",
    "C-111": "👥 人事・採用",
    "C-112": "📚 教育・研修",
    "C-113": "💻 IT・SaaS",
    "C-114": "⚙️ サービス",
    "C-115": "🏨 ホテル・観光",
    "C-116": "🏗️ 建設・ゼネコン",
    "C-117": "🌾 農業・食品加工",
    "C-118": "🚗 自動車・整備業",
    "C-121": "🏗️ 建設・ゼネコン",
    "C-125": "🚗 自動車・整備業",
    "B-13": "🍜 飲食",
    "B-14": "🏢 不動産",
    "B-09": "🏭 製造",
    "B-10": "🏪 小売",
    "B-11": "💰 金融・保険",
    "B-12": "📚 教育・研修",
    "B-15": "⚙️ サービス",
    "B-16": "🏥 医療・介護",
    "B-17": "📦 物流・倉庫",
    "B-18": "🏥 医療・介護",
    "B-19": "💰 金融・保険",
    "B-20": "👥 人事・採用",
    "B-21": "🏢 不動産",
    "B-22": "🍜 飲食",
    "B-23": "📦 物流・倉庫",
    "B-24": "👥 人事・採用",
    "B-25": "📚 教育・研修",
    "B-26": "🏪 小売",
    "B-27": "🏥 医療・介護",
    "B-28": "💰 金融・保険",
    "B-29": "📦 物流・倉庫",
    "B-30": "🏢 不動産",
    "B-31": "👥 人事・採用",
    "B-32": "🏪 小売",
    "B-33": "🍜 飲食",
    "B-34": "📚 教育・研修",
    "B-35": "🍜 飲食",
    "B-36": "📦 物流・倉庫",
    "B-37": "🏢 不動産",
    "B-38": "👥 人事・採用",
    "B-39": "🏥 医療・介護",
    "B-40": "💼 サービス",
    "B-41": "💰 金融・保険",
    "B-42": "🏢 不動産",
    "B-43": "💼 サービス",
    "B-44": "🏪 小売",
    "B-45": "🏥 医療・介護",
    "B-46": "💰 金融・保険",
    "B-47": "🏢 不動産",
    "B-48": "💻 IT・SaaS",
    "B-49": "🍜 飲食",
    "B-50": "🏥 医療・介護",
    "B-51": "💻 IT・SaaS",
    "B-52": "📦 物流・倉庫",
    "B-53": "🏨 ホテル・観光",
    "B-54": "⚙️ サービス",
    "B-55": "🏗️ 建設・ゼネコン",
    "B-56": "🍜 飲食",
    "B-57": "🚗 自動車・整備業",
    "B-58": "📚 教育・研修",
    "B-59": "🏨 ホテル・観光",
    "B-60": "🏨 ホテル・観光",
    "B-61": "🏨 ホテル・観光",
}
# C-74〜C-109 は製造まとめ
for _tid in ["C-97", "C-74", "C-75", "C-76", "C-77", "C-95", "C-96",
             "C-98", "C-99", "C-100", "C-101", "C-102", "C-103",
             "C-104", "C-106", "C-109"]:
    _SECTION_MAP[_tid] = "🏭 製造"

# セクション別にページをグループ化（_A_TOOL_DEFS の順序を保持）
_section_pages: dict[str, list] = {}
for _aid, _, _, _ in _A_TOOL_DEFS:
    _sec = _SECTION_MAP.get(_aid, "📦 その他")
    _section_pages.setdefault(_sec, []).append(_demo_pages[_aid])

_catalog_page = st.Page(_show_catalog, title="📊 ツールカタログ", url_path="catalog", default=True)

# カタログをトップに置き、業種セクションを続ける
_nav_dict: dict[str, list] = {"📋 メニュー": [_catalog_page]}
_nav_dict.update(_section_pages)

pg = st.navigation(_nav_dict)
pg.run()
