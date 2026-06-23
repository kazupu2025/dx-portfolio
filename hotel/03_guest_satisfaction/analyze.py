# -*- coding: utf-8 -*-
import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "sample_guest_satisfaction.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# ========== 総合サマリー ==========
avg_overall_score = df["overall_score"].mean()
avg_room_score = df["room_score"].mean()
avg_food_score = df["food_score"].mean()
avg_service_score = df["service_score"].mean()

repeat_count = df["is_repeat"].sum()
total_guests = len(df)
repeat_rate = repeat_count / total_guests if total_guests > 0 else 0.0

avg_spend_per_night = df["total_spend"].sum() / df["nights"].sum() if df["nights"].sum() > 0 else 0.0

# ========== 総合スコアの判定 ==========
def get_overall_judgment(score):
    if score >= 4.0:
        return "good"
    elif score >= 3.5:
        return "warning"
    else:
        return "alert"

overall_judgment = get_overall_judgment(avg_overall_score)

# ========== チャネル別集計 ==========
channel_summary_rows = []
for channel, grp in df.groupby("channel"):
    channel_rows = {
        "channel": channel,
        "guest_count": len(grp),
        "avg_overall_score": round(grp["overall_score"].mean(), 2),
        "repeat_rate": round(grp["is_repeat"].sum() / len(grp), 4) if len(grp) > 0 else 0.0,
        "avg_spend": round(grp["total_spend"].mean(), 0),
    }
    channel_summary_rows.append(channel_rows)

channel_summary_df = pd.DataFrame(channel_summary_rows).sort_values("guest_count", ascending=False)

# ========== 客室タイプ別集計 ==========
room_type_summary_rows = []
for room_type, grp in df.groupby("room_type"):
    room_summary = {
        "room_type": room_type,
        "guest_count": len(grp),
        "avg_overall_score": round(grp["overall_score"].mean(), 2),
        "avg_room_score": round(grp["room_score"].mean(), 2),
        "avg_food_score": round(grp["food_score"].mean(), 2),
        "avg_service_score": round(grp["service_score"].mean(), 2),
        "repeat_rate": round(grp["is_repeat"].sum() / len(grp), 4) if len(grp) > 0 else 0.0,
    }
    room_type_summary_rows.append(room_summary)

room_type_summary_df = pd.DataFrame(room_type_summary_rows).sort_values("guest_count", ascending=False)

# ========== リピーター vs 新規 ==========
repeat_data = df[df["is_repeat"] == True]
new_data = df[df["is_repeat"] == False]

repeat_avg_score = repeat_data["overall_score"].mean() if len(repeat_data) > 0 else 0.0
new_avg_score = new_data["overall_score"].mean() if len(new_data) > 0 else 0.0

# ========== Write report ==========
report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("# 顧客満足度・リピート分析レポート\n\n")
    f.write("## 総合サマリー\n\n")
    f.write("| 指標 | 値 |\n")
    f.write("|------|----|\n")
    f.write("| 平均総合スコア | {:.2f} |\n".format(avg_overall_score))
    f.write("| 判定 | {} |\n".format(overall_judgment))
    f.write("| リピート率 | {:.1%} |\n".format(repeat_rate))
    f.write("| 1泊単価 | {:,.0f} 円 |\n".format(avg_spend_per_night))
    f.write("| 総ゲスト数 | {} 人 |\n".format(total_guests))
    f.write("\n## スコア別詳細\n\n")
    f.write("| スコア項目 | 平均値 |\n")
    f.write("|-----------|-------|\n")
    f.write("| 客室満足度 | {:.2f} |\n".format(avg_room_score))
    f.write("| 食事満足度 | {:.2f} |\n".format(avg_food_score))
    f.write("| サービス満足度 | {:.2f} |\n".format(avg_service_score))
    f.write("\n## チャネル別集計\n\n")
    f.write("| チャネル | ゲスト数 | 平均スコア | リピート率 | 平均支払額 |\n")
    f.write("|---------|---------|-----------|-----------|----------|\n")
    for _, row in channel_summary_df.iterrows():
        f.write("| {} | {} | {:.2f} | {:.1%} | {:,.0f} 円 |\n".format(
            row["channel"], int(row["guest_count"]), row["avg_overall_score"],
            row["repeat_rate"], row["avg_spend"]
        ))
    f.write("\n## 客室タイプ別集計\n\n")
    f.write("| 客室タイプ | ゲスト数 | 総合 | 客室 | 食事 | サービス | リピート率 |\n")
    f.write("|-----------|---------|------|------|------|---------|----------|\n")
    for _, row in room_type_summary_df.iterrows():
        f.write("| {} | {} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.1%} |\n".format(
            row["room_type"], int(row["guest_count"]),
            row["avg_overall_score"], row["avg_room_score"],
            row["avg_food_score"], row["avg_service_score"],
            row["repeat_rate"]
        ))
    f.write("\n## リピーター vs 新規ゲスト比較\n\n")
    f.write("| 区分 | ゲスト数 | 平均スコア |\n")
    f.write("|------|---------|----------|\n")
    f.write("| リピーター | {} | {:.2f} |\n".format(int(repeat_count), repeat_avg_score))
    f.write("| 新規ゲスト | {} | {:.2f} |\n".format(int(total_guests - repeat_count), new_avg_score))

print("[OK] analysis_report.md written")

# ========== Save result JSON ==========
result = {
    "avg_overall_score": round(avg_overall_score, 2),
    "avg_room_score": round(avg_room_score, 2),
    "avg_food_score": round(avg_food_score, 2),
    "avg_service_score": round(avg_service_score, 2),
    "overall_judgment": overall_judgment,
    "repeat_count": int(repeat_count),
    "total_guests": int(total_guests),
    "repeat_rate": round(repeat_rate, 4),
    "avg_spend_per_night": round(avg_spend_per_night, 2),
    "channels": list(channel_summary_df["channel"].values),
    "room_types": list(room_type_summary_df["room_type"].values),
    "repeat_avg_score": round(repeat_avg_score, 2),
    "new_avg_score": round(new_avg_score, 2),
}
json_path = os.path.join(OUTPUT_DIR, "result_analysis.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("[OK] result_analysis.json written")
print("[OK] Analysis complete.")
