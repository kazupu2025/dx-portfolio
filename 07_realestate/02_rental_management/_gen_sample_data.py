import pandas as pd
import numpy as np
import random
from pathlib import Path

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/07_realestate/02_rental_management")

areas = ["渋谷区", "新宿区", "港区", "世田谷区", "品川区"]
types = ["1K", "1DK", "1LDK", "2LDK", "3LDK"]

rent_map = {
    ("渋谷区",  "1K"):   (80000, 120000),
    ("渋谷区",  "1DK"):  (100000, 150000),
    ("渋谷区",  "1LDK"): (130000, 200000),
    ("渋谷区",  "2LDK"): (180000, 280000),
    ("渋谷区",  "3LDK"): (250000, 400000),
    ("新宿区",  "1K"):   (75000, 110000),
    ("新宿区",  "1DK"):  (90000, 140000),
    ("新宿区",  "1LDK"): (120000, 180000),
    ("新宿区",  "2LDK"): (160000, 250000),
    ("新宿区",  "3LDK"): (220000, 350000),
    ("港区",    "1K"):   (90000, 140000),
    ("港区",    "1DK"):  (120000, 170000),
    ("港区",    "1LDK"): (150000, 230000),
    ("港区",    "2LDK"): (200000, 320000),
    ("港区",    "3LDK"): (280000, 450000),
    ("世田谷区","1K"):   (65000, 100000),
    ("世田谷区","1DK"):  (80000, 120000),
    ("世田谷区","1LDK"): (100000, 160000),
    ("世田谷区","2LDK"): (140000, 220000),
    ("世田谷区","3LDK"): (180000, 300000),
    ("品川区",  "1K"):   (70000, 105000),
    ("品川区",  "1DK"):  (85000, 130000),
    ("品川区",  "1LDK"): (110000, 170000),
    ("品川区",  "2LDK"): (150000, 240000),
    ("品川区",  "3LDK"): (200000, 330000),
}

def gen_property(prop_id: str, area: str, prop_type: str, style: str) -> dict:
    rent_lo, rent_hi = rent_map.get((area, prop_type), (80000, 200000))
    rent = int(rng.integers(rent_lo, rent_hi) // 1000 * 1000)
    mgmt_fee = int(rent * rng.uniform(0.03, 0.08) // 500 * 500)
    mgmt_cost = int(rng.integers(5000, 25000))
    repair_cost = 0
    if rng.random() < 0.15:
        repair_cost = int(rng.integers(30000, 200000))

    vacancy_prob = {"渋谷区": 0.12, "新宿区": 0.15, "港区": 0.10, "世田谷区": 0.22, "品川区": 0.18}.get(area, 0.15)
    r = rng.random()
    if r < vacancy_prob * 0.5:
        status_std = "空室"; status_eng = "Vacant"; status_var = "空き"
        move_in = ""; move_out = "2024/01/10"
    elif r < vacancy_prob:
        status_std = "募集中"; status_eng = "ForRent"; status_var = "募集"
        move_in = ""; move_out = "2024/01/20"
    else:
        status_std = "入居中"; status_eng = "Occupied"; status_var = "居住中"
        move_in = f"202{rng.integers(1,4)}/{rng.integers(1,12):02d}/01"
        move_out = ""

    name = f"{area[0:2]}-{prop_type}-{prop_id[-3:]}"

    if style == "standard":
        return {
            "物件ID": prop_id, "物件名": name, "エリア": area, "物件タイプ": prop_type,
            "賃料(円)": rent, "管理費(円)": mgmt_fee, "入居状況": status_std,
            "入居開始日": move_in, "退去日": move_out,
            "管理コスト(円)": mgmt_cost, "修繕費(円)": repair_cost,
        }
    elif style == "english":
        return {
            "PropertyID": prop_id, "PropertyName": name, "Area": area, "PropertyType": prop_type,
            "Rent": rent, "ManagementFee": mgmt_fee, "OccupancyStatus": status_eng,
            "MoveInDate": move_in, "MoveOutDate": move_out,
            "ManagementCost": mgmt_cost, "RepairCost": repair_cost,
        }
    else:
        return {
            "物件番号": prop_id, "物件名称": name, "地域": area, "タイプ": prop_type,
            "月額賃料": rent, "管理費": mgmt_fee, "状態": status_var,
            "入居日": move_in, "退去日": move_out,
            "管理費用": mgmt_cost, "修繕費用": repair_cost,
        }

area_style = {
    "渋谷区":  ("standard", "01_渋谷区_物件_202401.csv"),
    "新宿区":  ("english",  "02_shinjuku_properties_202401.csv"),
    "港区":    ("standard", "03_港区_物件_202401.csv"),
    "世田谷区":("variant",  "04_世田谷区_物件_202401.csv"),
    "品川区":  ("variant",  "05_品川区_物件_202401.csv"),
}

for area, (style, filename) in area_style.items():
    rows = []
    n = random.randint(40, 60)
    for i in range(1, n+1):
        prop_type = random.choice(types)
        prop_id = f"P-{area[0]}{i:04d}"
        rows.append(gen_property(prop_id, area, prop_type, style))
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("サンプルデータ生成完了（5エリア）")
