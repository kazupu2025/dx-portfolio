"""
B-11: 与信スコアリング サンプルデータ生成スクリプト
500申込者を3スタイル（Standard/English/Variant）の3CSVに分割して生成する。
完全な架空データ。実在人物を連想させる情報は含まない。
"""
import pandas as pd
import numpy as np
import random
from pathlib import Path

rng = np.random.default_rng(42)
random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/04_finance/02_credit_scoring")

occupations_std  = ["会社員", "公務員", "自営業", "パート・アルバイト", "無職"]
occupations_eng  = ["Employee", "Government", "SelfEmployed", "PartTime", "Unemployed"]
occupations_var  = ["正社員", "官公庁", "個人事業", "非正規", "無職"]
purposes = ["住宅購入", "カーローン", "教育資金", "生活費", "医療費", "事業資金", "その他"]

# 職業別のプロファイル（年収下限, 年収上限, 負債比率上限, 延滞確率）
occ_profile = {
    0: (350, 800, 0.3, 0.05),   # 会社員: 年収350-800万, 負債率低め, 延滞確率低
    1: (400, 700, 0.2, 0.02),   # 公務員: 安定収入, 最低延滞リスク
    2: (200, 1200, 0.5, 0.12),  # 自営業: 収入幅広い, 延滞リスク中
    3: (100, 300, 0.6, 0.18),   # パート・アルバイト: 低収入, 高負債比率
    4: (0, 100, 0.9, 0.35),     # 無職: 最高リスク
}


def gen_row(app_id: str, style: str) -> dict:
    occ_idx = int(rng.integers(0, 5))
    income_lo, income_hi, debt_ratio_hi, delay_prob = occ_profile[occ_idx]
    age = int(rng.integers(22, 70))
    income = int(rng.integers(max(50, income_lo), max(income_lo + 100, income_hi)))
    years_emp = int(rng.integers(0, min(age - 20, 40)))
    if occ_idx == 4:  # 無職
        income = int(rng.integers(0, 100))
        years_emp = 0
    debt_ratio = rng.uniform(0, debt_ratio_hi)
    total_debt = int(income * debt_ratio)
    past_delays = int(rng.poisson(delay_prob * 3))
    loan_amount = int(rng.integers(50, max(51, income * 5)))
    purpose = random.choice(purposes)

    if style == "standard":
        return {
            "申込ID": app_id,
            "年齢": age,
            "職業": occupations_std[occ_idx],
            "年収(万円)": income,
            "勤続年数(年)": years_emp,
            "負債総額(万円)": total_debt,
            "過去延滞回数": past_delays,
            "申込金額(万円)": loan_amount,
            "申込用途": purpose,
        }
    elif style == "english":
        return {
            "ApplicationID": app_id,
            "Age": age,
            "Occupation": occupations_eng[occ_idx],
            "AnnualIncome": income,
            "YearsEmployed": years_emp,
            "TotalDebt": total_debt,
            "PastDelays": past_delays,
            "LoanAmount": loan_amount,
            "LoanPurpose": purpose,
        }
    else:  # variant
        return {
            "申込番号": app_id,
            "年齢": age,
            "職種": occupations_var[occ_idx],
            "収入": income,
            "勤務年数": years_emp,
            "負債額": total_debt,
            "延滞数": past_delays,
            "借入希望額": loan_amount,
            "用途": purpose,
        }


batches = [
    (range(1, 201),   "standard", "01_申込データ_A_202401.csv"),
    (range(201, 351), "english",  "02_application_data_B_202401.csv"),
    (range(351, 501), "variant",  "03_申込データ_C_202401.csv"),
]

for id_range, style, filename in batches:
    rows = [gen_row(f"APP-{i:05d}", style) for i in id_range]
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("サンプルデータ生成完了（500申込者）")
