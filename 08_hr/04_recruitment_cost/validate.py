"""
C-41: validate.py -- クレンジング結果の品質チェック (18項目以上)
全PASS必須。絵文字・em-dash・YEN記号は使用しない。[PASS]/[FAIL]を使う。
"""

import re
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "output" / "cleaned_recruitment_202401.csv"

REQUIRED_COLS = [
    "apply_date", "apply_no", "channel", "job_type",
    "cost", "phase", "is_hired", "is_accepted",
    "cost_per_hire", "channel_efficiency", "offer_acceptance",
    "source_file",
]

VALID_CHANNELS = {"求人サイト", "SNS採用", "リファラル", "エージェント", "合同説明会"}
VALID_JOB_TYPES = {"エンジニア", "営業", "事務", "マーケ", "デザイン"}
VALID_PHASES = {"書類選考", "一次面接", "二次面接", "最終面接", "内定"}
VALID_EFFICIENCY = {"高効率", "標準"}
VALID_OFFER_ACCEPTANCE = {"承諾", "辞退", "該当なし"}

results = []


def check(label: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append(passed)


# -------------------------------------------------------------------
# 1. ファイル存在チェック
# -------------------------------------------------------------------
if not CSV_PATH.exists():
    print(f"[FAIL] CSV ファイルが存在しない: {CSV_PATH}")
    sys.exit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

# -------------------------------------------------------------------
# 2. 行数チェック (>= 420)
# -------------------------------------------------------------------
check("行数 >= 420", len(df) >= 420, f"実際: {len(df)} 行")

# -------------------------------------------------------------------
# 3. 必須列の存在チェック
# -------------------------------------------------------------------
missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
check("必須列が全て存在する", len(missing_cols) == 0, f"不足: {missing_cols}")

# -------------------------------------------------------------------
# 4. apply_no のユニーク性
# -------------------------------------------------------------------
if "apply_no" in df.columns:
    dup_count = df["apply_no"].duplicated().sum()
    check("apply_no にユニーク性がある", dup_count == 0, f"重複件数: {dup_count}")
else:
    check("apply_no 列が存在する", False)

# -------------------------------------------------------------------
# 5. 日付フォーマット YYYY-MM-DD
# -------------------------------------------------------------------
if "apply_date" in df.columns:
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    invalid_dates = df["apply_date"].dropna().apply(
        lambda v: not bool(pattern.match(str(v).strip()))
    )
    check("apply_date が YYYY-MM-DD 形式", not invalid_dates.any(),
          f"不正件数: {invalid_dates.sum()}")
else:
    check("apply_date 列が存在する", False)

# -------------------------------------------------------------------
# 6. channel が5種類
# -------------------------------------------------------------------
if "channel" in df.columns:
    actual_channels = set(df["channel"].dropna().unique())
    check("channel が5種類", len(actual_channels) == 5, f"実際: {actual_channels}")
    check("channel が期待の値を含む",
          actual_channels == VALID_CHANNELS,
          f"期待: {VALID_CHANNELS}, 実際: {actual_channels}")
else:
    check("channel 列が存在する", False)

# -------------------------------------------------------------------
# 7. job_type が5種類
# -------------------------------------------------------------------
if "job_type" in df.columns:
    actual_jobs = set(df["job_type"].dropna().unique())
    check("job_type が5種類", len(actual_jobs) == 5, f"実際: {actual_jobs}")
    check("job_type が期待の職種を含む",
          actual_jobs == VALID_JOB_TYPES,
          f"期待: {VALID_JOB_TYPES}, 実際: {actual_jobs}")
else:
    check("job_type 列が存在する", False)

# -------------------------------------------------------------------
# 8. cost > 0
# -------------------------------------------------------------------
if "cost" in df.columns:
    invalid_cost = (df["cost"] <= 0).sum()
    check("cost がすべて > 0", invalid_cost == 0, f"違反件数: {invalid_cost}")
else:
    check("cost 列が存在する", False)

# -------------------------------------------------------------------
# 9. phase が5種類
# -------------------------------------------------------------------
if "phase" in df.columns:
    actual_phases = set(df["phase"].dropna().unique())
    check("phase が5種類以内（有効値のみ）",
          len(actual_phases - VALID_PHASES) == 0,
          f"無効値: {actual_phases - VALID_PHASES}")
    check("phase が5種類", len(actual_phases) == 5, f"実際: {actual_phases}")
else:
    check("phase 列が存在する", False)

# -------------------------------------------------------------------
# 10. is_hired が 0 または 1 のみ
# -------------------------------------------------------------------
if "is_hired" in df.columns:
    invalid_hired = (~df["is_hired"].isin([0, 1])).sum()
    check("is_hired が 0 または 1 のみ", invalid_hired == 0, f"違反件数: {invalid_hired}")
else:
    check("is_hired 列が存在する", False)

# -------------------------------------------------------------------
# 11. is_accepted が 0, 1, または NaN
# -------------------------------------------------------------------
if "is_accepted" in df.columns:
    not_na = df["is_accepted"].dropna()
    invalid_accepted = (~not_na.isin([0, 1])).sum()
    check("is_accepted が 0/1/NaN のみ", invalid_accepted == 0,
          f"違反件数: {invalid_accepted}")
else:
    check("is_accepted 列が存在する", False)

# -------------------------------------------------------------------
# 12. channel_efficiency が "高効率"/"標準" のみ
# -------------------------------------------------------------------
if "channel_efficiency" in df.columns:
    actual_eff = set(df["channel_efficiency"].dropna().unique())
    invalid_eff = actual_eff - VALID_EFFICIENCY
    check("channel_efficiency が高効率/標準 のみ",
          len(invalid_eff) == 0, f"無効値: {invalid_eff}")
else:
    check("channel_efficiency 列が存在する", False)

# -------------------------------------------------------------------
# 13. offer_acceptance が "承諾"/"辞退"/"該当なし" のみ
# -------------------------------------------------------------------
if "offer_acceptance" in df.columns:
    actual_oa = set(df["offer_acceptance"].dropna().unique())
    invalid_oa = actual_oa - VALID_OFFER_ACCEPTANCE
    check("offer_acceptance が承諾/辞退/該当なし のみ",
          len(invalid_oa) == 0, f"無効値: {invalid_oa}")
else:
    check("offer_acceptance 列が存在する", False)

# -------------------------------------------------------------------
# 14. source_file 列の存在
# -------------------------------------------------------------------
if "source_file" in df.columns:
    empty_sf = df["source_file"].isna().sum()
    check("source_file が全行に存在する", empty_sf == 0, f"空件数: {empty_sf}")
else:
    check("source_file 列が存在する", False)

# -------------------------------------------------------------------
# 15. 欠損率 <= 20% (is_accepted 列はNaN多数のため主要列のみ)
# -------------------------------------------------------------------
key_cols = [c for c in ["apply_date", "channel", "job_type", "phase", "cost", "is_hired"]
            if c in df.columns]
if key_cols:
    max_missing_rate = df[key_cols].isna().mean().max()
    check("主要列の欠損率 <= 20%", max_missing_rate <= 0.20,
          f"最大欠損率: {max_missing_rate:.2%}")
else:
    check("主要列の欠損率チェック", False)

# -------------------------------------------------------------------
# 16. source_file が 3種類
# -------------------------------------------------------------------
if "source_file" in df.columns:
    n_files = df["source_file"].nunique()
    check("source_file の種類数 == 3 (3ファイル)", n_files == 3, f"実際: {n_files}")
else:
    check("source_file の種類数チェック", False)

# -------------------------------------------------------------------
# 17. 採用件数 (is_hired=1) >= 1
# -------------------------------------------------------------------
if "is_hired" in df.columns:
    hired_count = (df["is_hired"] == 1).sum()
    check("採用件数 (is_hired=1) >= 1", hired_count >= 1, f"採用件数: {hired_count}")
else:
    check("is_hired 列が存在する (採用件数チェック用)", False)

# -------------------------------------------------------------------
# 18. cost の最大値 <= 1000000
# -------------------------------------------------------------------
if "cost" in df.columns:
    max_cost = df["cost"].max()
    check("cost の最大値 <= 1000000", max_cost <= 1000000, f"最大値: {max_cost}")
else:
    check("cost 列が存在する (最大値チェック用)", False)

# -------------------------------------------------------------------
# 19. cost_per_hire が cost と等しい
# -------------------------------------------------------------------
if all(c in df.columns for c in ("cost", "cost_per_hire")):
    mismatch = (df["cost"] != df["cost_per_hire"]).sum()
    check("cost_per_hire が cost と一致する", mismatch == 0, f"不一致件数: {mismatch}")
else:
    check("cost/cost_per_hire 列が存在する", False)

# -------------------------------------------------------------------
# 20. channel_efficiency が高効率の行はリファラルまたはSNS採用かつ低コスト
# -------------------------------------------------------------------
if all(c in df.columns for c in ("channel", "channel_efficiency", "cost")):
    cost_median = df["cost"].median()
    high_eff = df[df["channel_efficiency"] == "高効率"]
    valid_high_eff = high_eff[
        high_eff["channel"].isin(["リファラル", "SNS採用"]) & (high_eff["cost"] <= cost_median)
    ]
    check("高効率行はリファラル/SNS採用 かつ コスト<=中央値",
          len(valid_high_eff) == len(high_eff),
          f"高効率行数: {len(high_eff)}, 有効: {len(valid_high_eff)}")
else:
    check("channel_efficiency整合性チェック列が存在する", False)

# -------------------------------------------------------------------
# 結果サマリー
# -------------------------------------------------------------------
total = len(results)
passed = sum(results)
failed = total - passed

print(f"\n結果: {passed}/{total} PASS")

if failed > 0:
    print(f"FAIL: {failed} 件の検証に失敗しました")
    sys.exit(1)
else:
    print("全チェック PASS")
    sys.exit(0)
