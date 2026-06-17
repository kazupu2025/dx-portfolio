# validate.py — クレンジング済みCSVのバリデーション（C-36 顧客満足度）
# encoding: utf-8

import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
CLEANED_FILE = OUTPUT_DIR / "cleaned_satisfaction_202401.csv"

REQUIRED_COLS = [
    "response_date", "customer_code", "service_type", "agent",
    "overall_sat", "response_speed", "quality", "cost_perf", "nps",
    "csat_score", "nps_category", "satisfaction_flag", "source_file",
]

EXPECTED_SERVICE_TYPES = {"ITサポート", "コンサルティング", "保守", "導入支援", "研修"}
EXPECTED_AGENTS = {"田中", "佐藤", "鈴木", "高橋", "伊藤"}
EXPECTED_NPS_CATEGORIES = {"推奨者", "中立者", "批判者"}
EXPECTED_SAT_FLAGS = {"満足", "普通", "不満"}
MIN_ROWS = 400
MAX_MISSING_RATIO = 0.15
MIN_SOURCE_STYLES = 3


def _check(label: str, condition: bool, detail: str = "") -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    return condition


def run() -> bool:
    results = []

    # 1. ファイル存在確認
    exists = CLEANED_FILE.exists()
    results.append(_check("1. CSVファイル存在確認", exists, str(CLEANED_FILE)))
    if not exists:
        print("ファイルが存在しないためバリデーション中断")
        return False

    df = pd.read_csv(CLEANED_FILE, encoding="utf-8-sig")

    # 2. 行数チェック
    row_count = len(df)
    results.append(_check("2. 行数 >= 400", row_count >= MIN_ROWS, f"actual={row_count}"))

    # 3. 必須列の存在
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    results.append(_check("3. 必須列の存在", len(missing_cols) == 0,
                          f"missing={missing_cols}" if missing_cols else "all present"))

    # 4. 日付フォーマット YYYY-MM-DD
    date_ok = df["response_date"].dropna().str.match(r"^\d{4}-\d{2}-\d{2}$").all() \
        if "response_date" in df.columns else False
    results.append(_check("4. 日付フォーマット YYYY-MM-DD", bool(date_ok)))

    # 5. service_typeが5種類
    if "service_type" in df.columns:
        actual_types = set(df["service_type"].dropna().unique())
        types_ok = actual_types == EXPECTED_SERVICE_TYPES
        results.append(_check("5. service_typeが5種類", types_ok, f"actual={sorted(actual_types)}"))
    else:
        results.append(_check("5. service_typeが5種類", False, "column missing"))

    # 6. agentが5種類
    if "agent" in df.columns:
        actual_agents = set(df["agent"].dropna().unique())
        agents_ok = actual_agents == EXPECTED_AGENTS
        results.append(_check("6. agentが5種類", agents_ok, f"actual={sorted(actual_agents)}"))
    else:
        results.append(_check("6. agentが5種類", False, "column missing"))

    # 7. overall_sat 1-5
    if "overall_sat" in df.columns:
        sat_ok = df["overall_sat"].dropna().between(1, 5).all()
        results.append(_check("7. overall_satが1-5の範囲", bool(sat_ok),
                              f"min={df['overall_sat'].min()}, max={df['overall_sat'].max()}"))
    else:
        results.append(_check("7. overall_satが1-5の範囲", False, "column missing"))

    # 8. response_speed 1-5
    if "response_speed" in df.columns:
        rs_ok = df["response_speed"].dropna().between(1, 5).all()
        results.append(_check("8. response_speedが1-5の範囲", bool(rs_ok),
                              f"min={df['response_speed'].min()}, max={df['response_speed'].max()}"))
    else:
        results.append(_check("8. response_speedが1-5の範囲", False, "column missing"))

    # 9. quality 1-5
    if "quality" in df.columns:
        q_ok = df["quality"].dropna().between(1, 5).all()
        results.append(_check("9. qualityが1-5の範囲", bool(q_ok),
                              f"min={df['quality'].min()}, max={df['quality'].max()}"))
    else:
        results.append(_check("9. qualityが1-5の範囲", False, "column missing"))

    # 10. cost_perf 1-5
    if "cost_perf" in df.columns:
        cp_ok = df["cost_perf"].dropna().between(1, 5).all()
        results.append(_check("10. cost_perfが1-5の範囲", bool(cp_ok),
                              f"min={df['cost_perf'].min()}, max={df['cost_perf'].max()}"))
    else:
        results.append(_check("10. cost_perfが1-5の範囲", False, "column missing"))

    # 11. nps 0-10
    if "nps" in df.columns:
        nps_ok = df["nps"].dropna().between(0, 10).all()
        results.append(_check("11. npsが0-10の範囲", bool(nps_ok),
                              f"min={df['nps'].min()}, max={df['nps'].max()}"))
    else:
        results.append(_check("11. npsが0-10の範囲", False, "column missing"))

    # 12. csat_score 1.0-5.0
    if "csat_score" in df.columns:
        cs_ok = df["csat_score"].dropna().between(1.0, 5.0).all()
        results.append(_check("12. csat_scoreが1.0-5.0の範囲", bool(cs_ok),
                              f"min={df['csat_score'].min():.2f}, max={df['csat_score'].max():.2f}"))
    else:
        results.append(_check("12. csat_scoreが1.0-5.0の範囲", False, "column missing"))

    # 13. nps_category の値域
    if "nps_category" in df.columns:
        actual_cats = set(df["nps_category"].dropna().unique())
        cat_ok = actual_cats.issubset(EXPECTED_NPS_CATEGORIES)
        results.append(_check("13. nps_categoryの値域", cat_ok, f"actual={sorted(actual_cats)}"))
    else:
        results.append(_check("13. nps_categoryの値域", False, "column missing"))

    # 14. satisfaction_flag の値域
    if "satisfaction_flag" in df.columns:
        actual_flags = set(df["satisfaction_flag"].dropna().unique())
        flag_ok = actual_flags.issubset(EXPECTED_SAT_FLAGS)
        results.append(_check("14. satisfaction_flagの値域", flag_ok, f"actual={sorted(actual_flags)}"))
    else:
        results.append(_check("14. satisfaction_flagの値域", False, "column missing"))

    # 15. source_file 列の存在
    results.append(_check("15. source_file列の存在", "source_file" in df.columns))

    # 16. 欠損率 <= 15%
    if len(df) > 0:
        missing_ratio = df.isnull().mean().max()
        results.append(_check("16. 欠損率 <= 15%", missing_ratio <= MAX_MISSING_RATIO,
                              f"max_missing_ratio={missing_ratio:.2%}"))
    else:
        results.append(_check("16. 欠損率 <= 15%", False, "no rows"))

    # 17. source_fileが3種類
    if "source_file" in df.columns:
        src_count = df["source_file"].nunique()
        results.append(_check("17. source_fileが3種類", src_count >= MIN_SOURCE_STYLES,
                              f"actual={src_count}"))
    else:
        results.append(_check("17. source_fileが3種類", False, "column missing"))

    # 18. 推奨者件数 >= 1
    if "nps_category" in df.columns:
        promoters = (df["nps_category"] == "推奨者").sum()
        results.append(_check("18. 推奨者件数 >= 1", promoters >= 1, f"count={promoters}"))
    else:
        results.append(_check("18. 推奨者件数 >= 1", False, "column missing"))

    # サマリー
    passed = sum(results)
    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")
    return all(results)


if __name__ == "__main__":
    ok = run()
    exit(0 if ok else 1)
