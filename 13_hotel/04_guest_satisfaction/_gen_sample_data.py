# -*- coding: utf-8 -*-
import os
import random
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Parameters
num_records = 50
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 6, 30)

# Generate sample data
records = []
for i in range(num_records):
    guest_id = f"G{i+1:03d}"
    stay_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    room_type = random.choice(["シングル", "ダブル", "ツイン", "スイート"])
    nights = random.randint(1, 5)

    # Spend based on room type and nights
    room_rate = {
        "シングル": 8000,
        "ダブル": 12000,
        "ツイン": 14000,
        "スイート": 25000
    }[room_type]
    total_spend = room_rate * nights + random.randint(-5000, 5000)
    total_spend = max(15000, min(200000, total_spend))

    # Satisfaction scores (1.0-5.0)
    overall_score = round(random.uniform(1.0, 5.0), 1)
    room_score = round(random.uniform(1.0, 5.0), 1)
    food_score = round(random.uniform(1.0, 5.0), 1)
    service_score = round(random.uniform(1.0, 5.0), 1)

    # Repeat guest (30% probability)
    is_repeat = random.choice([True, False, False])

    # Channel
    channel = random.choice(["OTA", "直接予約", "旅行代理店", "法人"])

    records.append({
        "stay_date": stay_date.strftime("%Y-%m-%d"),
        "guest_id": guest_id,
        "room_type": room_type,
        "nights": nights,
        "total_spend": int(total_spend),
        "overall_score": overall_score,
        "room_score": room_score,
        "food_score": food_score,
        "service_score": service_score,
        "is_repeat": is_repeat,
        "channel": channel,
    })

df = pd.DataFrame(records)
csv_path = os.path.join(DATA_DIR, "sample_guest_satisfaction.csv")
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"[OK] {csv_path} written ({len(df)} rows)")
