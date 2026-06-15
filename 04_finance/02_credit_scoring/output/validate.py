"""
B-11: 与信スコアリング クレンジング結果バリデーション（18チェック）
"""
import sys
from pathlib import Path
import pandas as pd
import yaml

BASE = Path(__file__).parent.parent
OUT = Path(__file__).parent

with open(BASE / "config.yml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

VALID_OCCUPATIONS = {"会社員", "公務員", "自営業", "パート・アルバイト", "無職"}
VALID_RISK_CATEGORIES = {"高リスク", "中リスク", "低リスク"}
REQUIRED_COLS = [
    "application_id", "age", "occupation", "annual_income",
    "years_employed", "total_debt", "past_delays", "loan_amount",
    "loan_purpose", "credit_score", "risk_category",
    "debt_income_ratio", "loan_income_ratio", "score_imputed",
]

results = []


def check(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f": {detail}"
    print(msg)
    results.append((name, passed))
    return passed


def main():
    # 1. CSV存在チェック
    csv_path = OUT / "cleaned_credit_202401.csv"
    if not check("csv_exists", csv_path.exists(), str(csv_path)):
        print("CRITICAL: 出力CSVが存在しません。cleanse.pyを先に実行してください。")
        sys.exit(1)

    # 2. ログ存在チェック
    log_path = OUT / "cleanse.log"
    check("log_exists", log_path.exists(), str(log_path))

    # データ読み込み
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # 3. スキーマチェック
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    check("schema", len(missing_cols) == 0,
          f"不足列: {missing_cols}" if missing_cols else f"全{len(REQUIRED_COLS)}列OK")

    # 4〜8. Null チェック
    check("application_id_nan", df["application_id"].isnull().sum() == 0,
          f"NaN={df['application_id'].isnull().sum()}")
    check("age_nan", df["age"].isnull().sum() == 0,
          f"NaN={df['age'].isnull().sum()}")
    check("occupation_nan", df["occupation"].isnull().sum() == 0,
          f"NaN={df['occupation'].isnull().sum()}")
    check("annual_income_nan", df["annual_income"].isnull().sum() == 0,
          f"NaN={df['annual_income'].isnull().sum()}")
    check("credit_score_nan", df["credit_score"].isnull().sum() == 0,
          f"NaN={df['credit_score'].isnull().sum()}")
    check("risk_category_nan", df["risk_category"].isnull().sum() == 0,
          f"NaN={df['risk_category'].isnull().sum()}")

    # 10. 年齢範囲
    age_ok = df["age"].between(18, 100).all()
    check("age_range", age_ok,
          f"範囲外: {(~df['age'].between(18, 100)).sum()}件")

    # 11. 年収非負
    check("annual_income_nonneg", (df["annual_income"] >= 0).all(),
          f"負値: {(df['annual_income'] < 0).sum()}件")

    # 12. 負債総額非負
    check("total_debt_nonneg", (df["total_debt"] >= 0).all(),
          f"負値: {(df['total_debt'] < 0).sum()}件")

    # 13. 延滞回数非負
    check("past_delays_nonneg", (df["past_delays"] >= 0).all(),
          f"負値: {(df['past_delays'] < 0).sum()}件")

    # 14. スコア範囲 0〜100
    score_ok = df["credit_score"].between(0, 100).all()
    check("credit_score_range", score_ok,
          f"範囲外: {(~df['credit_score'].between(0, 100)).sum()}件")

    # 15. リスク分類値チェック
    invalid_risk = set(df["risk_category"].unique()) - VALID_RISK_CATEGORIES
    check("risk_category_values", len(invalid_risk) == 0,
          f"不正値: {invalid_risk}" if invalid_risk else "全値OK")

    # 16. 職業5種類すべて存在
    present_occupations = set(df["occupation"].unique())
    missing_occ = VALID_OCCUPATIONS - present_occupations
    check("occupation_count", len(missing_occ) == 0,
          f"不足職業: {missing_occ}" if missing_occ else f"{len(present_occupations)}種類OK")

    # 17. 職業値チェック（正規名のみ）
    invalid_occ = present_occupations - VALID_OCCUPATIONS
    check("occupation_values", len(invalid_occ) == 0,
          f"不正値: {invalid_occ}" if invalid_occ else "全値OK")

    # 18. 行数チェック
    n = len(df)
    row_ok = config["min_rows"] <= n <= config["max_rows"]
    check("row_count", row_ok,
          f"{n}行 (想定: {config['min_rows']}〜{config['max_rows']})")

    # --- 結果集計 ---
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'='*40}")
    print(f"バリデーション結果: {passed}/{total} PASS")
    if passed < total:
        failed = [name for name, ok in results if not ok]
        print(f"FAIL項目: {failed}")
    print(f"{'='*40}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
