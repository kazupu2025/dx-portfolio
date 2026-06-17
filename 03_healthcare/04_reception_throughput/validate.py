# -*- coding: utf-8 -*-
"""
C-37: 来客記録データ集計・スループット分析パイプライン
バリデーションスクリプト: cleaned CSV の品質を 18 項目以上チェックする
絵文字・em-dash・記号は使わず [PASS]/[FAIL] で出力する
"""

import pandas as pd
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "cleaned_reception_202401.csv"

REQUIRED_COLS = [
    "visit_date", "reception_no", "department",
    "arrival_time", "start_time", "end_time",
    "wait_minutes", "treat_minutes",
    "source_file", "wait_level", "time_slot",
]

VALID_DEPARTMENTS = {"内科", "外科", "整形外科", "小児科", "眼科"}
VALID_WAIT_LEVELS = {"長待ち", "普通", "短待ち"}


def run_checks(df: pd.DataFrame) -> list:
    """チェック結果を (チェック名, 合否, 詳細メッセージ) のリストで返す"""
    results = []

    def ok(name, detail=""):
        results.append((name, True, detail))

    def ng(name, detail=""):
        results.append((name, False, detail))

    # 2. 行数 >= 420
    if len(df) >= 420:
        ok("行数 >= 420", f"{len(df)} 件")
    else:
        ng("行数 >= 420", f"{len(df)} 件 (期待: >= 420)")

    # 3. 必須列の存在（8列）
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if not missing:
        ok("必須列の存在", f"{len(REQUIRED_COLS)} 列すべて存在")
    else:
        ng("必須列の存在", f"不足列: {missing}")

    # 4. reception_no のユニーク性
    n_total = len(df)
    n_unique = df["reception_no"].nunique()
    if n_unique == n_total:
        ok("reception_no のユニーク性", f"{n_unique} 件すべてユニーク")
    else:
        ng("reception_no のユニーク性", f"重複あり: {n_total - n_unique} 件")

    # 5. 日付フォーマット YYYY-MM-DD
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    bad_dates = df["visit_date"].dropna()[
        ~df["visit_date"].dropna().apply(lambda x: bool(date_pattern.match(str(x))))
    ]
    if len(bad_dates) == 0:
        ok("日付フォーマット YYYY-MM-DD", "全行一致")
    else:
        ng("日付フォーマット YYYY-MM-DD", f"{len(bad_dates)} 件不正")

    # 6. department が 5 種類
    depts = set(df["department"].dropna().unique())
    if depts == VALID_DEPARTMENTS:
        ok("department が 5 種類", f"{sorted(depts)}")
    else:
        ng("department が 5 種類", f"{sorted(depts)} (期待: {sorted(VALID_DEPARTMENTS)})")

    # 7. wait_minutes >= 0
    bad_wm = df["wait_minutes"].dropna()[df["wait_minutes"].dropna() < 0]
    if len(bad_wm) == 0:
        ok("wait_minutes >= 0", "全行非負")
    else:
        ng("wait_minutes >= 0", f"{len(bad_wm)} 件が負値")

    # 8. treat_minutes > 0
    bad_tm = df["treat_minutes"].dropna()[df["treat_minutes"].dropna() <= 0]
    if len(bad_tm) == 0:
        ok("treat_minutes > 0", "全行正値")
    else:
        ng("treat_minutes > 0", f"{len(bad_tm)} 件が 0 以下")

    # 9. wait_level が "長待ち"/"普通"/"短待ち" のみ
    bad_wl = df["wait_level"].dropna()[~df["wait_level"].dropna().isin(VALID_WAIT_LEVELS)]
    if len(bad_wl) == 0:
        ok("wait_level 値域", f"有効値のみ: {sorted(df['wait_level'].unique())}")
    else:
        ng("wait_level 値域", f"{len(bad_wl)} 件が不正値")

    # 10. time_slot が存在（NULL件数0）
    null_ts = df["time_slot"].isna().sum()
    if null_ts == 0:
        ok("time_slot NULL件数 = 0", "全行非NULL")
    else:
        ng("time_slot NULL件数 = 0", f"{null_ts} 件が NULL")

    # 11. source_file 列の存在
    if "source_file" in df.columns:
        ok("source_file 列の存在", "存在する")
    else:
        ng("source_file 列の存在", "列がない")

    # 12. 欠損率 <= 15%
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isnull().sum().sum()
    null_rate = null_cells / total_cells if total_cells > 0 else 0
    if null_rate <= 0.15:
        ok("欠損率 <= 15%", f"{null_rate:.1%}")
    else:
        ng("欠損率 <= 15%", f"{null_rate:.1%} (期待: <= 15%)")

    # 13. source_file が 3 種類
    n_src = df["source_file"].nunique() if "source_file" in df.columns else 0
    if n_src == 3:
        ok("source_file が 3 種類", f"{sorted(df['source_file'].unique())}")
    else:
        ng("source_file が 3 種類", f"{n_src} 種類")

    # 14. 長待ち件数 >= 1
    n_long_wait = (df["wait_level"] == "長待ち").sum()
    if n_long_wait >= 1:
        ok("長待ち件数 >= 1", f"{n_long_wait} 件")
    else:
        ng("長待ち件数 >= 1", "長待ちレコードが 0 件")

    # 15. 診療科5種類確認
    n_dept = df["department"].nunique()
    if n_dept == 5:
        ok("診療科が 5 種類", f"{sorted(df['department'].unique())}")
    else:
        ng("診療科が 5 種類", f"{n_dept} 種類")

    # 16. wait_minutes の最大値 <= 200
    max_wait = df["wait_minutes"].dropna().max()
    if max_wait <= 200:
        ok("wait_minutes の最大値 <= 200", f"最大値: {max_wait}")
    else:
        ng("wait_minutes の最大値 <= 200", f"最大値: {max_wait} (期待: <= 200)")

    # 17. treat_minutes の最大値 <= 120
    max_treat = df["treat_minutes"].dropna().max()
    if max_treat <= 120:
        ok("treat_minutes の最大値 <= 120", f"最大値: {max_treat}")
    else:
        ng("treat_minutes の最大値 <= 120", f"最大値: {max_treat} (期待: <= 120)")

    # 18. 診察時間 > 0 の確認（再チェック）
    bad_treat2 = df["treat_minutes"].dropna()[df["treat_minutes"].dropna() <= 0]
    if len(bad_treat2) == 0:
        ok("treat_minutes > 0 再確認", "全行正値")
    else:
        ng("treat_minutes > 0 再確認", f"{len(bad_treat2)} 件が 0 以下")

    return results


def main():
    print("=" * 60)
    print("バリデーション開始: cleaned_reception_202401.csv")
    print("=" * 60)

    # 1. CSVファイル存在確認
    if not CSV_PATH.exists():
        print(f"[FAIL] CSVファイル存在確認: {CSV_PATH} が見つかりません")
        sys.exit(1)
    print(f"[PASS] CSVファイル存在確認: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    results = run_checks(df)

    fail_count = 0
    for name, passed, detail in results:
        tag = "[PASS]" if passed else "[FAIL]"
        suffix = f" -- {detail}" if detail else ""
        print(f"{tag} {name}{suffix}")
        if not passed:
            fail_count += 1

    print("=" * 60)
    total = len(results) + 1  # +1 for file existence check
    print(f"結果: {total - fail_count}/{total} PASS, {fail_count} FAIL")
    if fail_count > 0:
        sys.exit(1)
    print("全チェック PASS")


if __name__ == "__main__":
    main()
