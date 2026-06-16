"""
C-26: 請求書突合・差異検出パイプライン 可視化スクリプト
3枚のグラフを output/charts/ に保存する。
日本語フォント: MS Gothic
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

matplotlib.rcParams["font.family"] = "MS Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "cleaned_invoice_202401.csv"
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["invoice_amount", "received_amount", "variance_amount"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ===== グラフ1: 突合ステータス別件数の棒グラフ =====
status_order = ["一致", "差異", "過払", "未入金"]
status_colors = {
    "一致": "#22c55e",
    "差異": "#f59e0b",
    "過払": "#3b82f6",
    "未入金": "#ef4444",
}

if "match_status" in df.columns:
    status_counts = (
        df["match_status"]
        .value_counts()
        .reindex(status_order)
        .fillna(0)
        .astype(int)
    )
    colors = [status_colors.get(s, "#94a3b8") for s in status_counts.index]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(status_counts.index, status_counts.values, color=colors, width=0.5)
    ax.set_title("突合ステータス別 件数（2024年1月）", fontsize=14)
    ax.set_xlabel("突合ステータス")
    ax.set_ylabel("件数")
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 1,
                f"{int(h):,}", ha="center", va="bottom", fontsize=10,
            )
    ax.set_ylim(0, status_counts.max() * 1.15)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "bar_match_status.png", dpi=150)
    plt.close()
    print("[OK] Saved: bar_match_status.png")

# ===== グラフ2: 差異金額上位10社の横棒グラフ =====
if "client_code" in df.columns and "variance_amount" in df.columns:
    diff_df = df[df["match_status"] != "一致"].copy() if "match_status" in df.columns else df.copy()
    client_var = (
        diff_df.groupby("client_code")["variance_amount"]
        .apply(lambda x: x.abs().sum())
        .sort_values(ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    bar_colors = ["#ef4444" if v >= 0 else "#3b82f6" for v in client_var.values]
    ax.barh(client_var.index[::-1], client_var.values[::-1], color=bar_colors[::-1])
    ax.set_title("差異金額上位10社（絶対値）（2024年1月）", fontsize=14)
    ax.set_xlabel("差異金額合計（円）")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    for i, (val, label) in enumerate(zip(client_var.values[::-1], client_var.index[::-1])):
        ax.text(val + val * 0.01, i, f"{val:,.0f}", va="center", fontsize=8)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "bar_client_variance_top10.png", dpi=150)
    plt.close()
    print("[OK] Saved: bar_client_variance_top10.png")

# ===== グラフ3: 支払区分別件数の円グラフ =====
if "payment_type" in df.columns:
    pay_counts = df["payment_type"].value_counts()
    pie_colors = ["#2563eb", "#7c3aed", "#0891b2"]

    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(
        pay_counts.values,
        labels=pay_counts.index,
        autopct="%1.1f%%",
        colors=pie_colors[: len(pay_counts)],
        startangle=90,
        pctdistance=0.82,
    )
    for at in autotexts:
        at.set_fontsize(11)
    ax.set_title("支払区分別 件数（2024年1月）", fontsize=14)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "pie_payment_type.png", dpi=150)
    plt.close()
    print("[OK] Saved: pie_payment_type.png")

print("[OK] グラフ生成完了 -> output/charts/")
