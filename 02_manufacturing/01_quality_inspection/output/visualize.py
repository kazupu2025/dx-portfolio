import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pathlib import Path
import yaml

with open("config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)
DEFECT_ALERT = config.get("defect_rate_alert_threshold", 0.05)

df = pd.read_csv("output/cleaned_inspection_202401.csv", encoding="utf-8-sig")
for col in ["inspection_value", "lower_limit", "upper_limit"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
if "is_defect" in df.columns:
    df["is_defect"] = df["is_defect"].astype(bool)

charts_dir = Path("output/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

# 1. 工程別不良率棒グラフ
proc_dr = df.groupby("process").apply(
    lambda g: g["is_defect"].mean() * 100
).sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#ef4444" if v > DEFECT_ALERT * 100 else "#2563eb" for v in proc_dr.values]
bars = ax.bar(proc_dr.index, proc_dr.values, color=colors)
ax.axhline(y=DEFECT_ALERT * 100, color="#f97316", linestyle="--",
           label=f"アラートライン ({DEFECT_ALERT*100:.0f}%)")
ax.set_title("工程別 不良率（2024年1月）", fontsize=14)
ax.set_ylabel("不良率（%）")
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 0.05,
            f"{h:.2f}%", ha="center", va="bottom", fontsize=9)
ax.legend()
plt.tight_layout()
plt.savefig(charts_dir / "bar_process_defect_rate.png", dpi=150)
plt.close()
print("Saved: bar_process_defect_rate.png")

# 2. 日次不良率トレンド折れ線グラフ
if "date" in df.columns:
    daily = df.groupby("date").apply(lambda g: g["is_defect"].mean() * 100).reset_index()
    daily.columns = ["date", "defect_rate"]
    daily = daily.sort_values("date")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(daily["date"], daily["defect_rate"], color="#2563eb", marker="o", markersize=4)
    ax.axhline(y=DEFECT_ALERT * 100, color="#ef4444", linestyle="--",
               label=f"アラートライン ({DEFECT_ALERT*100:.0f}%)")
    ax.fill_between(daily["date"],
                    daily["defect_rate"],
                    DEFECT_ALERT * 100,
                    where=daily["defect_rate"] > DEFECT_ALERT * 100,
                    alpha=0.3, color="#ef4444", label="アラート超過")
    ax.set_title("日次 不良率トレンド（2024年1月）", fontsize=14)
    ax.set_ylabel("不良率（%）")
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%m/%d"))
    plt.xticks(rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig(charts_dir / "line_daily_defect_trend.png", dpi=150)
    plt.close()
    print("Saved: line_daily_defect_trend.png")

# 3. 工程×製品 不良率ヒートマップ
try:
    import seaborn as sns
    pivot = df.pivot_table(
        index="process", columns="product_code",
        values="is_defect", aggfunc="mean"
    ) * 100

    if pivot.shape[1] > 0:
        fig, ax = plt.subplots(figsize=(14, 5))
        sns.heatmap(
            pivot,
            annot=True, fmt=".1f", cmap="YlOrRd",
            linewidths=0.5,
            cbar_kws={"label": "不良率 (%)"},
            ax=ax,
        )
        ax.set_title("工程×製品コード 不良率ヒートマップ（2024年1月）", fontsize=14)
        ax.set_xlabel("製品コード")
        ax.set_ylabel("工程")
        plt.tight_layout()
        plt.savefig(charts_dir / "heatmap_process_product.png", dpi=150)
        plt.close()
        print("Saved: heatmap_process_product.png")
    else:
        print("WARN: pivot が空のためヒートマップをスキップ")
except ImportError:
    print("WARN: seaborn がないためヒートマップをスキップ")
    # フォールバック: matplotlibのimshowで代替
    pivot2 = df.pivot_table(
        index="process", columns="product_code",
        values="is_defect", aggfunc="mean"
    ).fillna(0) * 100

    fig, ax = plt.subplots(figsize=(14, 5))
    im = ax.imshow(pivot2.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(pivot2.columns)))
    ax.set_xticklabels(pivot2.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(pivot2.index)))
    ax.set_yticklabels(pivot2.index)
    for i in range(len(pivot2.index)):
        for j in range(len(pivot2.columns)):
            ax.text(j, i, f"{pivot2.values[i,j]:.1f}",
                    ha="center", va="center", fontsize=7, color="black")
    plt.colorbar(im, ax=ax, label="不良率 (%)")
    ax.set_title("工程×製品コード 不良率ヒートマップ（2024年1月）", fontsize=14)
    plt.tight_layout()
    plt.savefig(charts_dir / "heatmap_process_product.png", dpi=150)
    plt.close()
    print("Saved: heatmap_process_product.png (fallback)")

print("グラフ生成完了")
