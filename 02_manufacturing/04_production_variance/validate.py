# -*- coding: utf-8 -*-
"""
C-25: 生産計画 vs 実績 差異分析パイプライン
クレンジング出力バリデーション（18項目チェック）
"""
import sys
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_CSV = OUTPUT_DIR / "cleaned_production_202401.csv"

EXPECTED_LINES = {"LINE-A", "LINE-B", "LINE-C", "LINE-D", "LINE-E"}
EXPECTED_CATEGORIES = {"電子部品", "機械部品", "樹脂成型", "金属加工"}
REQUIRED_COLS = [
    "date", "line_name", "category",
    "planned_qty", "actual_qty", "defect_qty", "work_hours",
    "achievement_rate", "defect_rate", "variance_qty", "achievement_flag",
]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return condition


def validate() -> bool:
    results = []

    # 1. CSVファイル存在確認
    results.append(check("CSV存在確認", CLEANED_CSV.exists(), str(CLEANED_CSV)))
    if not CLEANED_CSV.exists():
        print("[FAIL] CSVが存在しないため、以降のチェックをスキップします。")
        return False

    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")

    # 2. 行数 >= 400
    results.append(check("行数 >= 400", len(df) >= 400, f"actual={len(df)}"))

    # 3. 必須列の存在
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    results.append(check("必須列の存在（11列）", len(missing) == 0, f"missing={missing}"))

    # 4. 日付フォーマット YYYY-MM-DD
    invalid_dates = df["date"].dropna().apply(lambda x: not bool(DATE_PATTERN.match(str(x))))
    results.append(check("日付フォーマット YYYY-MM-DD", not invalid_dates.any(),
                          f"invalid_count={invalid_dates.sum()}"))

    # 5. line_nameが5種類（LINE-A〜LINE-E）
    actual_lines = set(df["line_name"].dropna().unique())
    results.append(check("line_name 5種類", actual_lines == EXPECTED_LINES,
                          f"actual={actual_lines}"))

    # 6. categoryが4種類
    actual_cats = set(df["category"].dropna().unique())
    results.append(check("category 4種類", actual_cats == EXPECTED_CATEGORIES,
                          f"actual={actual_cats}"))

    # 7. planned_qty > 0（全行）
    valid_planned = (df["planned_qty"] > 0).all()
    results.append(check("planned_qty > 0（全行）", valid_planned,
                          f"non_positive_count={(df['planned_qty'] <= 0).sum()}"))

    # 8. actual_qty >= 0（全行）
    valid_actual = (df["actual_qty"] >= 0).all()
    results.append(check("actual_qty >= 0（全行）", valid_actual,
                          f"negative_count={(df['actual_qty'] < 0).sum()}"))

    # 9. defect_qty >= 0（全行）
    valid_defect = (df["defect_qty"] >= 0).all()
    results.append(check("defect_qty >= 0（全行）", valid_defect,
                          f"negative_count={(df['defect_qty'] < 0).sum()}"))

    # 10. defect_qty <= actual_qty（整合性）
    defect_over = (df["defect_qty"] > df["actual_qty"]).sum()
    results.append(check("defect_qty <= actual_qty", defect_over == 0,
                          f"violation_count={defect_over}"))

    # 11. achievement_rate >= 0（非負）
    ar = df["achievement_rate"].dropna()
    results.append(check("achievement_rate >= 0", (ar >= 0).all(),
                          f"negative_count={(ar < 0).sum()}"))

    # 12. defect_rate >= 0 かつ <= 1
    dr = df["defect_rate"].dropna()
    valid_dr = ((dr >= 0) & (dr <= 1)).all()
    results.append(check("defect_rate in [0,1]", valid_dr,
                          f"out_of_range={(~((dr >= 0) & (dr <= 1))).sum()}"))

    # 13. variance_qty = actual_qty - planned_qty（整合性チェック、許容誤差0.01）
    diff = (df["variance_qty"] - (df["actual_qty"] - df["planned_qty"])).abs()
    variance_ok = (diff <= 0.01).all()
    results.append(check("variance_qty整合性（誤差<=0.01）", variance_ok,
                          f"mismatch_count={(diff > 0.01).sum()}"))

    # 14. achievement_flagが"達成"/"未達"のみ
    valid_flags = {"達成", "未達"}
    actual_flags = set(df["achievement_flag"].dropna().unique())
    results.append(check('achievement_flag値域（"達成"/"未達"）',
                          actual_flags.issubset(valid_flags),
                          f"actual={actual_flags}"))

    # 15. work_hours > 0
    valid_wh = (df["work_hours"] > 0).all()
    results.append(check("work_hours > 0", valid_wh,
                          f"non_positive_count={(df['work_hours'] <= 0).sum()}"))

    # 16. source_file列の存在
    results.append(check("source_file列の存在", "source_file" in df.columns))

    # 17. 欠損率 <= 15%
    null_rate = df.isnull().mean().max()
    results.append(check("欠損率 <= 15%", null_rate <= 0.15,
                          f"max_null_rate={null_rate:.2%}"))

    # 18. source_fileが3種類（3ファイル）
    if "source_file" in df.columns:
        n_sources = df["source_file"].nunique()
        results.append(check("source_file 3種類", n_sources == 3,
                              f"actual={n_sources}"))
    else:
        results.append(check("source_file 3種類", False, "source_file列なし"))

    passed = sum(results)
    total = len(results)
    print(f"\n[RESULT] {passed}/{total} checks passed")
    return passed == total


if __name__ == "__main__":
    ok = validate()
    sys.exit(0 if ok else 1)
