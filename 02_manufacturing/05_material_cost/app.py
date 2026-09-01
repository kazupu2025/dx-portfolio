# -*- coding: utf-8 -*-
"""
B-87: 製造 原材料コスト変動ダッシュボード
材料別単価変動 × カテゴリ別コスト構成 × 仕入先構成分析
スタンドアロン版（外部ファイル・PNG依存を排除）
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path

try:
    import plotly.express as px
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

BASE_DIR = Path(__file__).resolve().parent


# ── サンプルデータ生成（インライン） ────────────────────────────
@st.cache_data
def load_b87_material_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    categories = ["金属", "樹脂", "化学品", "電子部品", "補助材"]
    suppliers  = ["サプライヤーA", "サプライヤーB", "サプライヤーC",
                  "サプライヤーD", "サプライヤーE"]
    materials = [
        ("M001", "鉄板（SS400）", "金属"), ("M002", "アルミ押出材", "金属"),
        ("M003", "銅板", "金属"), ("M004", "ステンレス棒", "金属"),
        ("M005", "ABS樹脂ペレット", "樹脂"), ("M006", "ポリカーボネート", "樹脂"),
        ("M007", "ナイロン66", "樹脂"), ("M008", "ポリプロピレン", "樹脂"),
        ("M009", "溶剤（MEK）", "化学品"), ("M010", "切削油", "化学品"),
        ("M011", "接着剤", "化学品"), ("M012", "塗料（ライン用）", "化学品"),
        ("M013", "抵抗器（1/4W）", "電子部品"), ("M014", "コンデンサ（1uF）", "電子部品"),
        ("M015", "ICチップ（マイコン）", "電子部品"), ("M016", "コネクタ", "電子部品"),
        ("M017", "梱包ダンボール", "補助材"), ("M018", "クッション材", "補助材"),
        ("M019", "結束バンド", "補助材"), ("M020", "シリカゲル", "補助材"),
    ]
    rows = []
    for code, name, cat in materials:
        base_price  = float(rng.integers(100, 5000))
        prev_price  = base_price * float(rng.uniform(0.85, 1.15))
        change_rate = (base_price - prev_price) / prev_price
        quantity    = int(rng.integers(50, 500))
        supplier    = rng.choice(suppliers)
        flag = "急騰" if change_rate > 0.10 else ("急落" if change_rate < -0.10 else "安定")
        rows.append({
            "material_code":    code,
            "material_name":    name,
            "category":         cat,
            "supplier":         supplier,
            "purchase_date":    "2024-01-15",
            "quantity":         quantity,
            "unit_price":       round(base_price, 2),
            "prev_month_price": round(prev_price, 2),
            "price_change_rate": round(change_rate, 4),
            "total_cost":       round(base_price * quantity, 2),
            "price_change_flag": flag,
        })
    return pd.DataFrame(rows)


# ── UI ─────────────────────────────────────────────────────────
st.title("🏭 B-87 製造 原材料コスト変動ダッシュボード")
st.caption("B-87 | 製造 × 購買管理 | 材料別単価変動・急騰急落検知・仕入先コスト構成分析")

df_all = load_b87_material_data()

# カテゴリフィルター
categories = sorted(df_all["category"].unique().tolist())
selected_cats = st.multiselect("カテゴリフィルター", categories, default=categories,
                                key="b87_cat_filter")
df = df_all[df_all["category"].isin(selected_cats)] if selected_cats else df_all

st.divider()

# ── KPI 4列 ────────────────────────────────────────────────────
total_cost = float(df["total_cost"].sum())
n_soar     = int((df["price_change_flag"] == "急騰").sum())
n_drop     = int((df["price_change_flag"] == "急落").sum())
avg_change = float(df["price_change_rate"].mean()) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("仕入総額", f"¥{total_cost:,.0f}")
c2.metric("急騰品目数", f"{n_soar} 件",
          delta="要注意" if n_soar > 0 else "問題なし",
          delta_color="inverse" if n_soar > 0 else "normal")
c3.metric("急落品目数", f"{n_drop} 件",
          delta="機会あり" if n_drop > 0 else "なし",
          delta_color="normal")
c4.metric("平均変動率", f"{avg_change:+.2f}%",
          delta="上昇傾向" if avg_change > 0 else "下落傾向",
          delta_color="inverse" if avg_change > 5 else "normal")

st.divider()

# ── 3タブ ────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["カテゴリ別コスト", "単価変動ランキング", "仕入先構成"])

with tab1:
    cat_tbl = (
        df.groupby("category")
          .agg(仕入コスト合計=("total_cost", "sum"), 取引件数=("total_cost", "count"))
          .sort_values("仕入コスト合計", ascending=False)
    )
    if _HAS_PLOTLY:
        fig = px.bar(cat_tbl.reset_index(), x="category", y="仕入コスト合計",
                     color="category", title="カテゴリ別 仕入コスト",
                     labels={"category": "カテゴリ", "仕入コスト合計": "コスト（円）"})
        fig.update_layout(showlegend=False, height=360)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(cat_tbl["仕入コスト合計"])

    cat_disp = cat_tbl.copy()
    cat_disp["仕入コスト合計"] = cat_disp["仕入コスト合計"].apply(lambda x: f"¥{x:,.0f}")
    st.dataframe(cat_disp, use_container_width=True)

with tab2:
    rank_df = df.sort_values("price_change_rate", ascending=False).copy()
    rank_df["変動率(%)"] = (rank_df["price_change_rate"] * 100).round(2)
    colors = ["#ef4444" if f == "急騰" else "#16a34a" if f == "急落" else "#94a3b8"
              for f in rank_df["price_change_flag"]]
    if _HAS_PLOTLY:
        fig2 = go.Figure()
        fig2.add_bar(
            x=rank_df["material_name"], y=rank_df["変動率(%)"],
            marker_color=colors, name="変動率(%)",
        )
        fig2.add_hline(y=10,  line_dash="dash", line_color="#ef4444",
                       annotation_text="急騰ライン(+10%)")
        fig2.add_hline(y=-10, line_dash="dash", line_color="#16a34a",
                       annotation_text="急落ライン(-10%)")
        fig2.update_layout(title="材料別 単価変動率", xaxis_title="材料名",
                           yaxis_title="変動率(%)", height=380)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.bar_chart(rank_df.set_index("material_name")["変動率(%)"])

with tab3:
    sup_tbl = (
        df.groupby("supplier")
          .agg(仕入コスト合計=("total_cost", "sum"), 取引件数=("total_cost", "count"))
    )
    total_sup = sup_tbl["仕入コスト合計"].sum()
    sup_tbl["構成比(%)"] = (sup_tbl["仕入コスト合計"] / total_sup * 100).round(1)
    if _HAS_PLOTLY:
        fig3 = px.pie(sup_tbl.reset_index(), names="supplier", values="仕入コスト合計",
                      title="仕入先別コスト構成")
        fig3.update_layout(height=360)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.bar_chart(sup_tbl["仕入コスト合計"].sort_values(ascending=False))

    sup_disp = sup_tbl.copy()
    sup_disp["仕入コスト合計"] = sup_disp["仕入コスト合計"].apply(lambda x: f"¥{x:,.0f}")
    sup_disp = sup_disp.sort_values("構成比(%)", ascending=False)
    st.dataframe(sup_disp, use_container_width=True)

st.divider()

# ── 急騰・急落明細 ────────────────────────────────────────────
st.subheader("急騰・急落 明細")
flag_filter = st.radio("フィルター", ["急騰", "急落", "すべて"], horizontal=True,
                        key="b87_flag_filter")
if flag_filter == "すべて":
    alert_df = df[df["price_change_flag"].isin(["急騰", "急落"])].copy()
else:
    alert_df = df[df["price_change_flag"] == flag_filter].copy()

if len(alert_df) > 0:
    disp = alert_df[[
        "material_code", "material_name", "category", "supplier",
        "unit_price", "prev_month_price", "price_change_rate", "price_change_flag",
        "total_cost",
    ]].copy()
    disp["price_change_rate"] = (disp["price_change_rate"] * 100).round(2)
    disp = disp.rename(columns={
        "material_code": "材料コード", "material_name": "材料名", "category": "カテゴリ",
        "supplier": "仕入先", "unit_price": "単価", "prev_month_price": "前月単価",
        "price_change_rate": "変動率(%)", "price_change_flag": "フラグ",
        "total_cost": "仕入コスト",
    })
    st.dataframe(disp.sort_values("変動率(%)", ascending=False),
                 hide_index=True, use_container_width=True)
else:
    st.info("該当データなし")
