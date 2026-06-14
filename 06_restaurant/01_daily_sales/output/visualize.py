import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path

df = pd.read_csv("output/cleaned_sales_202401.csv", encoding="utf-8-sig")
for col in ["sales_amount", "waste_amount"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

charts_dir = Path("output/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. 店舗別売上棒グラフ
store_sales = df.groupby("store_name")["sales_amount"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(store_sales.index, store_sales.values, color="#2563eb")
ax.set_title("店舗別月間売上（2024年1月）", fontsize=14)
ax.set_ylabel("売上金額（円）")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + h*0.01,
            f"{h:,.0f}", ha="center", va="bottom", fontsize=10)
plt.tight_layout()
plt.savefig(charts_dir / "bar_store_sales.png", dpi=150)
plt.close()
print("Saved: bar_store_sales.png")

# 2. 日次売上折れ線グラフ
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    daily = df.groupby("date")["sales_amount"].sum().sort_index()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(daily.index, daily.values, marker="o", color="#2563eb", linewidth=2, markersize=4)
    ax.set_title("日次売上トレンド（2024年1月）", fontsize=14)
    ax.set_ylabel("売上金額（円）")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(charts_dir / "line_daily_sales.png", dpi=150)
    plt.close()
    print("Saved: line_daily_sales.png")

# 3. 廃棄ロス率棒グラフ（A-02 追加）
if "waste_amount" in df.columns:
    waste = df.groupby("store_name").agg(
        売上=("sales_amount", "sum"),
        廃棄=("waste_amount", "sum"),
    )
    waste["廃棄ロス率"] = waste["廃棄"] / waste["売上"] * 100
    waste = waste.sort_values("廃棄ロス率", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#ef4444" if v > 5 else "#22c55e" for v in waste["廃棄ロス率"]]
    bars = ax.bar(waste.index, waste["廃棄ロス率"], color=colors)
    ax.axhline(y=5, color="red", linestyle="--", linewidth=1.5, label="アラート閾値（5%）")
    ax.set_title("店舗別廃棄ロス率（2024年1月）", fontsize=14)
    ax.set_ylabel("廃棄ロス率（%）")
    for bar, v in zip(bars, waste["廃棄ロス率"]):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.1,
                f"{v:.2f}%", ha="center", va="bottom", fontsize=10)
    ax.legend()
    plt.tight_layout()
    plt.savefig(charts_dir / "bar_waste_loss.png", dpi=150)
    plt.close()
    print("Saved: bar_waste_loss.png")

print("グラフ生成完了")
