"""
_gen_sample_data.py
医療・介護施設のシフト希望サンプルデータを 3 CSV（スタイル A/B/C）で生成する。
"""

import os
import random
import pandas as pd
from datetime import date, timedelta

random.seed(42)

# ── 出力先 ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── マスタ定義 ─────────────────────────────────────────────────────────
ROLES = ["看護師", "介護士", "看護補助", "リハビリ師"]
ROLE_WEIGHTS = [0.40, 0.30, 0.20, 0.10]

SHIFTS = ["早番", "日勤", "遅番", "夜勤", "休み"]
# 夜勤は月4回程度（31日中）→ 13% 程度、休みは 8日/31日 ≒ 26%
SHIFT_WEIGHTS = [0.18, 0.33, 0.16, 0.13, 0.20]

SKILL_LEVELS = ["初級", "中級", "上級"]
SKILL_WEIGHTS = [0.30, 0.50, 0.20]

EMPLOYMENT_TYPES = ["正社員", "パート", "派遣"]
EMPLOYMENT_WEIGHTS = [0.60, 0.30, 0.10]

FACILITIES = ["第一病院", "第二クリニック", "介護老人保健施設"]
STAFF_PER_FACILITY = 10   # 各施設10名 → 合計30名

# ── 2024-01 の日付リスト ───────────────────────────────────────────────
JAN_DATES = [date(2024, 1, d) for d in range(1, 32)]   # 31日


def _make_staff_master(facility_id: int, n: int) -> list[dict]:
    """スタッフマスタを生成（施設ごと）"""
    staff = []
    for i in range(1, n + 1):
        sid = f"S{facility_id:02d}{i:03d}"
        role = random.choices(ROLES, ROLE_WEIGHTS)[0]
        skill = random.choices(SKILL_LEVELS, SKILL_WEIGHTS)[0]
        emp = random.choices(EMPLOYMENT_TYPES, EMPLOYMENT_WEIGHTS)[0]
        # 夜勤可否の個人バイアス（上級・正社員は夜勤しやすい）
        night_bias = 1.5 if (skill == "上級" and emp == "正社員") else 1.0
        staff.append(
            {
                "staff_id": sid,
                "name": f"スタッフ{sid}",
                "role": role,
                "skill_level": skill,
                "employment_type": emp,
                "night_bias": night_bias,
            }
        )
    return staff


def _make_shifts_for_staff(staff_master: list[dict]) -> list[dict]:
    """スタッフごとに31日分のシフト希望を生成"""
    records = []
    for s in staff_master:
        # 個人ごとに夜勤重みを調整
        w = list(SHIFT_WEIGHTS)
        night_idx = SHIFTS.index("夜勤")
        w[night_idx] = w[night_idx] * s["night_bias"]
        total = sum(w)
        w = [x / total for x in w]

        for dt in JAN_DATES:
            shift = random.choices(SHIFTS, w)[0]
            records.append(
                {
                    "staff_id": s["staff_id"],
                    "name": s["name"],
                    "role": s["role"],
                    "date": dt.strftime("%Y-%m-%d"),
                    "preferred_shift": shift,
                    "skill_level": s["skill_level"],
                    "employment_type": s["employment_type"],
                }
            )
    return records


def _save_style_a(records: list[dict], path: str) -> None:
    """スタイルA: 標準日本語列名"""
    col_map = {
        "staff_id": "スタッフID",
        "name": "氏名",
        "role": "役職",
        "date": "日付",
        "preferred_shift": "希望シフト",
        "skill_level": "スキルレベル",
        "employment_type": "雇用形態",
    }
    df = pd.DataFrame(records).rename(columns=col_map)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[生成] {os.path.basename(path)}  ({len(df)}行)")


def _save_style_b(records: list[dict], path: str) -> None:
    """スタイルB: 英語列名（そのまま）"""
    df = pd.DataFrame(records)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[生成] {os.path.basename(path)}  ({len(df)}行)")


def _save_style_c(records: list[dict], path: str) -> None:
    """スタイルC: 別表記日本語列名"""
    col_map = {
        "staff_id": "社員番号",
        "name": "スタッフ名",
        "role": "職種",
        "date": "勤務日",
        "preferred_shift": "シフト希望",
        "skill_level": "技能区分",
        "employment_type": "雇用区分",
    }
    df = pd.DataFrame(records).rename(columns=col_map)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[生成] {os.path.basename(path)}  ({len(df)}行)")


def main():
    all_records_info = []
    for fac_id, (fac_name, style_func) in enumerate(
        zip(
            FACILITIES,
            [_save_style_a, _save_style_b, _save_style_c],
        ),
        start=1,
    ):
        staff = _make_staff_master(fac_id, STAFF_PER_FACILITY)
        records = _make_shifts_for_staff(staff)
        filename = f"0{fac_id}_{fac_name}_shift_202401.csv"
        path = os.path.join(DATA_DIR, filename)
        style_func(records, path)
        all_records_info.append(len(records))

    total = sum(all_records_info)
    print(f"\n合計 {total} 行のデータを data/ に生成しました。")
    assert total >= 500, f"生成行数が500未満です: {total}"


if __name__ == "__main__":
    main()
