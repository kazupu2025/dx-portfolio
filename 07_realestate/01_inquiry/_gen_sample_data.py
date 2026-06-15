import pandas as pd
import numpy as np
import random
from datetime import date, timedelta
from pathlib import Path

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/07_realestate/01_inquiry")

areas = ["渋谷区", "新宿区", "港区", "世田谷区", "品川区"]
property_types = ["マンション", "戸建て", "土地", "事務所"]
channels = ["ポータルサイト", "SNS広告", "紹介", "店頭来店", "チラシ"]
agents = ["田中", "鈴木", "佐藤", "山田", "中村"]
stages = ["問い合わせ", "内見", "申し込み", "成約"]

stage_probs = [1.0, 0.40, 0.35 * 0.40, 0.70 * 0.35 * 0.40]

def all_days(year=2024, month=1):
    days = []
    d = date(year, month, 1)
    while d.month == month:
        days.append(d)
        d += timedelta(days=1)
    return days

month_days = all_days()


def gen_rows(area: str, n_total: int, col_style: str) -> list:
    rows = []
    for i in range(n_total):
        inq_id = f"INQ-{area[:2]}-{i+1:04d}"
        inq_date = random.choice(month_days)
        agent = random.choice(agents)
        prop_type = random.choice(property_types)
        channel = random.choices(channels, weights=[0.45, 0.20, 0.15, 0.12, 0.08])[0]
        price_range = {
            "渋谷区": (8000, 15000), "新宿区": (5000, 10000),
            "港区": (12000, 25000), "世田谷区": (6000, 12000), "品川区": (5000, 9000),
        }
        lo, hi = price_range[area]
        contract_amount = round(float(rng.uniform(lo, hi)), 0) if rng.random() > 0 else 0

        final_stage_idx = 0
        for j, prob in enumerate(stage_probs):
            if rng.random() < prob:
                final_stage_idx = j
        stage = stages[final_stage_idx]
        is_contracted = (stage == "成約")
        amount = contract_amount if is_contracted else 0.0
        date_str = inq_date.strftime("%Y/%m/%d")

        if col_style == "standard":
            rows.append({
                "日付": date_str, "問い合わせID": inq_id, "担当者": agent,
                "エリア": area, "物件種別": prop_type, "問い合わせ経路": channel,
                "ステータス": stage, "成約フラグ": int(is_contracted),
                "成約金額(万円)": amount,
            })
        elif col_style == "english":
            rows.append({
                "Date": date_str, "InquiryID": inq_id, "Agent": agent,
                "Area": area, "PropertyType": prop_type, "Channel": channel,
                "Status": stage, "IsContracted": int(is_contracted),
                "ContractAmount": amount,
            })
        else:  # variant
            rows.append({
                "受付日": date_str, "案件番号": inq_id, "担当": agent,
                "地区": area, "種別": prop_type, "媒体": channel,
                "進捗": stage, "契約済": int(is_contracted),
                "契約額": amount,
            })
    return rows


files_config = [
    ("渋谷区",   "standard", "01_渋谷区_問い合わせ_202401.csv",   120),
    ("新宿区",   "english",  "02_新宿区_inquiry_202401.csv",       100),
    ("港区",     "variant",  "03_港区_問い合わせ_202401.csv",       80),
    ("世田谷区", "standard", "04_世田谷区_問い合わせ_202401.csv",  110),
    ("品川区",   "standard", "05_品川区_問い合わせ_202401.csv",     90),
]

for area, style, filename, n in files_config:
    rows = gen_rows(area, n, style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    contracted = sum(1 for r in rows if r.get("成約フラグ", r.get("IsContracted", r.get("契約済", 0))) == 1)
    print(f"Created {filename}: {len(df)} rows, 成約: {contracted}件, style={style}")

print("\nサンプルデータ生成完了（5エリア）")
