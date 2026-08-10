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
    ("A-02", "06_restaurant/01_daily_sales/app.py",           "demo_restaurant",  "[A-02] 飲食売上管理・P/L集計"),
    ("A-06", "02_manufacturing/01_quality_inspection/app.py", "demo_quality",     "[A-06] 品質検査異常値検出"),
    ("A-07", "03_healthcare/01_patient_visit/app.py",         "demo_healthcare",  "[A-07] 患者訪問・ピーク時間解析"),
    ("A-04", "04_finance/01_expense/app.py",                  "demo_finance",     "[A-04] 出張費集計・比較レポート"),
    ("A-03", "05_logistics/01_inventory/app.py",              "demo_logistics",   "[A-03] 在庫データ鮮度確認"),
    ("A-08", "07_realestate/01_inquiry/app.py",               "demo_realestate",  "[A-08] 問い合わせ・反響率分析"),
    ("A-05", "08_hr/01_attendance/app.py",                    "demo_hr",          "[A-05] 勤怠データ・ツールアラート"),
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


# ── ナビゲーション ────────────────────────────────────────────
_catalog_page = st.Page(_show_catalog, title="📊 ツールカタログ", url_path="catalog", default=True)

pg = st.navigation(
    [_catalog_page] + list(_demo_pages.values()),
    position="sidebar",
)
pg.run()
