# -*- coding: utf-8 -*-
import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

# ---- settings ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

PLANS = ["スタータープラン", "スタンダードプラン", "エンタープライズプラン"]
PLAN_FEES = {
    "スタータープラン": 3000,
    "スタンダードプラン": 8000,
    "エンタープライズプラン": 30000,
}
INDUSTRIES = ["小売", "製造", "医療", "IT", "サービス"]
CHURN_REASONS = [
    "価格が高い",
    "機能不足",
    "競合他社に移行",
    "業務終了",
    "使いにくい",
]

NUM_RECORDS = 480
CHURN_RATE = 0.25

# contract_date range: 2023-01-01 to 2023-12-31
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2023, 12, 31)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days


def random_date():
    delta = random.randint(0, DATE_RANGE_DAYS)
    return START_DATE + timedelta(days=delta)


def generate_records():
    records = []
    for i in range(1, NUM_RECORDS + 1):
        plan = random.choice(PLANS)
        monthly_fee = PLAN_FEES[plan]
        industry = random.choice(INDUSTRIES)
        usage_months = random.randint(1, 24)
        login_count = random.randint(1, 60)
        support_count = random.randint(0, 10)
        is_churn = random.random() < CHURN_RATE
        status = "解約" if is_churn else "継続"
        churn_reason = random.choice(CHURN_REASONS) if is_churn else ""
        contract_date = random_date()
        records.append({
            "contract_date": contract_date,
            "contract_id": f"CON-{i:04d}",
            "plan": plan,
            "industry": industry,
            "monthly_fee": monthly_fee,
            "usage_months": usage_months,
            "login_count": login_count,
            "support_count": support_count,
            "status": status,
            "churn_reason": churn_reason,
        })
    return records


def write_style_a(records):
    """StyleA: 標準日本語、日付YYYY/MM/DD"""
    path = os.path.join(DATA_DIR, "contracts_styleA.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "契約開始日", "契約ID", "プラン", "業種",
            "月額料金", "利用月数", "月間ログイン数",
            "サポート問い合わせ数", "ステータス", "解約理由"
        ])
        for r in records:
            writer.writerow([
                r["contract_date"].strftime("%Y/%m/%d"),
                r["contract_id"],
                r["plan"],
                r["industry"],
                r["monthly_fee"],
                r["usage_months"],
                r["login_count"],
                r["support_count"],
                r["status"],
                r["churn_reason"],
            ])
    print(f"[OK] StyleA written: {path}")


def write_style_b(records):
    """StyleB: English、日付YYYY-MM-DD"""
    plan_map = {
        "スタータープラン": "Starter",
        "スタンダードプラン": "Standard",
        "エンタープライズプラン": "Enterprise",
    }
    industry_map = {
        "小売": "Retail",
        "製造": "Manufacturing",
        "医療": "Healthcare",
        "IT": "IT",
        "サービス": "Service",
    }
    status_map = {"継続": "Active", "解約": "Churned"}
    reason_map = {
        "価格が高い": "Too expensive",
        "機能不足": "Lack of features",
        "競合他社に移行": "Switched to competitor",
        "業務終了": "Business closed",
        "使いにくい": "Hard to use",
        "": "",
    }
    path = os.path.join(DATA_DIR, "contracts_styleB.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ContractDate", "ContractID", "Plan", "Industry",
            "MonthlyFee", "UsageMonths", "LoginCount",
            "SupportCount", "Status", "ChurnReason"
        ])
        for r in records:
            writer.writerow([
                r["contract_date"].strftime("%Y-%m-%d"),
                r["contract_id"],
                plan_map[r["plan"]],
                industry_map[r["industry"]],
                r["monthly_fee"],
                r["usage_months"],
                r["login_count"],
                r["support_count"],
                status_map[r["status"]],
                reason_map[r["churn_reason"]],
            ])
    print(f"[OK] StyleB written: {path}")


def write_style_c(records):
    """StyleC: バリアント日本語、日付YYYY/MM/DD"""
    path = os.path.join(DATA_DIR, "contracts_styleC.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "開始日", "顧客ID", "料金プラン", "業界",
            "月額", "契約月数", "ログイン回数",
            "問い合わせ回数", "契約状態", "退会理由"
        ])
        for r in records:
            writer.writerow([
                r["contract_date"].strftime("%Y/%m/%d"),
                r["contract_id"],
                r["plan"],
                r["industry"],
                r["monthly_fee"],
                r["usage_months"],
                r["login_count"],
                r["support_count"],
                r["status"],
                r["churn_reason"],
            ])
    print(f"[OK] StyleC written: {path}")


if __name__ == "__main__":
    records = generate_records()
    write_style_a(records)
    write_style_b(records)
    write_style_c(records)
    print(f"[OK] Total records generated: {len(records)}")
