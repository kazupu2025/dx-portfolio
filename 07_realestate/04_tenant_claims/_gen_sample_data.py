"""
C-39: 入居者対応履歴・クレーム集計パイプライン
サンプルデータ生成スクリプト
3スタイルのCSVを data/ フォルダに生成（合計420行以上）
"""

import random
import csv
import os
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PROPERTIES = ["サンシャインA棟", "グリーンB棟", "ブルーC棟", "ホワイトD棟", "シルバーE棟"]
CLAIM_TYPES = ["設備故障", "騒音", "水漏れ", "害虫", "駐車", "その他"]
STATUSES = ["解決済", "対応中", "未対応"]
STATUS_WEIGHTS = [0.65, 0.25, 0.10]

N_PER_STYLE = 140


def gen_date_slash(year=2024, month=1):
    """YYYY/MM/DD形式の日付を生成"""
    import datetime
    day = random.randint(1, 28)
    return f"{year}/{month:02d}/{day:02d}"


def gen_date_dash(year=2024, month=1):
    """YYYY-MM-DD形式の日付を生成"""
    import datetime
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def pick_status():
    return random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]


def gen_response_days(status):
    if status == "解決済":
        return random.randint(1, 30)
    elif status == "対応中":
        return random.randint(5, 90)
    else:  # 未対応
        return random.randint(10, 120)


def gen_work_hours():
    choices = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    return random.choice(choices)


def gen_room_no():
    floor = random.randint(1, 10)
    unit = random.randint(1, 8)
    return f"{floor:02d}{unit:02d}"


# --- スタイルA: 標準日本語列名、日付 YYYY/MM/DD ---
def gen_style_a():
    rows = []
    for i in range(N_PER_STYLE):
        case_no = f"A-{2024010001 + i}"
        month = random.randint(1, 3)
        status = pick_status()
        rows.append({
            "受付日": gen_date_slash(2024, month),
            "案件番号": case_no,
            "物件名": random.choice(PROPERTIES),
            "部屋番号": gen_room_no(),
            "クレーム区分": random.choice(CLAIM_TYPES),
            "対応状況": status,
            "対応日数": gen_response_days(status),
            "対応工数（時間）": gen_work_hours(),
        })
    return rows


# --- スタイルB: 英語列名、日付 YYYY-MM-DD ---
def gen_style_b():
    rows = []
    for i in range(N_PER_STYLE):
        case_no = f"B-{2024010001 + i}"
        month = random.randint(1, 3)
        status = pick_status()
        rows.append({
            "ReceiptDate": gen_date_dash(2024, month),
            "CaseNo": case_no,
            "PropertyName": random.choice(PROPERTIES),
            "RoomNo": gen_room_no(),
            "ClaimType": random.choice(CLAIM_TYPES),
            "Status": status,
            "ResponseDays": gen_response_days(status),
            "WorkHours": gen_work_hours(),
        })
    return rows


# --- スタイルC: バリアント日本語列名、日付 YYYY/MM/DD ---
def gen_style_c():
    rows = []
    for i in range(N_PER_STYLE):
        case_no = f"C-{2024010001 + i}"
        month = random.randint(1, 3)
        status = pick_status()
        rows.append({
            "日付": gen_date_slash(2024, month),
            "管理番号": case_no,
            "建物名": random.choice(PROPERTIES),
            "号室": gen_room_no(),
            "種別": random.choice(CLAIM_TYPES),
            "状況": status,
            "処理日数": gen_response_days(status),
            "工数": gen_work_hours(),
        })
    return rows


def write_csv(filepath, rows, fieldnames):
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] {filepath} ({len(rows)} rows)")


if __name__ == "__main__":
    style_a = gen_style_a()
    write_csv(
        DATA_DIR / "claims_styleA_202401.csv",
        style_a,
        ["受付日", "案件番号", "物件名", "部屋番号", "クレーム区分", "対応状況", "対応日数", "対応工数（時間）"],
    )

    style_b = gen_style_b()
    write_csv(
        DATA_DIR / "claims_styleB_202401.csv",
        style_b,
        ["ReceiptDate", "CaseNo", "PropertyName", "RoomNo", "ClaimType", "Status", "ResponseDays", "WorkHours"],
    )

    style_c = gen_style_c()
    write_csv(
        DATA_DIR / "claims_styleC_202401.csv",
        style_c,
        ["日付", "管理番号", "建物名", "号室", "種別", "状況", "処理日数", "工数"],
    )

    total = len(style_a) + len(style_b) + len(style_c)
    print(f"\n[DONE] Total rows generated: {total}")
