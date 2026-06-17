# -*- coding: utf-8 -*-
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "cleaned_reservations_202401.csv")

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["checkin_date"] = pd.to_datetime(df["checkin_date"].astype(str).str.replace("/", "-", regex=False), format="%Y-%m-%d")

# Room type analysis
room_groups = df.groupby("room_type")
room_summary_rows = []
for rtype, grp in room_groups:
    total_rev = grp["total_revenue"].sum()
    avg_rate = grp["room_rate"].mean()
    stayed = (grp["status"] == "宿泊済み").sum()
    total = len(grp)
    occ_rate = stayed / total if total > 0 else 0.0
    avg_nights = grp["nights"].mean()
    cancel_count = (grp["status"].isin(["キャンセル", "ノーショウ"])).sum()
    cancel_rate = cancel_count / total if total > 0 else 0.0
    loss_rev = grp["loss_revenue"].sum()
    room_summary_rows.append({
        "room_type": rtype,
        "total_revenue": int(total_rev),
        "avg_room_rate": round(avg_rate, 0),
        "occupancy_rate": round(occ_rate, 4),
        "avg_nights": round(avg_nights, 2),
        "total_reservations": total,
        "stayed_count": int(stayed),
        "cancel_count": int(cancel_count),
        "cancel_rate": round(cancel_rate, 4),
        "loss_revenue": int(loss_rev),
    })

room_summary_df = pd.DataFrame(room_summary_rows).sort_values("total_revenue", ascending=False)
room_summary_path = os.path.join(OUTPUT_DIR, "room_summary_202401.csv")
room_summary_df.to_csv(room_summary_path, index=False, encoding="utf-8-sig")
print("[OK] room_summary_202401.csv written ({} rows)".format(len(room_summary_df)))

# Daily analysis
daily = df.groupby("checkin_date").agg(
    total_reservations=("reserv_no", "count"),
    stayed_count=("status", lambda x: (x == "宿泊済み").sum()),
).reset_index()
daily["occupancy_rate"] = daily["stayed_count"] / daily["total_reservations"]
daily["checkin_date"] = daily["checkin_date"].dt.strftime("%Y-%m-%d")

# Overall stats
total_revenue = int(df["total_revenue"].sum())
total_reservations = len(df)
stayed_total = int((df["status"] == "宿泊済み").sum())
cancel_total = int((df["status"] == "キャンセル").sum())
noshow_total = int((df["status"] == "ノーショウ").sum())
overall_occ_rate = stayed_total / total_reservations if total_reservations > 0 else 0.0
cancel_rate_overall = (cancel_total + noshow_total) / total_reservations if total_reservations > 0 else 0.0
total_loss = int(df["loss_revenue"].sum())

# Write report
report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("# 宿泊予約・稼働率分析レポート (2024年1月)\n\n")
    f.write("## 総合サマリー\n\n")
    f.write("| 指標 | 値 |\n")
    f.write("|------|----|\n")
    f.write("| 総売上 | {:,} 円 |\n".format(total_revenue))
    f.write("| 総予約件数 | {} 件 |\n".format(total_reservations))
    f.write("| 宿泊済み | {} 件 |\n".format(stayed_total))
    f.write("| キャンセル | {} 件 |\n".format(cancel_total))
    f.write("| ノーショウ | {} 件 |\n".format(noshow_total))
    f.write("| 稼働率 | {:.1%} |\n".format(overall_occ_rate))
    f.write("| キャンセル率 | {:.1%} |\n".format(cancel_rate_overall))
    f.write("| キャンセル損失 | {:,} 円 |\n".format(total_loss))
    f.write("\n## 客室タイプ別分析\n\n")
    f.write("| 客室タイプ | 総売上 | 平均室料 | 稼働率 | 平均宿泊数 | キャンセル率 | 損失金額 |\n")
    f.write("|-----------|--------|---------|--------|-----------|-------------|--------|\n")
    for _, row in room_summary_df.iterrows():
        f.write("| {} | {:,} | {:,.0f} | {:.1%} | {:.2f} | {:.1%} | {:,} |\n".format(
            row["room_type"], row["total_revenue"], row["avg_room_rate"],
            row["occupancy_rate"], row["avg_nights"], row["cancel_rate"], row["loss_revenue"]
        ))
    f.write("\n## 日別稼働率\n\n")
    f.write("| 日付 | 予約数 | 宿泊済み | 稼働率 |\n")
    f.write("|------|--------|---------|-------|\n")
    for _, row in daily.iterrows():
        f.write("| {} | {} | {} | {:.1%} |\n".format(
            row["checkin_date"], int(row["total_reservations"]),
            int(row["stayed_count"]), row["occupancy_rate"]
        ))

print("[OK] analysis_report.md written")

# Save result JSON for validate_report.py
result = {
    "total_revenue": total_revenue,
    "total_reservations": total_reservations,
    "stayed_total": stayed_total,
    "cancel_total": cancel_total,
    "noshow_total": noshow_total,
    "overall_occ_rate": overall_occ_rate,
    "cancel_rate_overall": cancel_rate_overall,
    "total_loss": total_loss,
    "room_types": list(room_summary_df["room_type"].values),
    "daily_dates": list(daily["checkin_date"].values),
}
json_path = os.path.join(OUTPUT_DIR, "result_analysis.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("[OK] result_analysis.json written")
print("[OK] Analysis complete.")
