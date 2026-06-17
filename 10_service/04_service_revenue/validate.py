# -*- coding: utf-8 -*-
"""
C-45: サービス別売上・原価レポート
バリデーションスクリプト (18項目)
"""

import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TARGET = os.path.join(OUTPUT_DIR, "cleaned_revenue_202401.csv")

REQUIRED_COLS = [
    "sale_date", "service_id", "service_name", "category", "client_id",
    "revenue", "cost", "gross_profit", "gross_margin", "profit_flag",
    "margin_grade", "source_file",
]

VALID_SERVICES = {"清掃", "警備", "設備管理", "受付代行", "IT保守", "コールセンター", "警備巡回", "施設管理"}
VALID_CATEGORIES = {"定期契約", "スポット", "複合"}
VALID_PROFIT_FLAGS = {"黒字", "赤字"}
VALID_MARGIN_GRADES = {"高利益", "中利益", "低利益"}
VALID_SOURCES = {
    "service_revenue_styleA.csv",
    "service_revenue_styleB.csv",
    "service_revenue_styleC.csv",
}
VALID_CLIENT_IDS = {"CLI-001", "CLI-002", "CLI-003", "CLI-004", "CLI-005"}
VALID_SERVICE_IDS = {"SVC-001", "SVC-002", "SVC-003", "SVC-004", "SVC-005", "SVC-006", "SVC-007", "SVC-008"}


def check(label: str, cond: bool) -> bool:
    status = "[PASS]" if cond else "[FAIL]"
    print(f"  {status} {label}")
    return cond


def main():
    results = []

    # 1. ファイル存在
    exists = os.path.exists(TARGET)
    results.append(check("ファイルが存在する", exists))

    if not exists:
        print(f"\nResult: 0/18 checks passed")
        return

    df = pd.read_csv(TARGET, encoding="utf-8-sig")

    # 2. 行数 >= 420
    results.append(check(f"行数 >= 420 (実際: {len(df)})", len(df) >= 420))

    # 3. 必須列が揃っている
    missing = set(REQUIRED_COLS) - set(df.columns)
    results.append(check(f"必須列が揃っている (欠損: {missing})", len(missing) == 0))

    # 4. sale_date フォーマット YYYY-MM-DD
    try:
        parsed = pd.to_datetime(df["sale_date"], format="%Y-%m-%d", errors="coerce")
        fmt_ok = parsed.notna().all()
    except Exception:
        fmt_ok = False
    results.append(check("sale_date フォーマット YYYY-MM-DD", fmt_ok))

    # 5. service_name 8種類
    svc_names = set(df["service_name"].dropna().unique())
    results.append(check(f"service_name が8種類含まれる (実際: {svc_names})", svc_names == VALID_SERVICES))

    # 6. category 3種類
    cats = set(df["category"].dropna().unique())
    results.append(check(f"category が3種類含まれる (実際: {cats})", cats == VALID_CATEGORIES))

    # 7. revenue > 0
    rev_ok = (df["revenue"] > 0).all()
    results.append(check("revenue > 0 (全行)", rev_ok))

    # 8. cost > 0
    cost_ok = (df["cost"] > 0).all()
    results.append(check("cost > 0 (全行)", cost_ok))

    # 9. gross_profit = revenue - cost
    gp_calc = (df["revenue"] - df["cost"]).round(2)
    gp_actual = df["gross_profit"].round(2)
    gp_ok = (gp_calc == gp_actual).all()
    results.append(check("gross_profit = revenue - cost (整合性)", gp_ok))

    # 10. gross_margin in [-1, 1] (NaN許容)
    gm = df["gross_margin"].dropna()
    gm_ok = ((gm >= -1) & (gm <= 1)).all() if len(gm) > 0 else False
    results.append(check("gross_margin in [-1, 1]", gm_ok))

    # 11. profit_flag 種類 == 2 {"黒字", "赤字"}
    pf_vals = set(df["profit_flag"].dropna().unique())
    results.append(check(f"profit_flag が {{黒字, 赤字}} (実際: {pf_vals})", pf_vals == VALID_PROFIT_FLAGS))

    # 12. margin_grade 種類 == 3
    mg_vals = set(df["margin_grade"].dropna().unique())
    results.append(check(f"margin_grade が3種類 (実際: {mg_vals})", mg_vals == VALID_MARGIN_GRADES))

    # 13. 欠損率 <= 15%
    missing_rate = df.isnull().mean().max()
    results.append(check(f"欠損率 <= 15% (最大: {missing_rate:.1%})", missing_rate <= 0.15))

    # 14. source_file 3種類
    src_vals = set(df["source_file"].dropna().unique())
    results.append(check(f"source_file が3種類 (実際: {src_vals})", src_vals == VALID_SOURCES))

    # 15. 黒字件数 >= 1
    black_cnt = (df["profit_flag"] == "黒字").sum()
    results.append(check(f"黒字件数 >= 1 (実際: {black_cnt})", black_cnt >= 1))

    # 16. 赤字件数 >= 1
    red_cnt = (df["profit_flag"] == "赤字").sum()
    results.append(check(f"赤字件数 >= 1 (実際: {red_cnt})", red_cnt >= 1))

    # 17. client_id 5種類
    cli_vals = set(df["client_id"].dropna().unique())
    results.append(check(f"client_id が5種類 (実際: {cli_vals})", cli_vals == VALID_CLIENT_IDS))

    # 18. service_id 8種類
    sid_vals = set(df["service_id"].dropna().unique())
    results.append(check(f"service_id が8種類 (実際: {sid_vals})", sid_vals == VALID_SERVICE_IDS))

    passed = sum(results)
    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")


if __name__ == "__main__":
    main()
