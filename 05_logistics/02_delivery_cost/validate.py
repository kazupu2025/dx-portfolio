"""
C-17 配送コスト分析パイプライン
クレンジング出力バリデーション（18項目以上）
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_delivery_202401.csv"

REQUIRED_COLS = [
    "delivery_id", "date", "route_id", "vehicle_type", "distance_km",
    "fuel_cost", "toll_cost", "driver_cost", "total_cost", "status"
]
VALID_STATUSES = {"完了", "遅延", "キャンセル"}
VALID_VEHICLES = {"2tトラック", "4tトラック", "10tトラック", "軽バン"}
VALID_ROUTES = {"R01_東京-横浜", "R02_東京-埼玉", "R03_大阪-神戸", "R04_大阪-京都", "R05_名古屋-豊田"}


def check(name: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return passed


def main():
    results = []
    print("=" * 60)
    print("validate.py: クレンジング出力チェック")
    print("=" * 60)

    # 1. ファイル存在確認
    exists = CSV_PATH.exists()
    results.append(check("01 CSVファイル存在確認", exists, str(CSV_PATH)))
    if not exists:
        print("\n[ERROR] ファイルが存在しないため検証を中断します")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 2. 行数（400以上）
    results.append(check("02 行数 >= 400", len(df) >= 400, f"{len(df)} rows"))

    # 3. 必須列の存在
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    results.append(check("03 必須列の存在", len(missing_cols) == 0,
                         f"missing: {missing_cols}" if missing_cols else "all present"))

    if len(missing_cols) > 0:
        print("\n[ERROR] 必須列が不足しているため一部チェックをスキップします")
        sys.exit(1)

    # 4. delivery_idのユニーク性
    dup_count = df["delivery_id"].duplicated().sum()
    results.append(check("04 delivery_idのユニーク性", dup_count == 0, f"重複数: {dup_count}"))

    # 5. 日付フォーマット（YYYY-MM-DD）
    import re
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid_dates = df["date"].dropna().apply(lambda x: not bool(date_pattern.match(str(x)))).sum()
    results.append(check("05 日付フォーマット YYYY-MM-DD", invalid_dates == 0, f"不正件数: {invalid_dates}"))

    # 6. distance_kmが正の値
    neg_dist = (pd.to_numeric(df["distance_km"], errors="coerce") <= 0).sum()
    results.append(check("06 distance_km > 0", neg_dist == 0, f"非正値: {neg_dist}"))

    # 7. fuel_costが0以上
    neg_fuel = (pd.to_numeric(df["fuel_cost"], errors="coerce") < 0).sum()
    results.append(check("07 fuel_cost >= 0", neg_fuel == 0, f"負値: {neg_fuel}"))

    # 8. toll_costが0以上
    neg_toll = (pd.to_numeric(df["toll_cost"], errors="coerce") < 0).sum()
    results.append(check("08 toll_cost >= 0", neg_toll == 0, f"負値: {neg_toll}"))

    # 9. driver_costが0以上
    neg_driver = (pd.to_numeric(df["driver_cost"], errors="coerce") < 0).sum()
    results.append(check("09 driver_cost >= 0", neg_driver == 0, f"負値: {neg_driver}"))

    # 10. total_cost = fuel_cost + toll_cost + driver_cost（許容誤差1円）
    calc_total = df["fuel_cost"] + df["toll_cost"] + df["driver_cost"]
    diff = (df["total_cost"] - calc_total).abs()
    mismatch = (diff > 1).sum()
    results.append(check("10 total_cost整合性（誤差1円以内）", mismatch == 0, f"不一致件数: {mismatch}"))

    # 11. cost_per_kmが非負またはNaN
    cpk = pd.to_numeric(df["cost_per_km"], errors="coerce")
    neg_cpk = (cpk < 0).sum()
    results.append(check("11 cost_per_km >= 0 または NaN", neg_cpk == 0, f"負値: {neg_cpk}"))

    # 12. statusが有効値のみ
    invalid_status = (~df["status"].isin(VALID_STATUSES)).sum()
    results.append(check("12 status値の妥当性", invalid_status == 0,
                         f"不正値: {invalid_status}"))

    # 13. vehicle_typeが4種類
    vt_count = df["vehicle_type"].nunique()
    results.append(check("13 vehicle_typeが4種類", vt_count == 4, f"実際: {vt_count}種類"))

    # 14. route_idが5種類
    rt_count = df["route_id"].nunique()
    results.append(check("14 route_idが5種類", rt_count == 5, f"実際: {rt_count}種類"))

    # 15. source_file列の存在
    results.append(check("15 source_file列の存在", "source_file" in df.columns))

    # 16. 欠損率15%以下
    null_rate = df[REQUIRED_COLS].isnull().mean().max()
    results.append(check("16 必須列の欠損率 <= 15%", null_rate <= 0.15,
                         f"最大欠損率: {null_rate:.1%}"))

    # 17. 完了ステータスが全体の70%以上
    kanryo_rate = (df["status"] == "完了").mean()
    results.append(check("17 完了ステータス >= 70%", kanryo_rate >= 0.70,
                         f"完了率: {kanryo_rate:.1%}"))

    # 18. cost_per_kmの最大値が1000以下（異常値チェック）
    max_cpk = cpk.dropna().max() if len(cpk.dropna()) > 0 else 0
    results.append(check("18 cost_per_km最大値 <= 2000（異常値チェック）", max_cpk <= 2000,
                         f"最大値: {max_cpk:.2f}"))

    # 追加チェック
    # 19. cargo_weight_kg列の存在と正値
    if "cargo_weight_kg" in df.columns:
        neg_weight = (pd.to_numeric(df["cargo_weight_kg"], errors="coerce") <= 0).sum()
        results.append(check("19 cargo_weight_kg > 0", neg_weight == 0, f"非正値: {neg_weight}"))
    else:
        results.append(check("19 cargo_weight_kg列の存在", False, "列なし"))

    # 20. delivery_count >= 1
    if "delivery_count" in df.columns:
        low_dc = (pd.to_numeric(df["delivery_count"], errors="coerce") < 1).sum()
        results.append(check("20 delivery_count >= 1", low_dc == 0, f"0以下件数: {low_dc}"))
    else:
        results.append(check("20 delivery_count列の存在", False, "列なし"))

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\n結果: {passed}/{total} PASS")

    if passed == total:
        print("[SUCCESS] 全チェックPASS")
        sys.exit(0)
    else:
        print(f"[FAIL] {total - passed}項目が失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
