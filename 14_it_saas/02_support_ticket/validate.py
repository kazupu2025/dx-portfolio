# -*- coding: utf-8 -*-
"""
C-60 IT/SaaS - カスタマーサポートチケット分析
クレンジング出力バリデーションスクリプト (18項目)
"""

import os
import re
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CLEANED_PATH = os.path.join(BASE_DIR, "output", "cleaned_tickets_202401.csv")

REQUIRED_COLS = [
    "received_date", "ticket_id", "category", "priority", "agent_id",
    "resolution_hours", "is_escalated", "escalation_reason",
    "satisfaction", "is_resolved", "speed_grade", "cs_level", "source_file"
]

EXPECTED_CATEGORIES = {"ログイン障害", "機能不具合", "請求問い合わせ", "使い方質問", "データ移行"}
EXPECTED_PRIORITIES = {"高", "中", "低"}
EXPECTED_SPEED_GRADES = {"迅速", "標準", "長時間"}
EXPECTED_CS_LEVELS = {"高満足", "普通", "低満足"}
# escalation_reason は optional 列（欠損率チェック除外）
OPTIONAL_COLS = {"escalation_reason"}


def check(label, condition):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {label}")
    return condition


def main():
    results = []

    # 1. ファイル存在チェック
    exists = os.path.exists(CLEANED_PATH)
    results.append(check("ファイルが存在する", exists))
    if not exists:
        print("[FAIL] ファイルが存在しないため以降のチェックをスキップします")
        total = len(results)
        passed = sum(results)
        print(f"\n結果: {passed}/{total} PASS")
        return

    df = pd.read_csv(CLEANED_PATH, encoding="utf-8-sig")

    # 2. 行数 >= 420
    results.append(check(f"行数が420以上 (実際: {len(df)})", len(df) >= 420))

    # 3. 必須列がすべて存在する
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    results.append(check(f"必須列がすべて存在する (不足: {missing_cols})", len(missing_cols) == 0))

    # 4. received_date フォーマット YYYY-MM-DD
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    valid_dates = df["received_date"].dropna().apply(lambda x: bool(date_pattern.match(str(x))))
    results.append(check("received_dateがYYYY-MM-DD形式", valid_dates.all()))

    # 5. ticket_id 一意性
    results.append(check("ticket_idが一意", df["ticket_id"].nunique() == len(df)))

    # 6. category が5種類含まれる
    actual_cats = set(df["category"].dropna().unique())
    results.append(check(f"categoryが5種類含まれる (実際: {actual_cats})", EXPECTED_CATEGORIES <= actual_cats))

    # 7. priority が "高"/"中"/"低" のみ
    actual_prios = set(df["priority"].dropna().unique())
    results.append(check(f"priorityが正しい3種類 (実際: {actual_prios})", actual_prios <= EXPECTED_PRIORITIES))

    # 8. agent_id の種類が4以上
    agent_count = df["agent_id"].nunique()
    results.append(check(f"agent_idの種類が4以上 (実際: {agent_count})", agent_count >= 4))

    # 9. resolution_hours > 0
    rh = pd.to_numeric(df["resolution_hours"], errors="coerce")
    results.append(check("resolution_hoursがすべて>0", (rh > 0).all()))

    # 10. is_escalated が 0/1 のみ
    esc_vals = set(df["is_escalated"].dropna().astype(int).unique())
    results.append(check(f"is_escalatedが0/1のみ (実際: {esc_vals})", esc_vals <= {0, 1}))

    # 11. satisfaction が 1〜5 の範囲
    sat = pd.to_numeric(df["satisfaction"], errors="coerce")
    results.append(check("satisfactionが1〜5の範囲", ((sat >= 1) & (sat <= 5)).all()))

    # 12. is_resolved が 0/1 のみ
    res_vals = set(df["is_resolved"].dropna().astype(int).unique())
    results.append(check(f"is_resolvedが0/1のみ (実際: {res_vals})", res_vals <= {0, 1}))

    # 13. speed_grade が3種類
    actual_sg = set(df["speed_grade"].dropna().unique())
    results.append(check(f"speed_gradeが3種類 (実際: {actual_sg})", EXPECTED_SPEED_GRADES <= actual_sg))

    # 14. cs_level が3種類
    actual_cl = set(df["cs_level"].dropna().unique())
    results.append(check(f"cs_levelが3種類 (実際: {actual_cl})", EXPECTED_CS_LEVELS <= actual_cl))

    # 15. 必須列の欠損率 <= 15%（escalation_reason除く）
    check_cols = [c for c in REQUIRED_COLS if c not in OPTIONAL_COLS]
    null_rate_ok = True
    for col in check_cols:
        if col in df.columns:
            rate = df[col].isna().mean()
            if rate > 0.15:
                print(f"  [INFO] {col} 欠損率: {rate:.1%}")
                null_rate_ok = False
    results.append(check("必須列の欠損率<=15%（escalation_reason除く）", null_rate_ok))

    # 16. source_file が3種類
    sf_count = df["source_file"].nunique()
    results.append(check(f"source_fileが3種類 (実際: {sf_count})", sf_count == 3))

    # 17. 解決件数 >= 1
    resolved_count = int(pd.to_numeric(df["is_resolved"], errors="coerce").sum())
    results.append(check(f"解決件数が1以上 (実際: {resolved_count})", resolved_count >= 1))

    # 18. エスカレーション件数 >= 1
    esc_count = int(pd.to_numeric(df["is_escalated"], errors="coerce").sum())
    results.append(check(f"エスカレーション件数が1以上 (実際: {esc_count})", esc_count >= 1))

    total = len(results)
    passed = sum(results)
    print(f"\n[結果] {passed}/{total} PASS")
    if passed == total:
        print("[OK] すべてのチェックに合格しました")
    else:
        print(f"[NG] {total - passed}件のチェックが失敗しました")


if __name__ == "__main__":
    main()
