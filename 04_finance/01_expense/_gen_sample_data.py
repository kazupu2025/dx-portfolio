import pandas as pd
import random
from pathlib import Path

random.seed(42)
out = Path("C:/Users/realp/Desktop/claude_code_TRY/dx-portfolio/04_finance/01_expense")

departments = ["営業部", "経理部", "人事部", "開発部", "総務部"]
expense_types = ["交通費", "宿泊費", "接待費", "消耗品費", "通信費", "研修費"]

# 部門別予算（月次）
dept_budget = {
    "営業部": 500000, "経理部": 200000, "人事部": 250000,
    "開発部": 350000, "総務部": 180000,
}

# 費目別の典型金額レンジ
expense_range = {
    "交通費":   (500, 15000),
    "宿泊費":   (8000, 30000),
    "接待費":   (5000, 50000),
    "消耗品費": (300, 8000),
    "通信費":   (500, 5000),
    "研修費":   (10000, 80000),
}


def gen_rows(dept: str, n: int, col_style: str) -> list:
    rows = []
    for i in range(n):
        day = random.randint(1, 28)
        date_str = f"2024/01/{day:02d}"
        emp_id = f"EMP-{random.randint(100, 999)}"
        emp_name = f"社員{random.randint(1, 50):03d}"
        exp_type = random.choice(expense_types)
        lo, hi = expense_range[exp_type]
        amount = random.randint(lo, hi)
        # 10%の確率で予算超過気味の高額経費
        if random.random() < 0.10:
            amount = int(amount * random.uniform(2.0, 4.0))
        receipt_no = f"RCP-{2024010000 + i:08d}"
        budget = dept_budget[dept] // n  # 1件あたり仮予算

        if col_style == "standard":
            rows.append({
                "日付": date_str, "社員ID": emp_id, "氏名": emp_name,
                "部門": dept, "費目": exp_type, "金額": amount,
                "予算": budget, "領収書番号": receipt_no,
            })
        elif col_style == "english":
            rows.append({
                "Date": date_str, "EmployeeID": emp_id, "Name": emp_name,
                "Department": dept, "ExpenseType": exp_type, "Amount": amount,
                "Budget": budget, "ReceiptNo": receipt_no,
            })
        elif col_style == "variant":
            rows.append({
                "申請日": date_str, "社員番号": emp_id, "申請者": emp_name,
                "所属部門": dept, "経費区分": exp_type, "申請金額": amount,
                "予算額": budget, "領収No": receipt_no,
            })
    return rows


files = [
    ("営業部",   "standard", "01_営業部_経費_202401.csv",   90),
    ("経理部",   "english",  "02_経理部_expense_202401.csv", 60),
    ("人事部",   "variant",  "03_人事部_経費_202401.csv",   70),
    ("開発部",   "standard", "04_開発部_経費_202401.csv",   80),
    ("総務部",   "standard", "05_総務部_経費_202401.csv",   55),
]

for dept, style, filename, n in files:
    n_actual = random.randint(int(n * 0.85), int(n * 1.15))
    rows = gen_rows(dept, n_actual, style)
    df = pd.DataFrame(rows)
    df.to_csv(out / filename, index=False, encoding="utf-8-sig")
    print(f"Created {filename}: {len(df)} rows, style={style}")

print("\nサンプルデータ生成完了（5部門）")
