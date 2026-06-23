import streamlit as st
import pandas as pd
from db import init_db, seed_db, get_all, get_by_id, create_item, advance_status, update_field, delete_item, STATUSES
from analyze import analyze
import datetime

st.set_page_config(page_title="CAPAワークフロー", layout="wide")
st.title("🏭 CAPAワークフロー管理")

# DB初期化
init_db()
seed_db()

# タブ作成
tab1, tab2, tab3 = st.tabs(["📋 一覧・分析", "➕ 新規起票", "✏️ 詳細更新"])

# タブ1: 一覧・分析
with tab1:
    st.subheader("分析ダッシュボード")

    # KPIカード
    analysis = analyze()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("総件数", analysis["total"])

    with col2:
        st.metric("完了件数", analysis["completed"])

    with col3:
        st.metric("完了率", f"{analysis['completion_rate']:.1f}%")

    with col4:
        verdict_icon = "🟢" if analysis["verdict"] == "good" else ("🟡" if analysis["verdict"] == "warning" else "🔴")
        st.metric("判定", verdict_icon)

    # 超過件数表示
    if analysis["overdue_count"] > 0:
        st.warning(f"⚠️ 期限超過件数: **{analysis['overdue_count']}件**")

    st.divider()

    # ステータス別棒グラフ
    if len(analysis["status_df"]) > 0:
        st.subheader("ステータス別分布")
        chart_data = analysis["status_df"].set_index("status")
        st.bar_chart(chart_data)

    st.divider()

    # 一覧テーブル + アクション
    st.subheader("CAPA一覧")
    items = get_all()

    if items:
        # テーブル用データ準備
        display_data = []
        for item in items:
            display_data.append({
                "ID": item["id"],
                "タイトル": item["title"],
                "カテゴリ": item["category"],
                "担当者": item["assignee"],
                "ステータス": item["status"],
                "優先度": item["priority"],
                "期限": item["due_date"] or "未設定",
            })

        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True)

        st.divider()

        # ステータス遷移ボタン
        st.subheader("ステータス遷移")
        col_item, col_btn = st.columns([2, 1])

        with col_item:
            selected_id = st.selectbox(
                "CAPA選択",
                options=[item["id"] for item in items],
                format_func=lambda x: f"[{x}] {next(i['title'] for i in items if i['id'] == x)}"
            )

        with col_btn:
            if st.button("→ 次ステータスへ", key="advance_btn"):
                new_status = advance_status(selected_id)
                if new_status:
                    st.success(f"✅ ステータスが「{new_status}」に更新されました")
                    st.rerun()
                else:
                    st.info("ℹ️ これ以上進めません（完了状態）")
    else:
        st.info("CAP Aが登録されていません")


# タブ2: 新規起票
with tab2:
    st.subheader("新規CAPA起票")

    with st.form("new_capa_form"):
        title = st.text_input("タイトル *", placeholder="例：溶接工程不良再発")
        category = st.selectbox("カテゴリ *", ["工程不良", "検査精度", "受入検査", "設備管理", "教育訓練", "その他"])
        assignee = st.text_input("担当者 *", placeholder="例：田中")
        priority = st.selectbox("優先度", ["低", "中", "高"])
        description = st.text_area("詳細説明", placeholder="問題の詳細を入力")
        due_date = st.date_input("期限", datetime.date.today() + datetime.timedelta(days=30))

        submit_btn = st.form_submit_button("起票する", type="primary")

        if submit_btn:
            if not title or not category or not assignee:
                st.error("❌ タイトル・カテゴリ・担当者は必須です")
            else:
                create_item({
                    "title": title,
                    "category": category,
                    "assignee": assignee,
                    "status": "起票",
                    "priority": priority,
                    "description": description or None,
                    "due_date": str(due_date),
                })
                st.success("✅ CAP Aが起票されました")
                st.rerun()


# タブ3: 詳細更新
with tab3:
    st.subheader("CAPA詳細更新")

    items = get_all()
    if items:
        selected_id = st.selectbox(
            "CAPA選択",
            options=[item["id"] for item in items],
            format_func=lambda x: f"[{x}] {next(i['title'] for i in items if i['id'] == x)}",
            key="detail_select"
        )

        selected_item = get_by_id(selected_id)

        if selected_item:
            st.divider()
            st.write(f"**ステータス**: {selected_item['status']}")
            st.write(f"**担当者**: {selected_item['assignee']}")

            with st.form("update_form"):
                root_cause = st.text_area(
                    "根本原因",
                    value=selected_item["root_cause"] or "",
                    placeholder="根本原因を記入"
                )
                action_plan = st.text_area(
                    "対策計画",
                    value=selected_item["action_plan"] or "",
                    placeholder="実施する対策を記入"
                )
                effect_result = st.text_area(
                    "効果結果",
                    value=selected_item["effect_result"] or "",
                    placeholder="対策実施後の効果を記入"
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    update_btn = st.form_submit_button("更新する", type="primary")
                with col2:
                    delete_btn = st.form_submit_button("削除する", type="secondary")
                with col3:
                    pass

                if update_btn:
                    if root_cause:
                        update_field(selected_id, "root_cause", root_cause)
                    if action_plan:
                        update_field(selected_id, "action_plan", action_plan)
                    if effect_result:
                        update_field(selected_id, "effect_result", effect_result)
                    st.success("✅ CAP Aが更新されました")
                    st.rerun()

                if delete_btn:
                    delete_item(selected_id)
                    st.success("✅ CAP Aが削除されました")
                    st.rerun()
    else:
        st.info("CAP Aが登録されていません")
