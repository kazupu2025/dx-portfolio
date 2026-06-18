# -*- coding: utf-8 -*-
"""
C-55 生徒入学申込・入学率分析パイプライン
サンプルデータ生成スクリプト
480件を3スタイルに分割（各160件）
"""

import random
import numpy as np
import pandas as pd
import os

random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 定数
TOTAL = 480
PER_STYLE = 160
DEPARTMENTS = ["文系", "理系", "芸術系", "体育系"]
SELECTION_METHODS = ["一般", "推薦", "AO"]
REGIONS = ["東京", "大阪", "名古屋", "福岡", "仙台"]
RESULTS = ["合格", "不合格"]
PASS_RATE = 0.55
INTERVIEW_RATE = 0.60
DECLINE_REASONS = ["成績不足", "面接低評価", "書類不備"]

# 全480件のデータを生成
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-01-20")
date_range = pd.date_range(start_date, end_date)

records = []
for i in range(TOTAL):
    app_id = f"APP-{i+1:04d}"
    app_date = random.choice(date_range).strftime("%Y/%m/%d")
    dept = random.choice(DEPARTMENTS)
    sel = random.choice(SELECTION_METHODS)
    region = random.choice(REGIONS)
    result = "合格" if random.random() < PASS_RATE else "不合格"
    score = random.randint(50, 100)
    interview_flag = 1 if random.random() < INTERVIEW_RATE else 0
    if result == "不合格":
        decline_reason = random.choice(DECLINE_REASONS)
    else:
        decline_reason = ""
    records.append({
        "app_date_slash": app_date,
        "app_id": app_id,
        "department": dept,
        "selection_method": sel,
        "region": region,
        "result": result,
        "score": score,
        "interview_flag": interview_flag,
        "decline_reason": decline_reason,
    })

df_all = pd.DataFrame(records)

# --- Style A: 標準日本語 (YYYY/MM/DD) ---
df_a = df_all.iloc[0:PER_STYLE].copy()
df_a_out = pd.DataFrame({
    "申込日": df_a["app_date_slash"],
    "申込番号": df_a["app_id"],
    "学科": df_a["department"],
    "選考方法": df_a["selection_method"],
    "地域": df_a["region"],
    "合否": df_a["result"],
    "点数": df_a["score"],
    "面接フラグ": df_a["interview_flag"],
    "辞退理由": df_a["decline_reason"],
})
df_a_out.to_csv(os.path.join(DATA_DIR, "applications_styleA.csv"), index=False, encoding="utf-8-sig")
print(f"[OK] StyleA: {len(df_a_out)} rows -> data/applications_styleA.csv")

# --- Style B: English (YYYY-MM-DD) ---
df_b = df_all.iloc[PER_STYLE:PER_STYLE*2].copy()
# YYYY-MM-DD形式に変換
df_b["app_date_hyphen"] = df_b["app_date_slash"].str.replace("/", "-")
# result を Pass/Fail に変換
df_b["result_en"] = df_b["result"].map({"合格": "Pass", "不合格": "Fail"})
df_b_out = pd.DataFrame({
    "ApplicationDate": df_b["app_date_hyphen"],
    "AppID": df_b["app_id"],
    "Department": df_b["department"],
    "SelectionMethod": df_b["selection_method"],
    "Region": df_b["region"],
    "Result": df_b["result_en"],
    "Score": df_b["score"],
    "InterviewFlag": df_b["interview_flag"],
    "DeclineReason": df_b["decline_reason"],
})
df_b_out.to_csv(os.path.join(DATA_DIR, "applications_styleB.csv"), index=False, encoding="utf-8-sig")
print(f"[OK] StyleB: {len(df_b_out)} rows -> data/applications_styleB.csv")

# --- Style C: バリアント日本語 (YYYY/MM/DD) ---
df_c = df_all.iloc[PER_STYLE*2:PER_STYLE*3].copy()
df_c_out = pd.DataFrame({
    "受付日": df_c["app_date_slash"],
    "受付番号": df_c["app_id"],
    "専攻": df_c["department"],
    "入試区分": df_c["selection_method"],
    "出身地域": df_c["region"],
    "判定": df_c["result"],
    "得点": df_c["score"],
    "面接実施": df_c["interview_flag"],
    "不合格理由": df_c["decline_reason"],
})
df_c_out.to_csv(os.path.join(DATA_DIR, "applications_styleC.csv"), index=False, encoding="utf-8-sig")
print(f"[OK] StyleC: {len(df_c_out)} rows -> data/applications_styleC.csv")

print(f"\n[OK] 合計 {TOTAL} 件のサンプルデータを生成しました。")
