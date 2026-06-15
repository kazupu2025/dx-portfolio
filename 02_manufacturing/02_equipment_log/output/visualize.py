"""
B-09 可視化 (3チャート)
Usage: cd 02_manufacturing/02_equipment_log && python output/visualize.py
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

OUT    = Path(__file__).parent
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

EQUIPMENT_COLORS = {
    "E-001": "#1f77b4",
    "E-002": "#ff7f0e",
    "E-003": "#2ca02c",
    "E-004": "#d62728",
    "E-005": "#9467bd",
}


def main():
    anomaly_path = OUT / "anomaly_sensor_202401.csv"
    if not anomaly_path.exists():
        print("ERROR: anomaly_sensor_202401.csv が存在しません")
        return

    df = pd.read_csv(anomaly_path, encoding="utf-8-sig")
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # --- Chart 1: 設備別温度時系列（稼働中のみ）---
    fig, ax = plt.subplots(figsize=(14, 6))
    op_df = df[df["is_operating"] == 1]
    for eq_id, grp in op_df.groupby("equipment_id"):
        eq_name = grp["equipment_name"].iloc[0] if "equipment_name" in grp.columns else eq_id
        color = EQUIPMENT_COLORS.get(eq_id, None)
        ax.plot(grp["timestamp"], grp["temperature"],
                label=f"{eq_id} {eq_name}", color=color, linewidth=0.8, alpha=0.85)
    ax.set_title("設備別 温度時系列トレンド（稼働中）", fontsize=14, pad=12)
    ax.set_xlabel("日時")
    ax.set_ylabel("温度 (°C)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path1 = CHARTS / "line_equipment_temperature.png"
    fig.savefig(path1, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path1}")

    # --- Chart 2: 設備別アラート件数積み上げ棒グラフ ---
    fig, ax = plt.subplots(figsize=(10, 6))
    equipment_ids = sorted(df["equipment_id"].unique())
    alert_counts = {}
    for eq_id in equipment_ids:
        eq_df = df[df["equipment_id"] == eq_id]
        alert_counts[eq_id] = {
            "CRITICAL": (eq_df.get("alert_level", pd.Series()) == "CRITICAL").sum() if "alert_level" in eq_df else 0,
            "WARNING":  (eq_df.get("alert_level", pd.Series()) == "WARNING").sum()  if "alert_level" in eq_df else 0,
            "NORMAL":   (eq_df.get("alert_level", pd.Series()) == "NORMAL").sum()   if "alert_level" in eq_df else 0,
        }

    x = np.arange(len(equipment_ids))
    width = 0.5
    normal_vals   = [alert_counts[e]["NORMAL"]   for e in equipment_ids]
    warning_vals  = [alert_counts[e]["WARNING"]  for e in equipment_ids]
    critical_vals = [alert_counts[e]["CRITICAL"] for e in equipment_ids]

    bars_n = ax.bar(x, normal_vals,   width, label="NORMAL",   color="#2ca02c", alpha=0.8)
    bars_w = ax.bar(x, warning_vals,  width, bottom=normal_vals, label="WARNING", color="#ff7f0e", alpha=0.9)
    bottom2 = [n + w for n, w in zip(normal_vals, warning_vals)]
    bars_c = ax.bar(x, critical_vals, width, bottom=bottom2, label="CRITICAL", color="#d62728", alpha=0.9)

    ax.set_title("設備別 アラート件数（CRITICAL / WARNING / NORMAL）", fontsize=13)
    ax.set_xlabel("設備ID")
    ax.set_ylabel("件数")
    ax.set_xticks(x)
    ax.set_xticklabels(equipment_ids)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    path2 = CHARTS / "bar_equipment_alert_count.png"
    fig.savefig(path2, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path2}")

    # --- Chart 3: 設備×センサー 平均最大Zスコアヒートマップ ---
    SENSORS = ["temperature", "vibration", "pressure", "rpm"]
    z_cols  = [f"{s}_z" for s in SENSORS]

    heatmap_data = {}
    for eq_id in equipment_ids:
        eq_df = df[df["equipment_id"] == eq_id]
        row = []
        for z_col in z_cols:
            if z_col in eq_df.columns:
                val = eq_df[z_col].abs().mean()
                row.append(round(val, 3) if not pd.isna(val) else 0.0)
            else:
                row.append(0.0)
        heatmap_data[eq_id] = row

    heatmap_df = pd.DataFrame(heatmap_data, index=SENSORS).T

    fig, ax = plt.subplots(figsize=(9, 5))
    try:
        import seaborn as sns
        sns.heatmap(heatmap_df, ax=ax, annot=True, fmt=".3f",
                    cmap="YlOrRd", linewidths=0.5, linecolor="white",
                    cbar_kws={"label": "平均|Zスコア|"})
    except ImportError:
        im = ax.imshow(heatmap_df.values, aspect="auto", cmap="YlOrRd")
        plt.colorbar(im, ax=ax, label="平均|Zスコア|")
        ax.set_xticks(range(len(SENSORS)))
        ax.set_xticklabels(SENSORS)
        ax.set_yticks(range(len(equipment_ids)))
        ax.set_yticklabels(equipment_ids)
        for i in range(len(equipment_ids)):
            for j in range(len(SENSORS)):
                ax.text(j, i, f"{heatmap_df.values[i, j]:.3f}",
                        ha="center", va="center", fontsize=9)

    ax.set_title("設備×センサー 平均最大Zスコアヒートマップ", fontsize=13, pad=10)
    ax.set_xlabel("センサー")
    ax.set_ylabel("設備ID")
    fig.tight_layout()
    path3 = CHARTS / "heatmap_equipment_sensor_z.png"
    fig.savefig(path3, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path3}")

    print("=== 可視化完了: 3チャート ===")


if __name__ == "__main__":
    main()
