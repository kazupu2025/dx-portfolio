"""
B-09 クレンジング結果バリデーション (18チェック)
Usage: cd 02_manufacturing/02_equipment_log && python output/validate.py
"""
import sys
import pandas as pd
import yaml
from pathlib import Path

BASE = Path(__file__).parent.parent
OUT  = Path(__file__).parent

KEEP_COLS = ["timestamp", "equipment_id", "equipment_name",
             "temperature", "vibration", "pressure", "rpm",
             "op_status", "is_operating", "source_file"]

def run():
    with open(BASE / "config.yml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    results = []

    # 1. csv_exists
    csv_path = OUT / "cleaned_sensor_202401.csv"
    ok = csv_path.exists()
    results.append(("1", "csv_exists", ok, "" if ok else f"{csv_path} が存在しない"))

    # 2. log_exists
    log_path = OUT / "cleanse.log"
    ok = log_path.exists()
    results.append(("2", "log_exists", ok, "" if ok else f"{log_path} が存在しない"))

    if not csv_path.exists():
        for i, name in enumerate([
            "schema","timestamp_nan","equipment_id_nan","temperature_nan","vibration_nan",
            "pressure_nan","rpm_nan","timestamp_format","timestamp_range",
            "temperature_nonneg","vibration_nonneg","pressure_nonneg","rpm_nonneg",
            "op_status_values","equipment_count","row_count"
        ], 3):
            results.append((str(i), name, False, "cleaned_sensor_202401.csv が存在しない"))
        print_results(results)
        return

    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # 3. schema
    missing = [c for c in KEEP_COLS if c not in df.columns]
    ok = len(missing) == 0
    results.append(("3", "schema", ok, "" if ok else f"不足列: {missing}"))

    # 4. timestamp_nan
    ok = df["timestamp"].isna().sum() == 0 if "timestamp" in df.columns else False
    results.append(("4", "timestamp_nan", ok, "" if ok else f"timestamp NaN: {df['timestamp'].isna().sum()}"))

    # 5. equipment_id_nan
    ok = df["equipment_id"].isna().sum() == 0 if "equipment_id" in df.columns else False
    results.append(("5", "equipment_id_nan", ok, "" if ok else f"equipment_id NaN: {df['equipment_id'].isna().sum()}"))

    # 6. temperature_nan
    ok = df["temperature"].isna().sum() == 0 if "temperature" in df.columns else False
    results.append(("6", "temperature_nan", ok, "" if ok else f"temperature NaN: {df['temperature'].isna().sum()}"))

    # 7. vibration_nan
    ok = df["vibration"].isna().sum() == 0 if "vibration" in df.columns else False
    results.append(("7", "vibration_nan", ok, "" if ok else f"vibration NaN: {df['vibration'].isna().sum()}"))

    # 8. pressure_nan
    ok = df["pressure"].isna().sum() == 0 if "pressure" in df.columns else False
    results.append(("8", "pressure_nan", ok, "" if ok else f"pressure NaN: {df['pressure'].isna().sum()}"))

    # 9. rpm_nan
    ok = df["rpm"].isna().sum() == 0 if "rpm" in df.columns else False
    results.append(("9", "rpm_nan", ok, "" if ok else f"rpm NaN: {df['rpm'].isna().sum()}"))

    # 10. timestamp_format
    if "timestamp" in df.columns:
        import re
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
        bad = df["timestamp"].dropna().apply(lambda v: not bool(pattern.match(str(v)))).sum()
        ok = bad == 0
        results.append(("10", "timestamp_format", ok, "" if ok else f"形式不正 {bad} 件"))
    else:
        results.append(("10", "timestamp_format", False, "timestamp列なし"))

    # 11. timestamp_range
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
        ok = ((ts.dt.year == 2024) & (ts.dt.month == 1)).all()
        results.append(("11", "timestamp_range", ok, "" if ok else "2024-01以外のデータあり"))
    else:
        results.append(("11", "timestamp_range", False, "timestamp列なし"))

    # 12. temperature_nonneg
    if "temperature" in df.columns:
        ok = (df["temperature"] >= 0).all()
        results.append(("12", "temperature_nonneg", ok, "" if ok else "temperature に負の値あり"))
    else:
        results.append(("12", "temperature_nonneg", False, "temperature列なし"))

    # 13. vibration_nonneg
    if "vibration" in df.columns:
        ok = (df["vibration"] >= 0).all()
        results.append(("13", "vibration_nonneg", ok, "" if ok else "vibration に負の値あり"))
    else:
        results.append(("13", "vibration_nonneg", False, "vibration列なし"))

    # 14. pressure_nonneg
    if "pressure" in df.columns:
        ok = (df["pressure"] >= 0).all()
        results.append(("14", "pressure_nonneg", ok, "" if ok else "pressure に負の値あり"))
    else:
        results.append(("14", "pressure_nonneg", False, "pressure列なし"))

    # 15. rpm_nonneg
    if "rpm" in df.columns:
        ok = (df["rpm"] >= 0).all()
        results.append(("15", "rpm_nonneg", ok, "" if ok else "rpm に負の値あり"))
    else:
        results.append(("15", "rpm_nonneg", False, "rpm列なし"))

    # 16. op_status_values
    if "op_status" in df.columns:
        invalid = ~df["op_status"].isin([0, 1])
        ok = invalid.sum() == 0
        results.append(("16", "op_status_values", ok, "" if ok else f"0/1以外の値: {invalid.sum()} 件"))
    else:
        results.append(("16", "op_status_values", False, "op_status列なし"))

    # 17. equipment_count
    if "equipment_id" in df.columns:
        count = df["equipment_id"].nunique()
        expected = config.get("expected_equipment_count", 5)
        ok = count == expected
        results.append(("17", "equipment_count", ok, "" if ok else f"設備数: {count} (期待: {expected})"))
    else:
        results.append(("17", "equipment_count", False, "equipment_id列なし"))

    # 18. row_count
    min_r = config.get("min_rows", 3000)
    max_r = config.get("max_rows", 5000)
    ok = min_r <= len(df) <= max_r
    results.append(("18", "row_count", ok, "" if ok else f"行数: {len(df)} (期待: {min_r}〜{max_r})"))

    print_results(results)


def print_results(results):
    passed = sum(1 for _, _, ok, _ in results if ok)
    total  = len(results)
    print(f"\n=== バリデーション結果: {passed}/{total} PASS ===")
    for no, name, ok, msg in results:
        status = "PASS" if ok else "FAIL"
        detail = f" ({msg})" if msg else ""
        print(f"  [{status}] {no:>2}. {name}{detail}")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    run()
