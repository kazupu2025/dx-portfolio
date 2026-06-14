import pandas as pd
import numpy as np
import random
from datetime import date, timedelta
from pathlib import Path

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/02_manufacturing/01_quality_inspection")

# 工程定義
processes = ["切削工程", "溶接工程", "塗装工程", "組立工程", "最終検査"]

# 製品定義（工程ごとに担当製品が異なる）
products = {
    "切削工程":   [("P-001", "シャフトA型"),  ("P-002", "シャフトB型"),  ("P-003", "ギアC型")],
    "溶接工程":   [("P-004", "フレームX"),     ("P-005", "フレームY"),    ("P-006", "ブラケット")],
    "塗装工程":   [("P-007", "パネルS"),       ("P-008", "カバーT"),      ("P-009", "ハウジング")],
    "組立工程":   [("P-010", "アセンブリA"),   ("P-011", "アセンブリB"),  ("P-012", "ユニットC")],
    "最終検査":   [("P-013", "完成品α"),       ("P-014", "完成品β"),      ("P-015", "完成品γ")],
}

# 工程ごとの検査規格（中心値, 標準偏差, 下限, 上限, 単位）
specs = {
    "切削工程":  (50.0, 0.5,  49.0, 51.0,  "mm"),
    "溶接工程":  (200.0, 3.0, 192.0, 208.0, "N"),
    "塗装工程":  (80.0, 2.0,  75.0, 85.0,  "μm"),
    "組立工程":  (10.0, 0.2,  9.5,  10.5,  "Nm"),
    "最終検査":  (100.0, 1.5, 96.5, 103.5, "%"),
}

inspectors = ["田中", "鈴木", "佐藤", "山田", "中村"]

def business_days(year=2024, month=1):
    days = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days

bdays = business_days()


def gen_rows(process: str, n_per_day: int, col_style: str) -> list:
    mu, sigma, lo, hi, unit = specs[process]
    prods = products[process]
    rows = []
    for d in bdays:
        for _ in range(n_per_day):
            pcode, pname = random.choice(prods)
            lot_no = f"LOT-{d.strftime('%Y%m%d')}-{random.randint(100,999)}"
            inspector = random.choice(inspectors)

            # 通常分布（5%確率で3σ超の異常値を混入）
            if rng.random() < 0.05:
                value = mu + rng.choice([-1, 1]) * rng.uniform(3.2 * sigma, 5.0 * sigma)
            else:
                value = rng.normal(mu, sigma)

            value = round(float(value), 3)
            result_str = "OK" if lo <= value <= hi else "NG"
            date_str = d.strftime("%Y/%m/%d")

            if col_style == "standard":
                rows.append({
                    "日付": date_str, "製品コード": pcode, "製品名": pname,
                    "工程": process, "ロットNo": lot_no, "検査値": value,
                    "下限値": lo, "上限値": hi, "単位": unit,
                    "検査員": inspector, "判定": result_str,
                })
            elif col_style == "english":
                rows.append({
                    "Date": date_str, "ProductCode": pcode, "ProductName": pname,
                    "Process": process, "LotNo": lot_no, "InspectionValue": value,
                    "LowerLimit": lo, "UpperLimit": hi, "Unit": unit,
                    "Inspector": inspector, "Result": result_str,
                })
            else:  # variant
                rows.append({
                    "検査日": date_str, "品番": pcode, "製品": pname,
                    "工程名": process, "ロット番号": lot_no, "計測値": value,
                    "規格下限": lo, "規格上限": hi, "単位": unit,
                    "担当者": inspector, "合否": result_str,
                })
    return rows


files_config = [
    ("切削工程", "standard", "01_切削工程_検査_202401.csv",  5),
    ("溶接工程", "english",  "02_溶接工程_inspection_202401.csv", 5),
    ("塗装工程", "variant",  "03_塗装工程_検査_202401.csv",  4),
    ("組立工程", "standard", "04_組立工程_検査_202401.csv",  5),
    ("最終検査", "standard", "05_最終検査_検査_202401.csv",  4),
]

for process, style, filename, n_per_day in files_config:
    rows = gen_rows(process, n_per_day, style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print(f"\nサンプルデータ生成完了（{len(bdays)}営業日 × 5工程）")
