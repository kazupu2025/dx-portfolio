# -*- coding: utf-8 -*-
"""
クレンジング後データのバリデーションスクリプト
18項目チェックを実施する
"""
import pandas as pd
import numpy as np
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_CSV = OUTPUT_DIR / "cleaned_route_202401.csv"


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "[PASS]" if passed else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return passed


def run_validation() -> bool:
    results = []

    # 1. CSVファイル存在確認
    exists = CLEANED_CSV.exists()
    results.append(check("01. CSVファイル存在確認", exists, str(CLEANED_CSV)))
    if not exists:
        print("[ERROR] CSVファイルが存在しないため以降のチェックをスキップします。")
        return False

    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")

    # 2. 行数 >= 400
    row_count = len(df)
    results.append(check("02. 行数 >= 400", row_count >= 400, f"行数={row_count}"))

    # 3. 必須列の存在
    required_cols = [
        "date", "route_id", "area", "vehicle_type",
        "distance_km", "duration_min", "fuel_cost",
        "delivery_count", "delay_flag",
        "cost_per_km", "cost_per_delivery", "km_per_delivery", "efficiency_flag"
    ]
    missing_cols = [c for c in required_cols if c not in df.columns]
    results.append(check("03. 必須列の存在", len(missing_cols) == 0, f"不足列={missing_cols}"))

    # 4. 日付フォーマット YYYY-MM-DD
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if "date" in df.columns:
        bad_dates = df["date"].dropna().apply(lambda x: not date_pattern.match(str(x))).sum()
        results.append(check("04. 日付フォーマット YYYY-MM-DD", bad_dates == 0, f"不正件数={bad_dates}"))
    else:
        results.append(check("04. 日付フォーマット YYYY-MM-DD", False, "date列なし"))

    # 5. route_idが10種類
    if "route_id" in df.columns:
        route_count = df["route_id"].nunique()
        results.append(check("05. route_idが10種類", route_count == 10, f"種類数={route_count}"))
    else:
        results.append(check("05. route_idが10種類", False, "route_id列なし"))

    # 6. areaが5種類
    if "area" in df.columns:
        area_count = df["area"].nunique()
        results.append(check("06. areaが5種類", area_count == 5, f"種類数={area_count}"))
    else:
        results.append(check("06. areaが5種類", False, "area列なし"))

    # 7. vehicle_typeが3種類
    if "vehicle_type" in df.columns:
        vt_count = df["vehicle_type"].nunique()
        results.append(check("07. vehicle_typeが3種類", vt_count == 3, f"種類数={vt_count}"))
    else:
        results.append(check("07. vehicle_typeが3種類", False, "vehicle_type列なし"))

    # 8. distance_km > 0
    if "distance_km" in df.columns:
        bad_dist = (pd.to_numeric(df["distance_km"], errors="coerce") <= 0).sum()
        results.append(check("08. distance_km > 0", bad_dist == 0, f"違反件数={bad_dist}"))
    else:
        results.append(check("08. distance_km > 0", False, "distance_km列なし"))

    # 9. duration_min > 0
    if "duration_min" in df.columns:
        bad_dur = (pd.to_numeric(df["duration_min"], errors="coerce") <= 0).sum()
        results.append(check("09. duration_min > 0", bad_dur == 0, f"違反件数={bad_dur}"))
    else:
        results.append(check("09. duration_min > 0", False, "duration_min列なし"))

    # 10. fuel_cost > 0
    if "fuel_cost" in df.columns:
        bad_fuel = (pd.to_numeric(df["fuel_cost"], errors="coerce") <= 0).sum()
        results.append(check("10. fuel_cost > 0", bad_fuel == 0, f"違反件数={bad_fuel}"))
    else:
        results.append(check("10. fuel_cost > 0", False, "fuel_cost列なし"))

    # 11. delivery_count > 0
    if "delivery_count" in df.columns:
        bad_del = (pd.to_numeric(df["delivery_count"], errors="coerce") <= 0).sum()
        results.append(check("11. delivery_count > 0", bad_del == 0, f"違反件数={bad_del}"))
    else:
        results.append(check("11. delivery_count > 0", False, "delivery_count列なし"))

    # 12. delay_flagが0または1のみ
    if "delay_flag" in df.columns:
        valid_flags = df["delay_flag"].isin([0, 1])
        bad_flags = (~valid_flags).sum()
        results.append(check("12. delay_flagが0/1のみ", bad_flags == 0, f"違反件数={bad_flags}"))
    else:
        results.append(check("12. delay_flagが0/1のみ", False, "delay_flag列なし"))

    # 13. cost_per_kmが非負（またはNaN）
    if "cost_per_km" in df.columns:
        cpk = pd.to_numeric(df["cost_per_km"], errors="coerce")
        negative_cpk = (cpk < 0).sum()
        results.append(check("13. cost_per_kmが非負またはNaN", negative_cpk == 0, f"負値件数={negative_cpk}"))
    else:
        results.append(check("13. cost_per_kmが非負またはNaN", False, "cost_per_km列なし"))

    # 14. cost_per_deliveryが非負（またはNaN）
    if "cost_per_delivery" in df.columns:
        cpd = pd.to_numeric(df["cost_per_delivery"], errors="coerce")
        negative_cpd = (cpd < 0).sum()
        results.append(check("14. cost_per_deliveryが非負またはNaN", negative_cpd == 0, f"負値件数={negative_cpd}"))
    else:
        results.append(check("14. cost_per_deliveryが非負またはNaN", False, "cost_per_delivery列なし"))

    # 15. efficiency_flagが"高効率"/"低効率"のみ
    if "efficiency_flag" in df.columns:
        valid_eff = df["efficiency_flag"].isin(["高効率", "低効率"])
        bad_eff = (~valid_eff).sum()
        results.append(check("15. efficiency_flagが高効率/低効率のみ", bad_eff == 0, f"違反件数={bad_eff}"))
    else:
        results.append(check("15. efficiency_flagが高効率/低効率のみ", False, "efficiency_flag列なし"))

    # 16. 遅延件数 >= 1
    if "delay_flag" in df.columns:
        delay_count = (df["delay_flag"] == 1).sum()
        results.append(check("16. 遅延件数 >= 1", delay_count >= 1, f"遅延件数={delay_count}"))
    else:
        results.append(check("16. 遅延件数 >= 1", False, "delay_flag列なし"))

    # 17. source_file列の存在
    has_source = "source_file" in df.columns
    results.append(check("17. source_file列の存在", has_source))

    # 18. 欠損率 <= 15%
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = df.isnull().sum().sum()
    missing_rate = missing_cells / total_cells if total_cells > 0 else 0
    results.append(check("18. 欠損率 <= 15%", missing_rate <= 0.15, f"欠損率={missing_rate:.2%}"))

    # サマリー
    pass_count = sum(results)
    total_count = len(results)
    print(f"\n[SUMMARY] {pass_count}/{total_count} チェック通過")

    all_passed = all(results)
    if all_passed:
        print("[VALIDATE] 全チェック通過")
    else:
        print("[VALIDATE] 一部チェック失敗")
    return all_passed


if __name__ == "__main__":
    ok = run_validation()
    sys.exit(0 if ok else 1)
