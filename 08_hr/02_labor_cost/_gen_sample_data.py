"""
C-30: 人事・採用 x 経理・財務 -- 人件費推移・予実差異レポート
サンプルデータ生成スクリプト

5部門 x 3雇用区分 x 12ヶ月 = 各スタイル180行
スタイルA: 標準日本語列名 (YYYY/MM)
スタイルB: 英語列名 (YYYY-MM)
スタイルC: バリアント日本語列名 (YYYY/MM)
合計 540行以上
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(42)
rng = np.random.default_rng(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DEPARTMENTS = ["営業部", "製造部", "管理部", "開発部", "物流部"]
EMPLOYMENT_TYPES = ["正社員", "契約社員", "パート"]

# 部門別・雇用区分別の基準予算人件費（月次）
BASE_BUDGET = {
    ("営業部", "正社員"):   5_000_000,
    ("営業部", "契約社員"): 1_500_000,
    ("営業部", "パート"):     800_000,
    ("製造部", "正社員"):   6_000_000,
    ("製造部", "契約社員"): 2_000_000,
    ("製造部", "パート"):   1_200_000,
    ("管理部", "正社員"):   3_000_000,
    ("管理部", "契約社員"):   900_000,
    ("管理部", "パート"):     400_000,
    ("開発部", "正社員"):   7_000_000,
    ("開発部", "契約社員"): 2_500_000,
    ("開発部", "パート"):     300_000,
    ("物流部", "正社員"):   4_000_000,
    ("物流部", "契約社員"): 1_800_000,
    ("物流部", "パート"):   1_500_000,
}

HEAD_COUNT = {
    ("営業部", "正社員"):  10,
    ("営業部", "契約社員"): 5,
    ("営業部", "パート"):   8,
    ("製造部", "正社員"):  15,
    ("製造部", "契約社員"): 8,
    ("製造部", "パート"):  12,
    ("管理部", "正社員"):   8,
    ("管理部", "契約社員"): 3,
    ("管理部", "パート"):   4,
    ("開発部", "正社員"):  18,
    ("開発部", "契約社員"): 7,
    ("開発部", "パート"):   3,
    ("物流部", "正社員"):  10,
    ("物流部", "契約社員"): 6,
    ("物流部", "パート"):  15,
}

MONTHS_A = [f"2024/{m:02d}" for m in range(1, 13)]
MONTHS_B = [f"2024-{m:02d}" for m in range(1, 13)]


def generate_records(month_str_fmt: str, months: list) -> list[dict]:
    """指定フォーマットの月リストで全部門×雇用区分のレコードを生成"""
    rows = []
    for month_val, month_b in zip(months, MONTHS_B):
        # 季節トレンド（残業代が夏・年末に増加）
        m = int(month_b.split("-")[1])
        season_factor = 1.0 + 0.05 * (1 if m in (7, 8, 12) else 0)

        for dept in DEPARTMENTS:
            for emp_type in EMPLOYMENT_TYPES:
                budget = BASE_BUDGET[(dept, emp_type)]
                headcount = HEAD_COUNT[(dept, emp_type)]

                # 実績は予算の85%~115%の範囲でランダム
                # 10%の確率で115%超の大幅超過
                if random.random() < 0.10:
                    variance_factor = random.uniform(1.15, 1.30)
                else:
                    variance_factor = random.uniform(0.85, 1.15)

                actual = int(budget * variance_factor * season_factor)
                # 残業代は実績の5%~20%の範囲
                overtime_ratio = random.uniform(0.05, 0.20)
                overtime = int(actual * overtime_ratio)

                rows.append({
                    "month": month_val,
                    "department": dept,
                    "employment_type": emp_type,
                    "head_count": headcount,
                    "budget": budget,
                    "actual": actual,
                    "overtime": overtime,
                })
    return rows


def to_style_a(rec: dict) -> dict:
    """スタイルA: 標準日本語列名、YYYY/MM形式"""
    return {
        "対象年月":   rec["month"],
        "部門":       rec["department"],
        "雇用区分":   rec["employment_type"],
        "社員数":     rec["head_count"],
        "予算人件費": rec["budget"],
        "実績人件費": rec["actual"],
        "残業代":     rec["overtime"],
    }


def to_style_b(rec: dict) -> dict:
    """スタイルB: 英語列名、YYYY-MM形式（月文字列はそのまま）"""
    return {
        "YearMonth":       rec["month"],
        "Department":      rec["department"],
        "EmploymentType":  rec["employment_type"],
        "HeadCount":       rec["head_count"],
        "BudgetLaborCost": rec["budget"],
        "ActualLaborCost": rec["actual"],
        "OvertimeCost":    rec["overtime"],
    }


def to_style_c(rec: dict) -> dict:
    """スタイルC: バリアント日本語列名、YYYY/MM形式"""
    return {
        "集計月":   rec["month"],
        "所属部門": rec["department"],
        "雇用形態": rec["employment_type"],
        "人員数":   rec["head_count"],
        "人件費予算": rec["budget"],
        "人件費実績": rec["actual"],
        "時間外手当": rec["overtime"],
    }


def main():
    # スタイルAC用 YYYY/MM, スタイルB用 YYYY-MM
    months_ac = [f"2024/{m:02d}" for m in range(1, 13)]
    months_b  = [f"2024-{m:02d}" for m in range(1, 13)]

    configs = [
        (months_ac, to_style_a, "labor_cost_styleA_202401.csv"),
        (months_b,  to_style_b, "labor_cost_styleB_202401.csv"),
        (months_ac, to_style_c, "labor_cost_styleC_202401.csv"),
    ]

    for months, converter, filename in configs:
        rows = generate_records(None, months)
        styled = [converter(r) for r in rows]
        df = pd.DataFrame(styled)
        out_path = DATA_DIR / filename
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"Created {filename}: {len(df)} rows")

    total = sum(
        len(pd.read_csv(DATA_DIR / cfg[2], encoding="utf-8-sig"))
        for cfg in configs
    )
    print(f"\n合計: {total} 行 (5部門 x 3雇用区分 x 12ヶ月 x 3スタイル)")


if __name__ == "__main__":
    main()
