# -*- coding: utf-8 -*-
import random
import numpy as np
import pandas as pd
import os

random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DEPTS = ["naika", "geka", "seikei", "shonika", "hifuka"]
DEPT_JP = {
    "naika": "naika",
    "geka": "geka",
    "seikei": "seikei",
    "shonika": "shonika",
    "hifuka": "hifuka",
}

DEPTS_JP = ["naika", "geka", "seikei", "shonika", "hifuka"]
DEPTS_FULL = ["内科", "外科", "整形外科", "小児科", "皮膚科"]
INS_JP = ["社保", "国保", "後期高齢"]

PAYMENT_WEIGHTS = [0.75, 0.20, 0.05]
PAYMENT_STATUS_JP = ["支払済み", "審査中", "返戈"]


def gen_records(n, start_id):
    records = []
    dates = pd.date_range("2024-01-01", "2024-01-20", freq="D")
    for i in range(n):
        cid = start_id + i
        claim_date = random.choice(dates)
        dept_idx = random.randint(0, 4)
        ins_idx = random.randint(0, 2)
        patient_count = random.randint(10, 50)
        total_points = random.randint(500, 5000)
        claim_amount = total_points * 10
        max_reduction = int(claim_amount * 0.10)
        reduction_amount = random.randint(0, max_reduction)
        payment_status = random.choices(PAYMENT_STATUS_JP, weights=PAYMENT_WEIGHTS)[0]
        records.append({
            "dept_idx": dept_idx,
            "ins_idx": ins_idx,
            "claim_date": claim_date,
            "cid": cid,
            "patient_count": patient_count,
            "total_points": total_points,
            "claim_amount": claim_amount,
            "reduction_amount": reduction_amount,
            "payment_status": payment_status,
        })
    return records


all_records = gen_records(480, 1)
rA = all_records[0:160]
rB = all_records[160:320]
rC = all_records[320:480]

# --- Style A ---
rows_a = []
for r in rA:
    d = r["claim_date"].strftime("%Y/%m/%d")
    cid_str = "CLM-{:04d}".format(r["cid"])
    rows_a.append({
        "請求日": d,
        "請求ID": cid_str,
        "診療科": DEPTS_FULL[r["dept_idx"]],
        "保険区分": INS_JP[r["ins_idx"]],
        "患者数": r["patient_count"],
        "診療報酷点数": r["total_points"],
        "請求金額": r["claim_amount"],
        "査定減額": r["reduction_amount"],
        "支払状況": r["payment_status"],
    })
df_a = pd.DataFrame(rows_a)
df_a.to_csv(os.path.join(DATA_DIR, "claims_styleA_202401.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleA: {} rows".format(len(df_a)))

# --- Style B ---
PAYMENT_EN = {
    "支払済み": "Paid",
    "審査中": "UnderReview",
    "返戈": "Returned",
}
rows_b = []
for r in rB:
    d = r["claim_date"].strftime("%Y-%m-%d")
    cid_str = "CLM-{:04d}".format(r["cid"])
    rows_b.append({
        "ClaimDate": d,
        "ClaimID": cid_str,
        "Department": DEPTS_FULL[r["dept_idx"]],
        "InsuranceType": INS_JP[r["ins_idx"]],
        "PatientCount": r["patient_count"],
        "TotalPoints": r["total_points"],
        "ClaimAmount": r["claim_amount"],
        "ReductionAmount": r["reduction_amount"],
        "PaymentStatus": PAYMENT_EN[r["payment_status"]],
    })
df_b = pd.DataFrame(rows_b)
df_b.to_csv(os.path.join(DATA_DIR, "claims_styleB_202401.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleB: {} rows".format(len(df_b)))

# --- Style C ---
DEPT_C = {
    "内科": "内科",
    "外科": "外科",
    "整形外科": "整形外科",
    "小児科": "小児科",
    "皮膚科": "皮膚科",
}
STATUS_C = {
    "支払済み": "支払済み",
    "審査中": "審査中",
    "返戈": "返戈",
}
rows_c = []
for r in rC:
    d = r["claim_date"].strftime("%Y/%m/%d")
    cid_str = "CLM-{:04d}".format(r["cid"])
    rows_c.append({
        "算定日": d,
        "明細番号": cid_str,
        "科名": DEPTS_FULL[r["dept_idx"]],
        "保険種別": INS_JP[r["ins_idx"]],
        "受診者数": r["patient_count"],
        "点数合計": r["total_points"],
        "請求額": r["claim_amount"],
        "減額査定": r["reduction_amount"],
        "決済状況": r["payment_status"],
    })
df_c = pd.DataFrame(rows_c)
df_c.to_csv(os.path.join(DATA_DIR, "claims_styleC_202401.csv"), index=False, encoding="utf-8-sig")
print("[OK] StyleC: {} rows".format(len(df_c)))
print("[OK] Total: {} rows across 3 files".format(len(df_a) + len(df_b) + len(df_c)))
