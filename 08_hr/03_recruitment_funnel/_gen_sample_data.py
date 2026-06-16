"""
C-33: 人事・採用 -- 採用歩留まり率分析パイプライン
サンプルデータ生成スクリプト

3スタイルのCSVを data/ フォルダに生成（合計400行以上）
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

JOB_TYPES = ["エンジニア", "営業", "事務", "マーケティング", "製造"]
CHANNELS = ["転職サイト", "エージェント", "リファラル", "自社HP"]
PHASES = ["書類選考", "一次面接", "二次面接", "最終面接", "内定"]

PHASE_ORDER = {
    "書類選考": 1,
    "一次面接": 2,
    "二次面接": 3,
    "最終面接": 4,
    "内定": 5,
}

# 各フェーズの通過率
PASS_RATES = {
    "書類選考": 0.60,
    "一次面接": 0.50,
    "二次面接": 0.60,
    "最終面接": 0.70,
    "内定": 0.80,
}


def simulate_applicant(applicant_id: int, apply_date_str: str, job_type: str, channel: str) -> dict:
    """1応募者の選考フローをシミュレートして最終到達フェーズと採用結果を返す"""
    reached_phase = "書類選考"
    for phase in PHASES:
        pass_rate = PASS_RATES[phase]
        if random.random() < pass_rate:
            reached_phase = phase
        else:
            break

    # 採用結果: 内定まで到達した場合のみ「採用」
    hire_result = "採用" if reached_phase == "内定" else "不採用"

    # 選考日数: フェーズ順序に応じて長くなる
    phase_num = PHASE_ORDER[reached_phase]
    base_days = phase_num * 7
    screening_days = max(1, base_days + random.randint(-3, 7))

    return {
        "apply_date": apply_date_str,
        "applicant_id": applicant_id,
        "job_type": job_type,
        "channel": channel,
        "reached_phase": reached_phase,
        "hire_result": hire_result,
        "screening_days": screening_days,
    }


def generate_records(n: int, start_id: int = 1) -> list[dict]:
    """n件の応募者レコードを生成"""
    rows = []
    for i in range(n):
        applicant_id = start_id + i
        # 応募日: 2024年1月〜3月のランダム日
        month = random.randint(1, 3)
        day = random.randint(1, 28)
        apply_date = f"2024/{month:02d}/{day:02d}"

        job_type = random.choice(JOB_TYPES)
        channel = random.choice(CHANNELS)

        rec = simulate_applicant(applicant_id, apply_date, job_type, channel)
        rows.append(rec)
    return rows


def to_style_a(rec: dict) -> dict:
    """スタイルA: 標準日本語列名、YYYY/MM/DD形式"""
    return {
        "応募日":       rec["apply_date"],
        "応募者ID":     rec["applicant_id"],
        "職種":         rec["job_type"],
        "採用チャネル": rec["channel"],
        "到達フェーズ": rec["reached_phase"],
        "採用結果":     rec["hire_result"],
        "選考日数":     rec["screening_days"],
    }


def to_style_b(rec: dict) -> dict:
    """スタイルB: 英語列名、YYYY-MM-DD形式"""
    # 日付を YYYY-MM-DD 形式に変換
    date_parts = rec["apply_date"].replace("/", "-")
    return {
        "ApplyDate":      date_parts,
        "ApplicantID":    rec["applicant_id"],
        "JobType":        rec["job_type"],
        "Channel":        rec["channel"],
        "ReachedPhase":   rec["reached_phase"],
        "HireResult":     rec["hire_result"],
        "ScreeningDays":  rec["screening_days"],
    }


def to_style_c(rec: dict) -> dict:
    """スタイルC: バリアント日本語列名、YYYY/MM/DD形式"""
    return {
        "受付日":         rec["apply_date"],
        "候補者番号":     rec["applicant_id"],
        "募集職種":       rec["job_type"],
        "応募経路":       rec["channel"],
        "最終選考段階":   rec["reached_phase"],
        "採否":           rec["hire_result"],
        "選考所要日数":   rec["screening_days"],
    }


def main():
    # スタイルA: 140件 (ID: 1-140)
    records_a = generate_records(140, start_id=1)
    # スタイルB: 140件 (ID: 141-280)
    records_b = generate_records(140, start_id=141)
    # スタイルC: 140件 (ID: 281-420)
    records_c = generate_records(140, start_id=281)

    configs = [
        (records_a, to_style_a, "recruitment_styleA_202401.csv"),
        (records_b, to_style_b, "recruitment_styleB_202401.csv"),
        (records_c, to_style_c, "recruitment_styleC_202401.csv"),
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
