# -*- coding: utf-8 -*-
"""18項目バリデーション - cleaned_deliveries_202401.csv"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_deliveries_202401.csv"

CANONICAL_COLS = [
    "delivery_date", "delivery_id", "delivery_type", "area", "vehicle_type",
    "delivery_charge", "fuel_cost", "driver_cost", "other_cost", "distance_km",
    "total_cost", "gross_profit", "profit_margin", "cost_per_km",
    "margin_grade", "source_file",
]

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    return condition


# 1. CSVファイル存在確認
check("CSV存在", CSV_PATH.exists(), str(CSV_PATH))

if CSV_PATH.exists():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 2. 行数 >= 420
    check("行数420以上", len(df) >= 420, f"{len(df)}行")

    # 3. 必須列の存在
    for col in CANONICAL_COLS:
        check(f"列存在:{col}", col in df.columns)

    # 4. 日付フォーマット YYYY-MM-DD
    bad_dates = df["delivery_date"].dropna().apply(
        lambda x: not bool(re.match(r"\d{4}-\d{2}-\d{2}", str(x)))
    )
    check("日付フォーマット", bad_dates.sum() == 0, f"不正:{bad_dates.sum()}件")

    # 5. delivery_id 一意性
    check("delivery_id一意性", df["delivery_id"].nunique() == len(df),
          f"重複:{len(df) - df['delivery_id'].nunique()}件")

    # 6. delivery_type 4種類
    check("delivery_type 4種類", df["delivery_type"].nunique() == 4,
          str(sorted(df["delivery_type"].unique().tolist())))

    # 7. area 5種類
    check("area 5種類", df["area"].nunique() == 5,
          str(sorted(df["area"].unique().tolist())))

    # 8. vehicle_type 3種類
    check("vehicle_type 3種類", df["vehicle_type"].nunique() == 3,
          str(sorted(df["vehicle_type"].unique().tolist())))

    # 9. delivery_charge > 0
    check("delivery_charge>0", (df["delivery_charge"] > 0).all(),
          f"違反:{(df['delivery_charge'] <= 0).sum()}件")

    # 10. fuel_cost >= 0
    check("fuel_cost>=0", (df["fuel_cost"] >= 0).all(),
          f"違反:{(df['fuel_cost'] < 0).sum()}件")

    # 11. driver_cost > 0
    check("driver_cost>0", (df["driver_cost"] > 0).all(),
          f"違反:{(df['driver_cost'] <= 0).sum()}件")

    # 12. distance_km > 0
    check("distance_km>0", (df["distance_km"] > 0).all(),
          f"違反:{(df['distance_km'] <= 0).sum()}件")

    # 13. gross_profit 計算整合性
    computed_gp = df["delivery_charge"] - (df["fuel_cost"] + df["driver_cost"] + df["other_cost"])
    diff = (df["gross_profit"] - computed_gp).abs()
    check("gross_profit計算整合性", (diff < 0.01).all(),
          f"不整合:{(diff >= 0.01).sum()}件")

    # 14. profit_margin <= 1 (配送料を超える利益は発生しない)
    valid_pm = df["profit_margin"].dropna()
    check("profit_margin<=1 (利益率が100%以下)",
          (valid_pm <= 1).all(),
          f"違反:{(valid_pm > 1).sum()}件")

    # 15. margin_grade 3種類
    valid_grades = {"高利益", "普通", "低利益"}
    actual_grades = set(df["margin_grade"].dropna().unique())
    check("margin_grade 3種類", actual_grades.issubset(valid_grades),
          str(actual_grades))

    # 16. 欠損率 <= 15%
    missing_ratio = df.isnull().mean().max()
    check("欠損率15%以下", missing_ratio <= 0.15, f"最大欠損率:{missing_ratio:.2%}")

    # 17. source_file 3種類
    check("source_file 3種類", df["source_file"].nunique() == 3,
          f"{df['source_file'].nunique()}種: {df['source_file'].unique().tolist()}")

    # 18. 高利益件数 >= 1
    high_profit_count = (df["margin_grade"] == "高利益").sum()
    check("高利益件数>=1", high_profit_count >= 1, f"高利益:{high_profit_count}件")

# Print results
print("\n=== validate.py 結果 ===")
total = len(results)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
for name, status, detail in results:
    mark = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {mark} {name}" + (f" ({detail})" if detail else ""))
print(f"\nResult: {passed}/{total} checks passed")

if failed > 0:
    sys.exit(1)
