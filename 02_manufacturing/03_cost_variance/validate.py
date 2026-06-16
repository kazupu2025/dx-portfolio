"""18項目バリデーション"""
import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_production_cost_202401.csv"

CANONICAL_COLS = [
    "product_id","product_name","production_date","line_id",
    "planned_qty","actual_qty","planned_material","actual_material",
    "planned_labor","actual_labor","planned_overhead","actual_overhead",
    "source_file",
    "material_variance","labor_variance","overhead_variance",
    "planned_total_cost","actual_total_cost","total_variance",
    "variance_ratio","qty_variance","variance_flag",
]

checks = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append((name, status, detail))
    return condition

# 1. CSV存在
check("CSV存在", CSV_PATH.exists(), str(CSV_PATH))

if CSV_PATH.exists():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 2. 行数380以上
    check("行数380以上", len(df) >= 380, f"{len(df)}行")

    # 3-14. 必須列の存在
    for col in CANONICAL_COLS:
        check(f"列存在:{col}", col in df.columns)

    # 15. 日付フォーマット
    import re
    bad_dates = df["production_date"].dropna().apply(lambda x: not bool(re.match(r"\d{4}-\d{2}-\d{2}", str(x))))
    check("日付フォーマット", bad_dates.sum() == 0, f"不正:{bad_dates.sum()}件")

    # 16. planned_qty > 0
    check("planned_qty>0", (df["planned_qty"] > 0).all(), f"違反:{( df['planned_qty'] <= 0).sum()}件")

    # 17. actual_qty >= 0
    check("actual_qty>=0", (df["actual_qty"] >= 0).all())

    # 18. planned_material > 0
    check("planned_material>0", (df["planned_material"] > 0).all())

    # 19. planned_labor > 0
    check("planned_labor>0", (df["planned_labor"] > 0).all())

    # 20. planned_overhead > 0
    check("planned_overhead>0", (df["planned_overhead"] > 0).all())

    # 21. actual_material >= 0
    check("actual_material>=0", (df["actual_material"] >= 0).all())

    # 22. actual_labor >= 0
    check("actual_labor>=0", (df["actual_labor"] >= 0).all())

    # 23. actual_overhead >= 0
    check("actual_overhead>=0", (df["actual_overhead"] >= 0).all())

    # 24. total_variance整合性
    calc = df["actual_total_cost"] - df["planned_total_cost"]
    diff = (calc - df["total_variance"]).abs()
    check("total_variance整合性", (diff < 1).all(), f"最大誤差:{diff.max():.4f}")

    # 25. variance_flag値
    valid_flags = {"超過","節約","正常"}
    actual_flags = set(df["variance_flag"].unique())
    check("variance_flag値", actual_flags.issubset(valid_flags), str(actual_flags))

    # 26. line_id 3種類
    check("line_id 3種類", df["line_id"].nunique() == 3, str(df["line_id"].unique()))

    # 27. product_id ユニーク数15以上
    check("product_id>=15種", df["product_id"].nunique() >= 15, f"{df['product_id'].nunique()}種")

    # 28. source_file列存在（再確認）
    check("source_file列", "source_file" in df.columns)

    # 29. 欠損率15%以下
    missing_ratio = df.isnull().mean().max()
    check("欠損率15%以下", missing_ratio <= 0.15, f"最大欠損率:{missing_ratio:.2%}")

# Print results
print("\n=== validate.py 結果 ===")
passed = sum(1 for _, s, _ in checks if s == "PASS")
failed = sum(1 for _, s, _ in checks if s == "FAIL")
for name, status, detail in checks:
    mark = "PASS" if status == "PASS" else "FAIL"
    print(f"  [{mark}] {status} - {name}" + (f" ({detail})" if detail else ""))
print(f"\n合計: {passed}件PASS / {failed}件FAIL")

if failed > 0:
    sys.exit(1)
