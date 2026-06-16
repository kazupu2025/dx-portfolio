"""
C-31: 契約更新アラート・期限管理パイプライン 可視化スクリプト
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

CSV_PATH = OUTPUT_DIR / "cleaned_contracts_202401.csv"
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
for col in ["annual_premium", "days_to_expiry", "contract_years"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

STATUS_ORDER = ["期限切れ", "緊急", "警告", "正常"]
STATUS_COLORS = {
    "期限切れ": "#ef4444",  # 赤
    "緊急":     "#f97316",  # 橙
    "警告":     "#eab308",  # 黄
    "正常":     "#22c55e",  # 緑
}

# ===== グラフ1: 更新ステータス別件数の棒グラフ =====
if "renewal_status" in df.columns:
    status_counts = (
        df["renewal_status"]
        .value_counts()
        .reindex(STATUS_ORDER)
        .fillna(0)
        .astype(int)
    )
    colors = [STATUS_COLORS.get(s, "#94a3b8") for s in status_counts.index]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(status_counts.index, status_counts.values, color=colors, width=0.5)
    ax.set_title("更新ステータス別 契約件数（基準日: 2024/02/01）", fontsize=14)
    ax.set_xlabel("更新ステータス")
    ax.set_ylabel("件数")
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 0.5,
                f"{int(h):,}", ha="center", va="bottom", fontsize=11,
            )
    ax.set_ylim(0, status_counts.max() * 1.15)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "bar_renewal_status.png", dpi=150)
    plt.close()
    print("[OK] Saved: bar_renewal_status.png")

# ===== グラフ2: 担当者別アラート件数の横棒グラフ =====
if "agent_name" in df.columns and "renewal_status" in df.columns:
    alert_df = df[df["renewal_status"].isin(["期限切れ", "緊急"])]
    agent_alert = (
        alert_df.groupby("agent_name")["contract_no"]
        .count()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    bar_colors = ["#ef4444" if v >= agent_alert.median() else "#f97316"
                  for v in agent_alert.values]
    ax.barh(agent_alert.index, agent_alert.values, color=bar_colors)
    ax.set_title("担当者別 アラート件数（期限切れ+緊急）", fontsize=14)
    ax.set_xlabel("アラート件数")
    for i, val in enumerate(agent_alert.values):
        ax.text(val + 0.2, i, f"{val:,}", va="center", fontsize=10)
    ax.set_xlim(0, agent_alert.max() * 1.15)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "bar_agent_alert.png", dpi=150)
    plt.close()
    print("[OK] Saved: bar_agent_alert.png")

# ===== グラフ3: 保険種別件数の円グラフ =====
if "insurance_type" in df.columns:
    ins_counts = df["insurance_type"].value_counts()
    pie_colors = ["#2563eb", "#7c3aed", "#0891b2", "#059669"]

    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(
        ins_counts.values,
        labels=ins_counts.index,
        autopct="%1.1f%%",
        colors=pie_colors[: len(ins_counts)],
        startangle=90,
        pctdistance=0.82,
    )
    for at in autotexts:
        at.set_fontsize(11)
    ax.set_title("保険種別 件数構成（2024年1月）", fontsize=14)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "pie_insurance_type.png", dpi=150)
    plt.close()
    print("[OK] Saved: pie_insurance_type.png")

print("[OK] グラフ生成完了 -> output/charts/")
