"""
C-39: 入居者対応履歴・クレーム集計パイプライン
クレンジング出力バリデーションスクリプト（18項目以上）
絵文字・em-dash・円記号を使わず [PASS]/[FAIL] で表示する
"""

import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CLEANED_CSV = OUTPUT_DIR / "cleaned_claims_202401.csv"

REQUIRED_COLS = [
    "receipt_date", "case_no", "property_name", "room_no",
    "claim_type", "status", "response_days", "work_hours",
    "source_file", "is_resolved", "urgency", "cost_estimate",
]

EXPECTED_PROPERTIES = {"サンシャインA棟", "グリーンB棟", "ブルーC棟", "ホワイトD棟", "シルバーE棟"}
EXPECTED_CLAIM_TYPES = {"設備故障", "騒音", "水漏れ", "害虫", "駐車", "その他"}
EXPECTED_STATUSES = {"解決済", "対応中", "未対応"}
EXPECTED_URGENCIES = {"緊急", "通常", "遅延"}


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "[PASS]" if passed else "[FAIL]"
    msg = f"{status} {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    return passed


def run_validation() -> bool:
    results = []

    # 1. CSVファイル存在確認
    results.append(check("CSVファイル存在確認", CLEANED_CSV.exists(), str(CLEANED_CSV)))
    if not CLEANED_CSV.exists():
        print("\n[ERROR] 出力CSVが存在しないため検証を中止します。cleanse.py を先に実行してください。")
        return False

    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")

    # 2. 行数 >= 420
    results.append(check("行数 >= 420", len(df) >= 420, f"実際: {len(df)} rows"))

    # 3. 必須列の存在
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    results.append(check("必須列の存在", len(missing_cols) == 0, f"不足列: {missing_cols}" if missing_cols else ""))

    if missing_cols:
        print("[ERROR] 必須列が不足しているため一部チェックをスキップします。")

    # 4. case_noのユニーク性
    n_dup = df["case_no"].duplicated().sum() if "case_no" in df.columns else -1
    results.append(check("case_noのユニーク性", n_dup == 0, f"重複件数: {n_dup}"))

    # 5. 日付フォーマット YYYY-MM-DD
    if "receipt_date" in df.columns:
        import re
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        bad_dates = df["receipt_date"].dropna().apply(lambda x: not bool(re.match(pattern, str(x)))).sum()
        results.append(check("日付フォーマット YYYY-MM-DD", bad_dates == 0, f"不正件数: {bad_dates}"))
    else:
        results.append(check("日付フォーマット YYYY-MM-DD", False, "列なし"))

    # 6. property_nameが5種類
    if "property_name" in df.columns:
        prop_set = set(df["property_name"].dropna().unique())
        results.append(check("property_nameが5種類", prop_set == EXPECTED_PROPERTIES,
                             f"実際: {sorted(prop_set)}"))
    else:
        results.append(check("property_nameが5種類", False, "列なし"))

    # 7. claim_typeが6種類
    if "claim_type" in df.columns:
        ct_set = set(df["claim_type"].dropna().unique())
        results.append(check("claim_typeが6種類", ct_set == EXPECTED_CLAIM_TYPES,
                             f"実際: {sorted(ct_set)}"))
    else:
        results.append(check("claim_typeが6種類", False, "列なし"))

    # 8. statusが"解決済"/"対応中"/"未対応"のみ
    if "status" in df.columns:
        status_set = set(df["status"].dropna().unique())
        unexpected = status_set - EXPECTED_STATUSES
        results.append(check('statusが想定3値のみ', len(unexpected) == 0,
                             f"想定外の値: {unexpected}" if unexpected else ""))
    else:
        results.append(check("statusが想定3値のみ", False, "列なし"))

    # 9. response_days >= 1
    if "response_days" in df.columns:
        bad_days = (pd.to_numeric(df["response_days"], errors="coerce").dropna() < 1).sum()
        results.append(check("response_days >= 1", bad_days == 0, f"不正件数: {bad_days}"))
    else:
        results.append(check("response_days >= 1", False, "列なし"))

    # 10. work_hours > 0
    if "work_hours" in df.columns:
        bad_hours = (pd.to_numeric(df["work_hours"], errors="coerce").dropna() <= 0).sum()
        results.append(check("work_hours > 0", bad_hours == 0, f"不正件数: {bad_hours}"))
    else:
        results.append(check("work_hours > 0", False, "列なし"))

    # 11. is_resolvedが0または1のみ
    if "is_resolved" in df.columns:
        invalid_resolved = (~df["is_resolved"].isin([0, 1])).sum()
        results.append(check("is_resolvedが0または1のみ", invalid_resolved == 0,
                             f"不正件数: {invalid_resolved}"))
    else:
        results.append(check("is_resolvedが0または1のみ", False, "列なし"))

    # 12. urgencyが"緊急"/"通常"/"遅延"のみ
    if "urgency" in df.columns:
        urgency_set = set(df["urgency"].dropna().unique())
        unexpected_u = urgency_set - EXPECTED_URGENCIES
        results.append(check('urgencyが想定3値のみ', len(unexpected_u) == 0,
                             f"想定外の値: {unexpected_u}" if unexpected_u else ""))
    else:
        results.append(check("urgencyが想定3値のみ", False, "列なし"))

    # 13. cost_estimate > 0
    if "cost_estimate" in df.columns:
        bad_cost = (pd.to_numeric(df["cost_estimate"], errors="coerce").dropna() <= 0).sum()
        results.append(check("cost_estimate > 0", bad_cost == 0, f"不正件数: {bad_cost}"))
    else:
        results.append(check("cost_estimate > 0", False, "列なし"))

    # 14. source_file列の存在
    results.append(check("source_file列の存在", "source_file" in df.columns))

    # 15. 欠損率 <= 15%
    if len(df) > 0:
        missing_rate = df.isnull().mean().max()
        results.append(check("欠損率 <= 15%", missing_rate <= 0.15,
                             f"最大欠損率: {missing_rate:.1%}"))
    else:
        results.append(check("欠損率 <= 15%", False, "行数0"))

    # 16. source_fileが3種類
    if "source_file" in df.columns:
        n_sources = df["source_file"].nunique()
        results.append(check("source_fileが3種類", n_sources == 3, f"実際: {n_sources}"))
    else:
        results.append(check("source_fileが3種類", False, "列なし"))

    # 17. 未対応件数 >= 1
    if "status" in df.columns:
        n_unresolved = (df["status"] == "未対応").sum()
        results.append(check("未対応件数 >= 1", n_unresolved >= 1, f"件数: {n_unresolved}"))
    else:
        results.append(check("未対応件数 >= 1", False, "列なし"))

    # 18. 解決済件数 >= 1
    if "status" in df.columns:
        n_resolved = (df["status"] == "解決済").sum()
        results.append(check("解決済件数 >= 1", n_resolved >= 1, f"件数: {n_resolved}"))
    else:
        results.append(check("解決済件数 >= 1", False, "列なし"))

    # 集計
    passed = sum(results)
    total = len(results)
    print(f"\n--- Validation Summary ---")
    print(f"PASS: {passed} / {total}")
    if passed == total:
        print("Result: ALL PASSED")
    else:
        print(f"Result: {total - passed} FAILED")

    return passed == total


if __name__ == "__main__":
    ok = run_validation()
    sys.exit(0 if ok else 1)
