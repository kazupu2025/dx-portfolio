import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyze import analyze, REQUIRED_COLUMNS

st.set_page_config(page_title="C-119 宴会・イベント収益管理", layout="wide")

st.title("C-119 宴会・イベント収益管理")
st.markdown("ホテルの宴会・イベント収益分析ダッシュボード")

# サイドバー
st.sidebar.header("データアップロード")
uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type=["csv"])

# サンプルファイルがある場合はデフォルトで使用
sample_file = Path(__file__).parent / "sample_banquet.csv"

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif sample_file.exists():
    df = pd.read_csv(sample_file)
else:
    st.error("データファイルが見つかりません")
    st.stop()

# バリデーション
missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
if missing_cols:
    st.error(f"必須列が不足しています: {', '.join(missing_cols)}")
    st.stop()

# 分析実行
result = analyze(df)

# KPIカード
st.subheader("主要KPI")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "総収益",
        f"¥{result['total_revenue']:,.0f}",
        delta=None,
    )

with col2:
    st.metric(
        "イベント数",
        f"{result['total_events']}件",
        delta=None,
    )

with col3:
    st.metric(
        "1件平均売上",
        f"¥{result['avg_revenue_per_event']:,.0f}",
        delta=None,
    )

with col4:
    guest_price = result["avg_revenue_per_guest"]
    color = "🟢" if result["verdict"] == "good" else "🟡" if result["verdict"] == "warning" else "🔴"
    st.metric(
        "1名単価",
        f"¥{guest_price:,.0f}",
        delta=f"{color} {result['verdict'].upper()}",
    )

# 補足情報
col_cancel, col_verdict = st.columns(2)
with col_cancel:
    st.info(f"キャンセル率: {result['cancel_rate']:.1f}%")
with col_verdict:
    verdict_text = {
        "good": "良好 - 高単価を維持",
        "warning": "注意 - 改善の余地あり",
        "alert": "警告 - 単価向上が必要",
    }
    st.warning(verdict_text[result["verdict"]])

st.divider()

# イベント種別売上分析
st.subheader("イベント種別分析")
event_df = result["event_df"].copy()

col1, col2 = st.columns([2, 1])
with col1:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(event_df["event_type"], event_df["total_revenue"], color="#1f77b4")
    ax.set_xlabel("売上（円）", fontsize=11)
    ax.set_ylabel("イベント種別", fontsize=11)
    ax.set_title("イベント種別別総売上", fontsize=12, fontweight="bold")
    ax.invert_yaxis()
    for i, v in enumerate(event_df["total_revenue"]):
        ax.text(v, i, f" ¥{v/1e6:.1f}M", va="center", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.dataframe(
        event_df[["event_type", "count", "avg_revenue", "avg_guests"]].rename(
            columns={
                "event_type": "種別",
                "count": "件数",
                "avg_revenue": "平均売上",
                "avg_guests": "平均人数",
            }
        ),
        use_container_width=True,
    )

st.divider()

# 月次トレンド
st.subheader("月次収益トレンド")
monthly_df = result["monthly_df"].copy()

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(monthly_df["date"], monthly_df["total_revenue"], marker="o", linewidth=2, markersize=8, color="#ff7f0e")
ax.set_xlabel("月", fontsize=11)
ax.set_ylabel("売上（円）", fontsize=11)
ax.set_title("月次売上推移", fontsize=12, fontweight="bold")
ax.grid(True, alpha=0.3)
for i, v in enumerate(monthly_df["total_revenue"]):
    ax.text(i, v, f"¥{v/1e6:.1f}M", ha="center", va="bottom", fontsize=9)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

st.divider()

# 会場別分析
st.subheader("会場別稼働・収益")
room_df = result["room_df"].copy()

st.dataframe(
    room_df.rename(
        columns={
            "room_name": "会場名",
            "count": "稼働数",
            "total_revenue": "総売上",
            "avg_guests": "平均人数",
        }
    )[["会場名", "稼働数", "総売上", "平均人数"]],
    use_container_width=True,
)

st.divider()

# 生データ
st.subheader("生データ（完了分）")
st.dataframe(result["df"].rename(columns={
    "date": "日付",
    "event_type": "イベント種別",
    "room_name": "会場",
    "guests": "人数",
    "food_revenue": "食事売上",
    "beverage_revenue": "飲料売上",
    "room_fee": "会場費",
    "total_revenue": "総売上",
    "status": "ステータス",
}), use_container_width=True)
