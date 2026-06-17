"""
C-41: 人事・採用 -- 採用チャネル別コスト・採用レポートパイプライン
サンプルデータ生成スクリプト

3スタイルのCSVを data/ フォルダに生成（各スタイル140行、合計420行）
スタイルA: 標準日本語列名 (YYYY/MM/DD)
スタイルB: 英語列名 (YYYY-MM-DD)
スタイルC: バリアント日本語列名 (YYYY/MM/DD)
"""

import random
from pathlib import Path

import pandas as pd

random.seed(42)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CHANNELS = ["求人サイト", "SNS採用", "リファラル", "エージェント", "合同説明会"]
JOB_TYPES = ["エンジニア", "営業", "事務", "マーケ", "デザイン"]
PHASES = ["書類選考", "一次面接", "二次面接", "最終面接", "内定"]

# チャネル別採用コスト範囲
COST_RANGES = {
    "エージェント":   (300000, 500000),
    "求人サイト":     (100000, 200000),
    "SNS採用":       (30000,  80000),
    "リファラル":     (10000,  50000),
    "合同説明会":     (50000,  150000),
}


def generate_records(n: int, start_no: int = 1) -> list[dict]:
    """n件の応募レコードを生成"""
    rows = []
    for i in range(n):
        apply_no = start_no + i
        month = random.randint(1, 3)
        day = random.randint(1, 28)
        apply_date = f"2024/{month:02d}/{day:02d}"

        channel = random.choice(CHANNELS)
        job_type = random.choice(JOB_TYPES)

        cost_low, cost_high = COST_RANGES[channel]
        cost = random.randint(cost_low, cost_high)

        # 最終面接まで進んだ人の20%が採用
        phase_idx = random.randint(0, len(PHASES) - 1)
        phase = PHASES[phase_idx]

        if phase == "最終面接":
            is_hired = 1 if random.random() < 0.20 else 0
        elif phase == "内定":
            is_hired = 1
        else:
            is_hired = 0

        # 内定承諾: 採用可否=1の場合のみ設定
        if is_hired == 1:
            is_accepted = 1 if random.random() < 0.80 else 0
        else:
            is_accepted = None

        rows.append({
            "apply_date":  apply_date,
            "apply_no":    apply_no,
            "channel":     channel,
            "job_type":    job_type,
            "cost":        cost,
            "phase":       phase,
            "is_hired":    is_hired,
            "is_accepted": is_accepted,
        })
    return rows


def to_style_a(rec: dict) -> dict:
    """スタイルA: 標準日本語列名、YYYY/MM/DD形式"""
    return {
        "応募日":   rec["apply_date"],
        "応募番号": rec["apply_no"],
        "採用チャネル": rec["channel"],
        "職種":     rec["job_type"],
        "採用コスト": rec["cost"],
        "選考フェーズ": rec["phase"],
        "採用可否": rec["is_hired"],
        "内定承諾": rec["is_accepted"],
    }


def to_style_b(rec: dict) -> dict:
    """スタイルB: 英語列名、YYYY-MM-DD形式"""
    date_str = rec["apply_date"].replace("/", "-")
    return {
        "ApplyDate":   date_str,
        "ApplyNo":     rec["apply_no"],
        "Channel":     rec["channel"],
        "JobType":     rec["job_type"],
        "Cost":        rec["cost"],
        "Phase":       rec["phase"],
        "IsHired":     rec["is_hired"],
        "IsAccepted":  rec["is_accepted"],
    }


def to_style_c(rec: dict) -> dict:
    """スタイルC: バリアント日本語列名、YYYY/MM/DD形式"""
    return {
        "日付":     rec["apply_date"],
        "管理番号": rec["apply_no"],
        "チャネル": rec["channel"],
        "職種区分": rec["job_type"],
        "コスト":   rec["cost"],
        "フェーズ": rec["phase"],
        "採否":     rec["is_hired"],
        "承諾":     rec["is_accepted"],
    }


def main():
    # スタイルA: 140件 (No: 1-140)
    records_a = generate_records(140, start_no=1)
    # スタイルB: 140件 (No: 141-280)
    records_b = generate_records(140, start_no=141)
    # スタイルC: 140件 (No: 281-420)
    records_c = generate_records(140, start_no=281)

    configs = [
        (records_a, to_style_a, "recruitment_cost_styleA_202401.csv"),
        (records_b, to_style_b, "recruitment_cost_styleB_202401.csv"),
        (records_c, to_style_c, "recruitment_cost_styleC_202401.csv"),
    ]

    for records, converter, filename in configs:
        styled = [converter(r) for r in records]
        df = pd.DataFrame(styled)
        out_path = DATA_DIR / filename
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"Created {filename}: {len(df)} rows")

    total = sum(
        len(pd.read_csv(DATA_DIR / cfg[2], encoding="utf-8-sig"))
        for cfg in configs
    )
    print(f"\n合計: {total} 行 (3スタイル x 140件)")


if __name__ == "__main__":
    main()
