"""18項目バリデーション - cleaned_worker_202401.csv"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_worker_202401.csv"

CANONICAL_COLS = [
    "work_date", "worker_id", "line", "process",
    "production_qty", "defect_qty", "work_hours", "overtime_hours",
    "defect_rate", "productivity", "performance_flag", "source_file",
]

checks = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append((name, status, detail))
    return condition


# 1. CSVファイル存在確認
check("CSV存在", CSV_PATH.exists(), str(CSV_PATH))

if CSV_PATH.exists():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 2. 行数 >= 400
    check("行数400以上", len(df) >= 400, f"{len(df)}行")

    # 3. 必須列の存在
    for col in CANONICAL_COLS:
        check(f"列存在:{col}", col in df.columns)

    # 4. 日付フォーマット YYYY-MM-DD
    bad_dates = df["work_date"].dropna().apply(
        lambda x: not bool(re.match(r"\d{4}-\d{2}-\d{2}", str(x)))
    )
    check("日付フォーマット", bad_dates.sum() == 0, f"不正:{bad_dates.sum()}件")

    # 5. worker_idが20種類以上
    check("worker_id>=20種", df["worker_id"].nunique() >= 20, f"{df['worker_id'].nunique()}種")

    # 6. lineが4種類
    check("line 4種類", df["line"].nunique() == 4, str(df["line"].unique().tolist()))

    # 7. processが4種類
    check("process 4種類", df["process"].nunique() == 4, str(df["process"].unique().tolist()))

    # 8. production_qty > 0
    check("production_qty>0", (df["production_qty"] > 0).all(),
          f"違反:{(df['production_qty'] <= 0).sum()}件")

    # 9. defect_qty >= 0
    check("defect_qty>=0", (df["defect_qty"] >= 0).all(),
          f"違反:{(df['defect_qty'] < 0).sum()}件")

    # 10. defect_qty <= production_qty
    check("defect_qty<=production_qty",
          (df["defect_qty"] <= df["production_qty"]).all(),
          f"違反:{(df['defect_qty'] > df['production_qty']).sum()}件")

    # 11. work_hours > 0
    check("work_hours>0", (df["work_hours"] > 0).all(),
          f"違反:{(df['work_hours'] <= 0).sum()}件")

    # 12. overtime_hours >= 0
    check("overtime_hours>=0", (df["overtime_hours"] >= 0).all(),
          f"違反:{(df['overtime_hours'] < 0).sum()}件")

    # 13. defect_rateが0~1の範囲
    valid_dr = df["defect_rate"].dropna()
    check("defect_rate範囲0-1",
          ((valid_dr >= 0) & (valid_dr <= 1)).all(),
          f"違反:{((valid_dr < 0) | (valid_dr > 1)).sum()}件")

    # 14. productivity > 0（またはNaN）
    valid_prod = df["productivity"].dropna()
    check("productivity>0またはNaN",
          (valid_prod > 0).all(),
          f"違反:{(valid_prod <= 0).sum()}件")

    # 15. performance_flagが"高生産性"/"低生産性"のみ
    valid_flags = {"高生産性", "低生産性"}
    actual_flags = set(df["performance_flag"].dropna().unique())
    check("performance_flag値", actual_flags.issubset(valid_flags), str(actual_flags))

    # 16. source_file列の存在
    check("source_file列存在", "source_file" in df.columns)

    # 17. 欠損率 <= 15%
    missing_ratio = df.isnull().mean().max()
    check("欠損率15%以下", missing_ratio <= 0.15, f"最大欠損率:{missing_ratio:.2%}")

    # 18. source_fileが3種類
    check("source_file 3種類", df["source_file"].nunique() == 3,
          f"{df['source_file'].nunique()}種: {df['source_file'].unique().tolist()}")

# Print results
print("\n=== validate.py 結果 ===")
passed = sum(1 for _, s, _ in checks if s == "PASS")
failed = sum(1 for _, s, _ in checks if s == "FAIL")
for name, status, detail in checks:
    mark = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"  {mark} {name}" + (f" ({detail})" if detail else ""))
print(f"\n合計: {passed}件PASS / {failed}件FAIL")

if failed > 0:
    sys.exit(1)
